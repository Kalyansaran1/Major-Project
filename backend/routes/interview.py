"""
Enhanced AI Virtual Interview routes for TR and HR interview types
Supports interview type selection, resume/JD upload, and structured interview flow
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.file_extractor import extract_text_from_file
from utils.resume_processor import process_resume, process_job_description
from utils.interview_ai import (
    generate_interview_question, determine_phase_tr, determine_phase_hr,
    evaluate_answer, calculate_final_score_tr, calculate_final_score_hr,
    generate_interview_summary, generate_practice_materials
)
from models import db, InterviewSession, ResumeData, JobDescriptionData, InterviewAnswer, InterviewResult, Notification
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import tempfile
import json

interview_bp = Blueprint('interview', __name__)

@interview_bp.route('/select-interview-type', methods=['POST'])
@jwt_required()
def select_interview_type():
    """
    STEP 1: Select interview type (TR or HR)
    POST /api/interview/select-interview-type
    Body: { "interview_type": "TR" | "HR" }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        interview_type = data.get('interview_type', '').upper()
        
        if interview_type not in ['TR', 'HR']:
            return jsonify({'error': 'Invalid interview type. Must be "TR" (Technical) or "HR"'}), 400
        
        # Store interview type in session (could use Flask session or return to frontend to store)
        # For now, we'll return it and frontend can pass it to subsequent requests
        return jsonify({
            'message': 'Interview type selected',
            'interview_type': interview_type,
            'next_step': 'upload_resume_jd'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@interview_bp.route('/upload-resume', methods=['POST'])
@jwt_required()
def upload_resume():
    """
    STEP 2: Upload and process resume
    POST /api/interview/upload-resume
    Form data: file (PDF, JPG, PNG, TXT)
    """
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'txt']
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}'}), 400
        
        # Save file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{user_id}_{filename}")
        file.save(temp_file_path)
        
        try:
            # Extract text from file
            extracted_text = extract_text_from_file(temp_file_path, file_ext)
            
            # Process resume to extract structured data
            resume_data = process_resume(extracted_text)
            
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            return jsonify({
                'message': 'Resume uploaded and processed successfully',
                'resume_text': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text,
                'resume_data': resume_data,
                'filename': filename
            }), 200
        
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({'error': f'Error processing resume: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@interview_bp.route('/upload-jd', methods=['POST'])
@jwt_required()
def upload_jd():
    """
    STEP 2: Upload and process Job Description
    POST /api/interview/upload-jd
    Form data: file (PDF, TXT)
    Body (optional): resume_skills (JSON array) for skill mapping
    """
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        allowed_extensions = ['pdf', 'txt']
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Unsupported file type. Allowed: PDF, TXT'}), 400
        
        # Get resume skills from request if provided (for skill mapping)
        resume_skills = request.form.get('resume_skills')
        if resume_skills:
            try:
                resume_skills = json.loads(resume_skills)
            except:
                resume_skills = None
        
        # Save file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{user_id}_jd_{filename}")
        file.save(temp_file_path)
        
        try:
            # Extract text from file
            extracted_text = extract_text_from_file(temp_file_path, file_ext)
            
            # Process JD to extract structured data and map skills
            jd_data = process_job_description(extracted_text, resume_skills)
            
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            return jsonify({
                'message': 'Job description uploaded and processed successfully',
                'jd_text': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text,
                'jd_data': jd_data,
                'filename': filename
            }), 200
        
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({'error': f'Error processing job description: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@interview_bp.route('/start-interview', methods=['POST'])
@jwt_required()
def start_interview():
    """
    STEP 3 & 4: Start interview session
    POST /api/interview/start-interview
    Body: {
        "interview_type": "TR" | "HR",
        "resume_text": "...",
        "job_description": "...",
        "resume_data": {...},
        "jd_data": {...},
        "resume_file_path": "...",
        "jd_file_path": "..."
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        interview_type = data.get('interview_type', 'TR').upper()
        resume_text = data.get('resume_text', '')
        job_description = data.get('job_description', '')
        resume_data_dict = data.get('resume_data', {})
        jd_data_dict = data.get('jd_data', {})
        resume_file_path = data.get('resume_file_path', '')
        jd_file_path = data.get('jd_file_path', '')
        
        if interview_type not in ['TR', 'HR']:
            return jsonify({'error': 'Invalid interview type. Must be "TR" or "HR"'}), 400
        
        # Calculate dynamic number of questions based on resume and JD
        from utils.interview_ai import calculate_total_questions
        
        # Determine experience level from resume data
        experience_level = 'fresher'  # Default
        if resume_data_dict:
            experience_years = resume_data_dict.get('experience_years', 0)
            if experience_years >= 3:
                experience_level = 'experienced'
            elif experience_years >= 1:
                experience_level = 'intermediate'
        
        # Calculate total questions dynamically
        total_questions = calculate_total_questions(
            interview_type=interview_type,
            resume_data=resume_data_dict,
            jd_data=jd_data_dict,
            experience_level=experience_level
        )
        
        # Create interview session
        session = InterviewSession(
            user_id=user_id,
            resume_text=resume_text,
            job_description=job_description,
            interview_type=interview_type,
            experience_level=experience_level,
            resume_file_path=resume_file_path,
            jd_file_path=jd_file_path,
            current_phase='introduction',
            question_number=0,
            total_questions=total_questions  # Dynamic based on resume and JD
        )
        
        db.session.add(session)
        db.session.flush()  # Get session.id
        
        # Store resume data
        if resume_data_dict:
            resume_data = ResumeData(
                session_id=session.id,
                skills=json.dumps(resume_data_dict.get('skills', [])),
                programming_languages=json.dumps(resume_data_dict.get('programming_languages', [])),
                projects=json.dumps(resume_data_dict.get('projects', [])),
                certificates=json.dumps(resume_data_dict.get('certificates', [])),
                experience_years=resume_data_dict.get('experience_years', 0)
            )
            db.session.add(resume_data)
        
        # Store JD data
        if jd_data_dict:
            jd_data = JobDescriptionData(
                session_id=session.id,
                required_skills=json.dumps(jd_data_dict.get('required_skills', [])),
                matching_skills=json.dumps(jd_data_dict.get('matching_skills', [])),
                missing_skills=json.dumps(jd_data_dict.get('missing_skills', [])),
                job_title=jd_data_dict.get('job_title'),
                experience_required=jd_data_dict.get('experience_required')
            )
            db.session.add(jd_data)
        
        db.session.commit()
        
        # Generate first question: "Introduce yourself"
        first_question = generate_interview_question(
            interview_type=interview_type,
            resume_text=resume_text,
            job_description=job_description,
            phase='introduction',
            question_number=0,
            conversation_history=[],
            experience_level='fresher',
            resume_data=resume_data_dict,
            jd_data=jd_data_dict
        )
        
        # Update session
        session.question_number = 1
        session.total_questions_asked = 1
        conversation = [{
            'type': 'question',
            'content': first_question,
            'phase': 'introduction',
            'question_number': 1,
            'timestamp': datetime.utcnow().isoformat()
        }]
        session.conversation = json.dumps(conversation)
        db.session.commit()
        
        return jsonify({
            'session_id': session.id,
            'question': first_question,
            'interview_type': interview_type,
            'phase': 'introduction',
            'question_number': 1,
            'total_questions': session.total_questions
        }), 200
    
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error starting interview: {error_trace}")  # Log full error for debugging
        # Return user-friendly error message
        error_msg = str(e)
        if 'Unknown column' in error_msg or 'resume_file_path' in error_msg or 'final_score' in error_msg or 'score_breakdown' in error_msg:
            error_msg = 'Database schema mismatch. Please run: python backend/migrate_interview_columns.py'
        return jsonify({
            'error': error_msg,
            'error_type': type(e).__name__
        }), 500

@interview_bp.route('/submit-answer', methods=['POST'])
@jwt_required()
def submit_answer():
    """
    STEP 6: Submit answer and get next question
    POST /api/interview/submit-answer
    Body: {
        "session_id": 123,
        "answer": "...",
        "time_taken_seconds": 120
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        session_id = data.get('session_id')
        answer = data.get('answer', '')
        time_taken_seconds = data.get('time_taken_seconds', 0)
        
        if not session_id or not answer:
            return jsonify({'error': 'Session ID and answer required'}), 400
        
        # Get session
        session = InterviewSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if session.is_completed:
            return jsonify({'error': 'Interview already completed'}), 400
        
        # Load conversation and resume/JD data
        conversation = json.loads(session.conversation) if session.conversation else []
        
        # Get last question
        last_question = None
        last_phase = 'introduction'
        for msg in reversed(conversation):
            if msg.get('type') == 'question':
                last_question = msg.get('content')
                last_phase = msg.get('phase', 'introduction')
                break
        
        if not last_question:
            return jsonify({'error': 'No question found'}), 400
        
        # Get resume and JD data
        resume_data_obj = ResumeData.query.filter_by(session_id=session_id).first()
        jd_data_obj = JobDescriptionData.query.filter_by(session_id=session_id).first()
        
        resume_data = resume_data_obj.to_dict() if resume_data_obj else None
        jd_data = jd_data_obj.to_dict() if jd_data_obj else None
        
        # Evaluate answer
        evaluation = evaluate_answer(
            question=last_question,
            answer=answer,
            interview_type=session.interview_type,
            phase=last_phase,
            resume_text=session.resume_text,
            job_description=session.job_description
        )
        
        # Save answer to database
        interview_answer = InterviewAnswer(
            session_id=session_id,
            question_number=session.question_number,
            question=last_question,
            answer=answer,
            phase=last_phase,
            correctness_score=evaluation['correctness'],
            clarity_score=evaluation['clarity'],
            confidence_score=evaluation['confidence'],
            overall_score=evaluation['overall_score'],
            feedback=evaluation['feedback'],
            time_taken_seconds=time_taken_seconds
        )
        db.session.add(interview_answer)
        
        # Add answer and evaluation to conversation
        conversation.append({
            'type': 'answer',
            'content': answer,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        conversation.append({
            'type': 'evaluation',
            'feedback': evaluation['feedback'],
            'correctness': evaluation['correctness'],
            'clarity': evaluation['clarity'],
            'confidence': evaluation['confidence'],
            'overall_score': evaluation['overall_score'],
            'timestamp': datetime.utcnow().isoformat()
        })
        
        session.total_answers += 1
        
        # Check if interview should continue
        if session.question_number >= session.total_questions:
            # Interview complete - calculate final score and generate summary
            return complete_interview(session, conversation, resume_data, jd_data, interview_answer)
        
        # Determine next phase
        if session.interview_type == 'TR':
            next_phase = determine_phase_tr(session.question_number, resume_data, jd_data)
        else:
            next_phase = determine_phase_hr(session.question_number)
        
        session.current_phase = next_phase
        
        # Generate next question
        next_question = generate_interview_question(
            interview_type=session.interview_type,
            resume_text=session.resume_text,
            job_description=session.job_description,
            phase=next_phase,
            question_number=session.question_number,
            conversation_history=conversation,
            experience_level='fresher',
            previous_answer_score=evaluation['overall_score'],
            resume_data=resume_data,
            jd_data=jd_data
        )
        
        # Add next question to conversation
        conversation.append({
            'type': 'question',
            'content': next_question,
            'phase': next_phase,
            'question_number': session.question_number + 1,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Update session
        session.question_number += 1
        session.total_questions_asked += 1
        session.conversation = json.dumps(conversation)
        db.session.commit()
        
        return jsonify({
            'session_id': session.id,
            'feedback': evaluation['feedback'],
            'scores': {
                'correctness': evaluation['correctness'],
                'clarity': evaluation['clarity'],
                'confidence': evaluation['confidence'],
                'overall': evaluation['overall_score']
            },
            'next_question': next_question,
            'interview_type': session.interview_type,
            'phase': next_phase,
            'question_number': session.question_number,
            'total_questions': session.total_questions
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def complete_interview(session, conversation, resume_data, jd_data, last_answer):
    """Helper function to complete interview and calculate final results"""
    try:
        # Get all answers
        answers = InterviewAnswer.query.filter_by(session_id=session.id).order_by(InterviewAnswer.question_number).all()
        
        # Convert to list of dicts for scoring
        answers_list = []
        for ans in answers:
            answers_list.append({
                'phase': ans.phase,
                'overall_score': ans.overall_score,
                'correctness_score': ans.correctness_score,
                'clarity_score': ans.clarity_score,
                'confidence_score': ans.confidence_score
            })
        
        # Calculate final score based on interview type
        if session.interview_type == 'TR':
            score_result = calculate_final_score_tr(answers_list)
        else:
            score_result = calculate_final_score_hr(answers_list)
        
        # Generate summary
        summary_data = generate_interview_summary(
            conversation_history=conversation,
            interview_type=session.interview_type,
            final_score=score_result['total_score'],
            resume_text=session.resume_text,
            job_description=session.job_description,
            score_breakdown=score_result.get('breakdown')
        )
        
        # Generate practice materials based on weak skills
        weak_skills = summary_data.get('weak_skills', [])
        practice_materials = {}
        if weak_skills:
            practice_materials = generate_practice_materials(weak_skills, session.interview_type)
        
        # Save final result
        result = InterviewResult(
            session_id=session.id,
            total_score=score_result['total_score'],
            strengths=json.dumps(summary_data.get('strengths', [])),
            weaknesses=json.dumps(summary_data.get('weaknesses', [])),
            improvements=json.dumps(summary_data.get('improvements', [])),
            suggested_resources=json.dumps(summary_data.get('suggested_resources', []))
        )
        
        # Set component scores
        breakdown = score_result.get('breakdown', {})
        if session.interview_type == 'TR':
            result.introduction_score = breakdown.get('introduction_score', 0)
            result.projects_resume_score = breakdown.get('projects_resume_score', 0)
            result.programming_score = breakdown.get('programming_score', 0)
            result.jd_gap_skills_score = breakdown.get('jd_gap_skills_score', 0)
            result.communication_score = breakdown.get('communication_score', 0)
        else:
            result.hr_introduction_score = breakdown.get('hr_introduction_score', 0)
            result.hr_communication_score = breakdown.get('hr_communication_score', 0)
            result.hr_confidence_score = breakdown.get('hr_confidence_score', 0)
            result.hr_behavioral_score = breakdown.get('hr_behavioral_score', 0)
        
        db.session.add(result)
        
        # Update session
        session.final_score = score_result['total_score']
        session.score_breakdown = json.dumps(breakdown)
        # Store full summary data as JSON (including weak_skills) for practice recommendations
        session.evaluation_summary = json.dumps(summary_data)
        session.is_completed = True
        session.ended_at = datetime.utcnow()
        session.conversation = json.dumps(conversation)
        
        # Create notification for interview completion with feedback
        feedback_summary = summary_data.get('summary', '')[:200]  # First 200 chars
        if len(summary_data.get('summary', '')) > 200:
            feedback_summary += '...'
        
        notification = Notification(
            user_id=session.user_id,
            title='Interview Completed - Feedback Available',
            message=f'Your {session.interview_type} interview is complete! Score: {score_result["total_score"]:.1f}%. {feedback_summary}',
            type='interview_feedback',
            link=f'/interview/result/{session.id}'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'session_id': session.id,
            'interview_completed': True,
            'final_score': score_result['total_score'],
            'score_breakdown': breakdown,
            'summary': summary_data.get('summary', ''),
            'strengths': summary_data.get('strengths', []),
            'weaknesses': summary_data.get('weaknesses', []),
            'weak_skills': summary_data.get('weak_skills', []),
            'improvements': summary_data.get('improvements', []),
            'suggested_resources': summary_data.get('suggested_resources', []),
            'practice_materials': practice_materials
        }), 200
    
    except Exception as e:
        db.session.rollback()
        raise e

@interview_bp.route('/end-interview/<int:session_id>', methods=['POST'])
@jwt_required()
def end_interview(session_id):
    """
    STEP 8: End interview early and get results
    POST /api/interview/end-interview/<session_id>
    """
    try:
        user_id = get_jwt_identity()
        session = InterviewSession.query.get_or_404(session_id)
        
        if session.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if session.is_completed:
            # Return existing results
            result = InterviewResult.query.filter_by(session_id=session_id).first()
            if result:
                return jsonify({
                    'message': 'Interview already completed',
                    'result': result.to_dict(),
                    'session': session.to_dict()
                }), 200
        
        # Complete the interview
        conversation = json.loads(session.conversation) if session.conversation else []
        resume_data_obj = ResumeData.query.filter_by(session_id=session_id).first()
        jd_data_obj = JobDescriptionData.query.filter_by(session_id=session_id).first()
        
        resume_data = resume_data_obj.to_dict() if resume_data_obj else None
        jd_data = jd_data_obj.to_dict() if jd_data_obj else None
        
        # Get last answer if exists
        last_answer = InterviewAnswer.query.filter_by(session_id=session_id).order_by(InterviewAnswer.question_number.desc()).first()
        
        return complete_interview(session, conversation, resume_data, jd_data, last_answer)
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@interview_bp.route('/interview-result/<int:session_id>', methods=['GET'])
@jwt_required()
def get_interview_result(session_id):
    """
    STEP 8: Get final interview result
    GET /api/interview/interview-result/<session_id>
    """
    try:
        user_id = get_jwt_identity()
        session = InterviewSession.query.get_or_404(session_id)
        
        if session.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        result = InterviewResult.query.filter_by(session_id=session_id).first()
        if not result:
            return jsonify({'error': 'Interview result not found. Interview may not be completed yet.'}), 404
        
        # Get weak skills from evaluation summary if available
        weak_skills = []
        if session.evaluation_summary:
            try:
                # evaluation_summary is stored as JSON with full summary_data
                summary_dict = json.loads(session.evaluation_summary) if isinstance(session.evaluation_summary, str) else {}
                weak_skills = summary_dict.get('weak_skills', [])
            except (json.JSONDecodeError, TypeError):
                # Fallback: If evaluation_summary is just text (old format), try to get from result
                try:
                    result_dict = result.to_dict()
                    # Weak skills might be in weaknesses field
                    weaknesses = result_dict.get('weaknesses', [])
                    if isinstance(weaknesses, str):
                        weaknesses = json.loads(weaknesses)
                    weak_skills = weaknesses[:3] if weaknesses else []  # Use first 3 as weak skills
                except:
                    pass
        
        # Generate practice materials if weak skills found
        practice_materials = {}
        if weak_skills:
            practice_materials = generate_practice_materials(weak_skills, session.interview_type)
        
        result_dict = result.to_dict()
        result_dict['weak_skills'] = weak_skills
        result_dict['practice_materials'] = practice_materials
        
        # Also include summary data if available from evaluation_summary
        if session.evaluation_summary:
            try:
                summary_dict = json.loads(session.evaluation_summary) if isinstance(session.evaluation_summary, str) else {}
                if isinstance(summary_dict, dict):
                    result_dict['summary'] = summary_dict.get('summary', '')
                    # Only override if not already set from result
                    if not result_dict.get('strengths'):
                        result_dict['strengths'] = summary_dict.get('strengths', [])
                    if not result_dict.get('weaknesses'):
                        result_dict['weaknesses'] = summary_dict.get('weaknesses', [])
                    if not result_dict.get('improvements'):
                        result_dict['improvements'] = summary_dict.get('improvements', [])
                    if not result_dict.get('suggested_resources'):
                        result_dict['suggested_resources'] = summary_dict.get('suggested_resources', [])
                    if not result_dict.get('weak_skills'):
                        result_dict['weak_skills'] = summary_dict.get('weak_skills', [])
            except (json.JSONDecodeError, TypeError):
                # If evaluation_summary is just text, use it as summary
                if isinstance(session.evaluation_summary, str) and not result_dict.get('summary'):
                    result_dict['summary'] = session.evaluation_summary
        
        return jsonify({
            'session': session.to_dict(),
            'result': result_dict
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@interview_bp.route('/session/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    """Get interview session details"""
    try:
        user_id = get_jwt_identity()
        session = InterviewSession.query.get_or_404(session_id)
        
        if session.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'session': session.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@interview_bp.route('/practice-recommendations/<int:session_id>', methods=['GET'])
@jwt_required()
def get_practice_recommendations(session_id):
    """
    Get practice recommendations based on weak skills from interview
    GET /api/interview/practice-recommendations/<session_id>
    """
    try:
        user_id = get_jwt_identity()
        session = InterviewSession.query.get_or_404(session_id)
        
        if session.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if not session.is_completed:
            return jsonify({'error': 'Interview not completed yet'}), 400
        
        # Get weak skills from evaluation summary
        weak_skills = []
        try:
            # Try to get from evaluation_summary JSON (stored as full summary_data)
            if session.evaluation_summary:
                summary_dict = json.loads(session.evaluation_summary) if isinstance(session.evaluation_summary, str) else {}
                weak_skills = summary_dict.get('weak_skills', [])
            
            # If not found, try to get from result weaknesses field as fallback
            if not weak_skills:
                result = InterviewResult.query.filter_by(session_id=session_id).first()
                if result and result.weaknesses:
                    try:
                        weaknesses = json.loads(result.weaknesses) if isinstance(result.weaknesses, str) else result.weaknesses
                        weak_skills = weaknesses[:5] if isinstance(weaknesses, list) else []  # Use first 5 as weak skills
                    except (json.JSONDecodeError, TypeError):
                        pass
        except Exception as e:
            print(f"Error extracting weak skills: {e}")
        
        # Generate practice materials
        practice_materials = {}
        if weak_skills:
            practice_materials = generate_practice_materials(weak_skills, session.interview_type)
        
        return jsonify({
            'weak_skills': weak_skills,
            'practice_materials': practice_materials,
            'interview_type': session.interview_type
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

