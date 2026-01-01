"""
Faculty routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Quiz, Question, QuizQuestion, QuizAttempt, User, CodeSubmission, Notification, db
from utils.auth import role_required
from datetime import datetime
import json

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required(['faculty', 'admin'])
def dashboard():
    """Get faculty dashboard data with batch analytics"""
    try:
        user_id = get_jwt_identity()
        
        # Get quizzes created by faculty
        quizzes = Quiz.query.filter_by(created_by=user_id).all()
        
        # Get total students
        total_students = User.query.filter_by(role='student', is_active=True).count()
        
        # Get recent quiz attempts
        recent_attempts = QuizAttempt.query.join(Quiz)\
            .filter(Quiz.created_by == user_id)\
            .order_by(QuizAttempt.submitted_at.desc()).limit(10).all()
        
        # Batch Analytics - Average scores across all students
        all_students = User.query.filter_by(role='student', is_active=True).all()
        
        # Calculate batch averages
        total_coding_submissions = 0
        total_accepted_submissions = 0
        total_quiz_attempts = 0
        total_quiz_score = 0
        
        for student in all_students:
            submissions = CodeSubmission.query.filter_by(user_id=student.id).all()
            quiz_attempts = QuizAttempt.query.filter_by(user_id=student.id).all()
            
            total_coding_submissions += len(submissions)
            total_accepted_submissions += len([s for s in submissions if s.status == 'accepted'])
            total_quiz_attempts += len(quiz_attempts)
            total_quiz_score += sum(q.score for q in quiz_attempts)
        
        batch_avg_accuracy = (total_accepted_submissions / total_coding_submissions * 100) if total_coding_submissions > 0 else 0
        batch_avg_quiz_score = (total_quiz_score / total_quiz_attempts) if total_quiz_attempts > 0 else 0
        
        return jsonify({
            'total_quizzes': len(quizzes),
            'total_students': total_students,
            'quizzes': [q.to_dict() for q in quizzes],
            'recent_attempts': [a.to_dict() for a in recent_attempts],
            'batch_analytics': {
                'total_students': total_students,
                'total_submissions': total_coding_submissions,
                'total_quiz_attempts': total_quiz_attempts,
                'batch_avg_accuracy': round(batch_avg_accuracy, 2),
                'batch_avg_quiz_score': round(batch_avg_quiz_score, 2)
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faculty_bp.route('/quizzes', methods=['POST'])
@jwt_required()
@role_required(['student', 'faculty', 'admin'])
def create_quiz():
    """Create a new quiz"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        if not data.get('question_ids') or len(data.get('question_ids', [])) == 0:
            return jsonify({'error': 'At least one question is required'}), 400
        
        quiz = Quiz(
            title=data.get('title'),
            description=data.get('description'),
            created_by=user_id,
            company_id=data.get('company_id'),
            duration_minutes=data.get('duration_minutes', 60),
            total_marks=data.get('total_marks', 100),
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        )
        
        db.session.add(quiz)
        db.session.flush()
        
        # Add questions to quiz
        question_ids = data.get('question_ids', [])
        question_marks_map = data.get('question_marks', {})  # Optional: {question_id: marks}
        
        for idx, q_id in enumerate(question_ids):
            # Verify question exists
            question = Question.query.get(q_id)
            if not question:
                db.session.rollback()
                return jsonify({'error': f'Question with ID {q_id} not found'}), 400
            
            # Get marks from map if provided (try both string and int keys)
            marks = None
            if question_marks_map:
                marks = question_marks_map.get(str(q_id)) or question_marks_map.get(int(q_id)) if isinstance(q_id, int) else question_marks_map.get(q_id)
            
            # If not in map, fetch from question itself
            if marks is None:
                marks = question.marks if question.marks else data.get('marks_per_question', 1)
            
            qq = QuizQuestion(
                quiz_id=quiz.id,
                question_id=q_id,
                marks=int(marks),
                order=idx
            )
            db.session.add(qq)
        
        db.session.commit()
        
        # Notify all students about the new quiz
        students = User.query.filter_by(role='student', is_active=True).all()
        for student in students:
            notification = Notification(
                user_id=student.id,
                title='New Quiz Available',
                message=f'A new quiz "{quiz.title}" has been added. Check it out!',
                type='quiz',
                link=f'/quiz/{quiz.id}'
            )
            db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Quiz created successfully',
            'quiz': quiz.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating quiz: {error_trace}")
        return jsonify({'error': str(e), 'trace': error_trace}), 500

@faculty_bp.route('/quizzes/<int:quiz_id>', methods=['DELETE'])
@jwt_required()
@role_required(['faculty', 'admin'])
def delete_quiz(quiz_id):
    """Delete a quiz"""
    try:
        user_id = get_jwt_identity()
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Check if user created the quiz or is admin
        if quiz.created_by != user_id:
            user = User.query.get(user_id)
            if not user or user.role != 'admin':
                return jsonify({'error': 'You do not have permission to delete this quiz'}), 403
        
        # Soft delete: set is_active to False
        quiz.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Quiz deleted successfully',
            'quiz_id': quiz_id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error deleting quiz: {error_trace}")
        return jsonify({'error': str(e)}), 500

@faculty_bp.route('/questions', methods=['GET'])
@jwt_required()
@role_required(['faculty', 'admin'])
def list_questions():
    """List all questions (for faculty/admin - includes inactive)"""
    try:
        question_type = request.args.get('type')  # coding, mcq, fill_blank
        difficulty = request.args.get('difficulty')
        company_id = request.args.get('company_id')
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        query = Question.query
        
        # Faculty can see inactive questions if requested
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        if question_type:
            query = query.filter_by(type=question_type)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        questions = query.order_by(Question.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'questions': [q.to_dict() for q in questions.items],
            'total': questions.total,
            'page': page,
            'per_page': per_page,
            'pages': questions.pages
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faculty_bp.route('/questions', methods=['POST'])
@jwt_required()
@role_required(['student', 'faculty', 'admin'])
def create_question():
    """Create a new question"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        if not data.get('description'):
            return jsonify({'error': 'Description is required'}), 400
        if not data.get('type'):
            return jsonify({'error': 'Type is required'}), 400
        
        # Validate type
        if data.get('type') not in ['coding', 'mcq', 'fill_blank']:
            return jsonify({'error': 'Invalid question type'}), 400
        
        # For coding questions, validate test cases
        if data.get('type') == 'coding':
            test_cases = data.get('test_cases', [])
            if not test_cases or len(test_cases) == 0:
                return jsonify({'error': 'At least one test case is required for coding questions'}), 400
            for i, tc in enumerate(test_cases):
                if not tc.get('input') or not tc.get('output'):
                    return jsonify({'error': f'Test case {i+1} must have both input and output'}), 400
        
        question = Question(
            title=data.get('title'),
            description=data.get('description'),
            type=data.get('type'),  # coding, mcq, fill_blank
            difficulty=data.get('difficulty', 'medium'),
            company_id=data.get('company_id'),
            tags=','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else (data.get('tags') or ''),
            created_by=user_id,
            is_active=True  # Explicitly set as active
        )
        
        if question.type == 'coding':
            question.test_cases = json.dumps(data.get('test_cases', []))
            question.starter_code = data.get('starter_code', '')
            question.solution = data.get('solution', '')
        elif question.type == 'mcq':
            question.options = json.dumps(data.get('options', []))
            question.correct_answer = data.get('correct_answer')
            question.marks = data.get('marks', 1)
        elif question.type == 'fill_blank':
            question.blanks = json.dumps(data.get('blanks', []))
        
        db.session.add(question)
        db.session.commit()
        
        # Determine question type label
        question_type_label = 'Coding Question' if question.type == 'coding' else 'Non-Technical Question'
        
        # Notify all students about the new question
        students = User.query.filter_by(role='student', is_active=True).all()
        for student in students:
            notification = Notification(
                user_id=student.id,
                title=f'New {question_type_label} Added',
                message=f'A new {question_type_label.lower()} "{question.title}" has been added. Start practicing!',
                type='question',
                link=f'/coding/questions/{question.id}' if question.type == 'coding' else f'/non-technical'
            )
            db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Question created successfully',
            'question': question.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating question: {error_trace}")
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc() if request.args.get('debug') == 'true' else None
        }), 500

@faculty_bp.route('/questions/<int:question_id>', methods=['PUT'])
@jwt_required()
@role_required(['faculty', 'admin'])
def update_question(question_id):
    """Update a question"""
    try:
        question = Question.query.get_or_404(question_id)
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            question.title = data['title']
        if 'description' in data:
            question.description = data['description']
        if 'difficulty' in data:
            question.difficulty = data['difficulty']
        if 'company_id' in data:
            question.company_id = data['company_id']
        if 'tags' in data:
            question.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']
        if 'is_active' in data:
            question.is_active = data['is_active']
        
        if question.type == 'coding':
            if 'test_cases' in data:
                question.test_cases = json.dumps(data['test_cases'])
            if 'starter_code' in data:
                question.starter_code = data['starter_code']
            if 'solution' in data:
                question.solution = data['solution']
        elif question.type == 'mcq':
            if 'options' in data:
                question.options = json.dumps(data['options'])
            if 'correct_answer' in data:
                question.correct_answer = data['correct_answer']
            if 'marks' in data:
                question.marks = data['marks']
        elif question.type == 'fill_blank':
            if 'blanks' in data:
                question.blanks = json.dumps(data['blanks'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Question updated successfully',
            'question': question.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@faculty_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
@role_required(['faculty', 'admin'])
def delete_question(question_id):
    """Delete (deactivate) a question"""
    try:
        question = Question.query.get_or_404(question_id)
        
        # Soft delete - set is_active to False
        question.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Question deactivated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@faculty_bp.route('/students/performance', methods=['GET'])
@jwt_required()
@role_required(['faculty', 'admin'])
def student_performance():
    """Get student performance analytics with detailed metrics"""
    try:
        student_id = request.args.get('student_id')
        
        if student_id:
            students = [User.query.get_or_404(student_id)]
        else:
            students = User.query.filter_by(role='student', is_active=True).all()
        
        performance_data = []
        for student in students:
            submissions = CodeSubmission.query.filter_by(user_id=student.id).all()
            quiz_attempts = QuizAttempt.query.filter_by(user_id=student.id).all()
            
            total_submissions = len(submissions)
            accepted = len([s for s in submissions if s.status == 'accepted'])
            accuracy = (accepted / total_submissions * 100) if total_submissions > 0 else 0
            avg_quiz_score = sum(q.score for q in quiz_attempts) / len(quiz_attempts) if quiz_attempts else 0
            
            # Language-wise performance
            language_stats = {}
            for submission in submissions:
                lang = submission.language
                if lang not in language_stats:
                    language_stats[lang] = {'total': 0, 'accepted': 0}
                language_stats[lang]['total'] += 1
                if submission.status == 'accepted':
                    language_stats[lang]['accepted'] += 1
            
            # Difficulty-wise performance
            difficulty_stats = {}
            for submission in submissions:
                if submission.question:
                    diff = submission.question.difficulty or 'unknown'
                    if diff not in difficulty_stats:
                        difficulty_stats[diff] = {'total': 0, 'accepted': 0}
                    difficulty_stats[diff]['total'] += 1
                    if submission.status == 'accepted':
                        difficulty_stats[diff]['accepted'] += 1
            
            performance_data.append({
                'student': student.to_dict(),
                'total_submissions': total_submissions,
                'accepted_submissions': accepted,
                'accuracy': round(accuracy, 2),
                'total_quizzes': len(quiz_attempts),
                'avg_quiz_score': round(avg_quiz_score, 2),
                'language_stats': language_stats,
                'difficulty_stats': difficulty_stats
            })
        
        return jsonify({
            'performance': performance_data
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faculty_bp.route('/batch/weak-areas', methods=['GET'])
@jwt_required()
@role_required(['faculty', 'admin'])
def batch_weak_areas():
    """Identify weak areas across the batch"""
    try:
        all_students = User.query.filter_by(role='student', is_active=True).all()
        
        # Collect statistics across all students
        difficulty_stats = {}
        language_stats = {}
        topic_stats = {}
        question_type_stats = {}
        
        for student in all_students:
            submissions = CodeSubmission.query.filter_by(user_id=student.id).all()
            
            for submission in submissions:
                if submission.question:
                    # Difficulty analysis
                    diff = submission.question.difficulty or 'unknown'
                    if diff not in difficulty_stats:
                        difficulty_stats[diff] = {'total': 0, 'accepted': 0}
                    difficulty_stats[diff]['total'] += 1
                    if submission.status == 'accepted':
                        difficulty_stats[diff]['accepted'] += 1
                    
                    # Language analysis
                    lang = submission.language
                    if lang not in language_stats:
                        language_stats[lang] = {'total': 0, 'accepted': 0}
                    language_stats[lang]['total'] += 1
                    if submission.status == 'accepted':
                        language_stats[lang]['accepted'] += 1
                    
                    # Question type analysis
                    q_type = submission.question.type or 'unknown'
                    if q_type not in question_type_stats:
                        question_type_stats[q_type] = {'total': 0, 'accepted': 0}
                    question_type_stats[q_type]['total'] += 1
                    if submission.status == 'accepted':
                        question_type_stats[q_type]['accepted'] += 1
                    
                    # Topic analysis (from tags)
                    if submission.question.tags:
                        tags = submission.question.tags.split(',')
                        for tag in tags:
                            tag = tag.strip()
                            if tag:
                                if tag not in topic_stats:
                                    topic_stats[tag] = {'total': 0, 'accepted': 0}
                                topic_stats[tag]['total'] += 1
                                if submission.status == 'accepted':
                                    topic_stats[tag]['accepted'] += 1
        
        # Calculate accuracy for each category
        def calculate_weak_areas(stats_dict):
            weak_areas = []
            for key, stats in stats_dict.items():
                if stats['total'] > 0:
                    accuracy = (stats['accepted'] / stats['total']) * 100
                    weak_areas.append({
                        'area': key,
                        'total_attempts': stats['total'],
                        'accepted': stats['accepted'],
                        'accuracy': round(accuracy, 2),
                        'needs_improvement': accuracy < 50  # Less than 50% accuracy
                    })
            # Sort by accuracy (lowest first - weakest areas)
            weak_areas.sort(key=lambda x: x['accuracy'])
            return weak_areas
        
        weak_difficulties = calculate_weak_areas(difficulty_stats)
        weak_languages = calculate_weak_areas(language_stats)
        weak_topics = calculate_weak_areas(topic_stats)
        weak_question_types = calculate_weak_areas(question_type_stats)
        
        # Get quiz weak areas
        quiz_weak_areas = []
        all_quiz_attempts = QuizAttempt.query.all()
        quiz_scores_by_quiz = {}
        
        for attempt in all_quiz_attempts:
            quiz_id = attempt.quiz_id
            if quiz_id not in quiz_scores_by_quiz:
                quiz_scores_by_quiz[quiz_id] = {'scores': [], 'quiz_title': attempt.quiz.title if attempt.quiz else 'Unknown'}
            quiz_scores_by_quiz[quiz_id]['scores'].append(attempt.score)
        
        for quiz_id, data in quiz_scores_by_quiz.items():
            if data['scores']:
                avg_score = sum(data['scores']) / len(data['scores'])
                quiz_weak_areas.append({
                    'quiz_id': quiz_id,
                    'quiz_title': data['quiz_title'],
                    'avg_score': round(avg_score, 2),
                    'total_attempts': len(data['scores']),
                    'needs_improvement': avg_score < 50
                })
        
        quiz_weak_areas.sort(key=lambda x: x['avg_score'])
        
        return jsonify({
            'weak_difficulties': weak_difficulties[:10],  # Top 10 weakest
            'weak_languages': weak_languages[:10],
            'weak_topics': weak_topics[:15],  # Top 15 weakest topics
            'weak_question_types': weak_question_types,
            'weak_quizzes': quiz_weak_areas[:10],
            'summary': {
                'total_students_analyzed': len(all_students),
                'total_weak_areas_identified': len([w for w in weak_difficulties + weak_languages + weak_topics if w['needs_improvement']])
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faculty_bp.route('/feedback', methods=['POST'])
@jwt_required()
@role_required(['faculty', 'admin'])
def provide_feedback():
    """Provide feedback to student"""
    try:
        from models import Notification
        
        data = request.get_json()
        student_id = data.get('student_id')
        title = data.get('title')
        message = data.get('message')
        link = data.get('link')
        
        notification = Notification(
            user_id=student_id,
            title=title,
            message=message,
            type='feedback',
            link=link
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Feedback sent successfully',
            'notification': notification.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

