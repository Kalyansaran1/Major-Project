"""
Student routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Question, CodeSubmission, Quiz, QuizQuestion, QuizAttempt, Resource, Notification, InterviewSession, db
from utils.auth import role_required, get_current_user
from utils.leaderboard import update_leaderboard

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required(['student'])
def dashboard():
    """Get student dashboard data"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Get recent submissions
        recent_submissions = CodeSubmission.query.filter_by(user_id=user_id)\
            .order_by(CodeSubmission.submitted_at.desc()).limit(5).all()
        
        # Get recent quiz attempts
        recent_quizzes = QuizAttempt.query.filter_by(user_id=user_id)\
            .order_by(QuizAttempt.submitted_at.desc()).limit(5).all()
        
        # Get unread notifications
        unread_notifications = Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        # Get available quizzes
        available_quizzes = Quiz.query.filter_by(is_active=True).limit(5).all()
        
        # Get coding questions
        coding_questions = Question.query.filter_by(
            type='coding', is_active=True
        ).limit(10).all()
        
        return jsonify({
            'user': user.to_dict(),
            'recent_submissions': [s.to_dict() for s in recent_submissions],
            'recent_quizzes': [q.to_dict() for q in recent_quizzes],
            'notifications': [n.to_dict() for n in unread_notifications],
            'available_quizzes': [q.to_dict() for q in available_quizzes],
            'coding_questions': [q.to_dict() for q in coding_questions]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/performance', methods=['GET'])
@jwt_required()
@role_required(['student'])
def performance():
    """Get student performance analytics"""
    try:
        user_id = get_jwt_identity()
        
        # Get all submissions
        submissions = CodeSubmission.query.filter_by(user_id=user_id).all()
        total_submissions = len(submissions)
        accepted_submissions = len([s for s in submissions if s.status == 'accepted'])
        accuracy = (accepted_submissions / total_submissions * 100) if total_submissions > 0 else 0
        
        # Get quiz attempts
        quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
        total_quizzes = len(quiz_attempts)
        avg_quiz_score = sum(q.score for q in quiz_attempts) / total_quizzes if total_quizzes > 0 else 0
        
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
            diff = submission.question.difficulty if submission.question else 'unknown'
            if diff not in difficulty_stats:
                difficulty_stats[diff] = {'total': 0, 'accepted': 0}
            difficulty_stats[diff]['total'] += 1
            if submission.status == 'accepted':
                difficulty_stats[diff]['accepted'] += 1
        
        return jsonify({
            'total_submissions': total_submissions,
            'accepted_submissions': accepted_submissions,
            'accuracy': round(accuracy, 2),
            'total_quizzes': total_quizzes,
            'avg_quiz_score': round(avg_quiz_score, 2),
            'language_stats': language_stats,
            'difficulty_stats': difficulty_stats
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/questions', methods=['GET'])
@jwt_required()
def get_questions():
    """Get questions with filters"""
    try:
        question_type = request.args.get('type')  # coding, mcq, fill_blank
        difficulty = request.args.get('difficulty')
        company_id = request.args.get('company_id')
        exclude_quiz_questions = request.args.get('exclude_quiz_questions', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = Question.query.filter_by(is_active=True)
        
        if question_type:
            query = query.filter_by(type=question_type)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        # Exclude questions that are part of any quiz (for non-technical page)
        if exclude_quiz_questions:
            # Get all question IDs that are used in quizzes
            quiz_question_ids = [q[0] for q in db.session.query(QuizQuestion.question_id).distinct().all()]
            if quiz_question_ids:
                query = query.filter(~Question.id.in_(quiz_question_ids))
        
        questions = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'questions': [q.to_dict() for q in questions.items],
            'total': questions.total,
            'page': page,
            'per_page': per_page,
            'pages': questions.pages
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/resources', methods=['GET'])
@jwt_required()
def get_resources():
    """Get learning resources - accessible to everyone"""
    try:
        resource_type = request.args.get('type')
        company_id = request.args.get('company_id')
        
        # Show all resources to everyone (no filtering by is_public or user_id)
        query = Resource.query
        
        if resource_type:
            query = query.filter_by(type=resource_type)
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        resources = query.order_by(Resource.created_at.desc()).all()
        
        return jsonify({
            'resources': [r.to_dict() for r in resources]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/placement-readiness', methods=['GET'])
@jwt_required()
@role_required(['student', 'faculty', 'admin'])
def placement_readiness():
    """Get Placement Readiness Score for a user"""
    try:
        # Allow faculty/admin to view any student's score, or students to view their own
        target_user_id = request.args.get('user_id')
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'Current user not found'}), 404
        
        # Determine which user's score to calculate
        if target_user_id and current_user.role in ['faculty', 'admin']:
            user_id = int(target_user_id)
        else:
            user_id = current_user_id
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 1. Calculate Code Practice Score (from code submissions)
        # This is the main coding performance metric based on test cases passed
        coding_submissions = CodeSubmission.query.filter_by(user_id=user_id).all()
        code_practice_scores = []
        for submission in coding_submissions:
            if submission.total_test_cases and submission.total_test_cases > 0:
                percentage = (submission.test_cases_passed / submission.total_test_cases) * 100
                code_practice_scores.append(percentage)
        code_practice_score = sum(code_practice_scores) / len(code_practice_scores) if code_practice_scores else 0
        
        # 2. Calculate Non-Technical Score (from ALL quiz attempts)
        # Include all quiz attempts - both Non-Technical quizzes and regular quizzes
        # This combines all quiz performance into the Non-Technical score
        quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
        non_technical_scores = []
        for attempt in quiz_attempts:
            try:
                # Include all quiz attempts that have valid scores
                # The score field is already stored as a percentage (0-100) in QuizAttempt
                # Score is calculated as: (obtained_marks / total_marks) * 100
                if attempt.score is not None and attempt.score >= 0:
                    # Score is already a percentage, use it directly
                    non_technical_scores.append(attempt.score)
            except Exception as e:
                # Skip if attempt has issues
                print(f"Warning: Could not process quiz attempt {attempt.id}: {str(e)}")
                continue
        
        non_technical_score = sum(non_technical_scores) / len(non_technical_scores) if non_technical_scores else 0
        
        # 3. Calculate AI Virtual Interview Score (from completed interviews)
        completed_interviews = InterviewSession.query.filter_by(
            user_id=user_id, 
            is_completed=True
        ).all()
        interview_scores = []
        for interview in completed_interviews:
            if interview.final_score is not None:
                interview_scores.append(interview.final_score)
        interview_score = sum(interview_scores) / len(interview_scores) if interview_scores else 0
        
        # Calculate overall Placement Readiness Score (weighted average)
        # Weights: Code Practice 40%, Non-Technical 30%, AI Virtual Interview 30%
        weights = {
            'code_practice': 0.40,
            'non_technical': 0.30,
            'interview': 0.30
        }
        
        # Only include components that have data
        total_weight = 0
        weighted_sum = 0
        
        if code_practice_scores:
            weighted_sum += code_practice_score * weights['code_practice']
            total_weight += weights['code_practice']
        if non_technical_scores:
            weighted_sum += non_technical_score * weights['non_technical']
            total_weight += weights['non_technical']
        if interview_scores:
            weighted_sum += interview_score * weights['interview']
            total_weight += weights['interview']
        
        # Calculate final score (normalize if some components are missing)
        if total_weight > 0:
            placement_readiness_score = weighted_sum / total_weight
        else:
            placement_readiness_score = 0
        
        return jsonify({
            'placement_readiness_score': round(placement_readiness_score, 2),
            'breakdown': {
                'code_practice': round(code_practice_score, 2),
                'non_technical': round(non_technical_score, 2),
                'interview': round(interview_score, 2)
            },
            'data_available': {
                'code_practice': len(code_practice_scores) > 0,
                'non_technical': len(non_technical_scores) > 0,
                'interview': len(interview_scores) > 0
            },
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name
            }
        }), 200
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in placement_readiness endpoint: {error_trace}")
        return jsonify({
            'error': str(e),
            'trace': error_trace if current_app.config.get('DEBUG', False) else None
        }), 500

