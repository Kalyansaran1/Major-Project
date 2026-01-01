"""
AI Chatbot routes for virtual interviews with structured flow
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.chatbot import (
    generate_interview_question, 
    evaluate_answer, 
    generate_interview_summary,
    extract_programming_languages
)
from utils.file_extractor import extract_text_from_file
from models import db, InterviewSession
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import tempfile
import json

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/start-interview', methods=['POST'])
@jwt_required()
def start_interview():
    """Start a new virtual interview session with structured flow"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        resume_text = data.get('resume_text', '')
        job_description = data.get('job_description', '')
        interview_type = data.get('interview_type', 'technical')  # 'technical', 'hr', 'behavioral'
        experience_level = data.get('experience_level', 'fresher')  # 'fresher', 'intermediate', 'experienced'
        total_questions = data.get('total_questions', 5)  # Default 5 questions
        
        # Create interview session in database
        session = InterviewSession(
            user_id=user_id,
            resume_text=resume_text,
            job_description=job_description,
            interview_type=interview_type,
            experience_level=experience_level,
            total_questions=total_questions,
            current_phase='introduction',
            question_number=0
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Generate first question: "Tell me about yourself"
        first_question = generate_interview_question(
            resume_text=resume_text,
            job_description=job_description,
            phase='introduction',
            question_number=0,
            conversation_history=[],
            interview_type=interview_type,
            experience_level=experience_level
        )
        
        # Update session
        session.question_number = 1
        session.total_questions_asked = 1
        conversation = [{
            'type': 'question',
            'content': first_question,
            'question_type': interview_type,
            'phase': 'introduction',
            'question_number': 1,
            'timestamp': datetime.utcnow().isoformat()
        }]
        session.conversation = json.dumps(conversation)
        db.session.commit()
        
        return jsonify({
            'session_id': session.id,
            'question': first_question,
            'question_type': interview_type,
            'phase': 'introduction',
            'question_number': 1,
            'total_questions': total_questions
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/answer', methods=['POST'])
@jwt_required()
def submit_answer():
    """Submit answer to interview question with evaluation and adaptive next question"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        session_id = data.get('session_id')
        answer = data.get('answer')
        
        if not session_id or not answer:
            return jsonify({'error': 'Session ID and answer required'}), 400
        
        # Get session from database
        session = InterviewSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if session.is_completed:
            return jsonify({'error': 'Interview already completed'}), 400
        
        # Load conversation
        conversation = json.loads(session.conversation) if session.conversation else []
        
        # Get last question
        last_q = None
        for msg in reversed(conversation):
            if msg.get('type') == 'question':
                last_q = msg
                break
        
        if not last_q:
            return jsonify({'error': 'No question found'}), 400
        
        # Evaluate answer with scoring
        evaluation = evaluate_answer(
            question=last_q['content'],
            answer=answer,
            question_type=session.interview_type,
            resume_text=session.resume_text,
            job_description=session.job_description
        )
        
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
        
        # Update session
        session.total_answers += 1
        
        # Calculate average score
        scores = [msg.get('overall_score', 0) for msg in conversation if msg.get('type') == 'evaluation']
        if scores:
            session.average_score = sum(scores) / len(scores)
        
        # Check if interview should continue
        if session.question_number >= session.total_questions:
            # Interview complete - generate summary
            summary = generate_interview_summary(
                conversation_history=conversation,
                resume_text=session.resume_text,
                job_description=session.job_description
            )
            session.evaluation_summary = summary
            session.is_completed = True
            session.ended_at = datetime.utcnow()
            session.conversation = json.dumps(conversation)
            db.session.commit()
            
            return jsonify({
                'session_id': session.id,
                'interview_completed': True,
                'summary': summary,
                'total_questions': session.total_questions_asked,
                'average_score': round(session.average_score, 1),
                'conversation': conversation
            }), 200
        
        # Determine next phase based on question number
        next_phase = determine_next_phase(session.question_number, session.resume_text, session.job_description)
        session.current_phase = next_phase
        
        # Get previous answer score for adaptive difficulty
        previous_score = evaluation['overall_score']
        
        # Generate next question
        next_question = generate_interview_question(
            resume_text=session.resume_text,
            job_description=session.job_description,
            phase=next_phase,
            question_number=session.question_number,
            conversation_history=conversation,
            interview_type=session.interview_type,
            experience_level=session.experience_level,
            previous_answer_score=previous_score
        )
        
        # Add next question to conversation
        conversation.append({
            'type': 'question',
            'content': next_question,
            'question_type': session.interview_type,
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
            'question_type': session.interview_type,
            'phase': next_phase,
            'question_number': session.question_number,
            'total_questions': session.total_questions,
            'conversation': conversation[-5:]  # Return last 5 messages
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def determine_next_phase(question_number, resume_text, job_description):
    """
    Determine interview phase based on question number:
    - Q1: Introduction
    - Q2-Q3: Resume-based (if resume provided)
    - Q4-Q5: JD-based (if JD provided)
    - Q6+: General
    """
    if question_number == 0:
        return 'introduction'
    elif question_number <= 2 and resume_text:
        return 'resume'
    elif question_number <= 4 and job_description:
        return 'jd'
    else:
        return 'general'

@chatbot_bp.route('/session/<int:session_id>', methods=['GET'])
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

@chatbot_bp.route('/end-interview/<int:session_id>', methods=['POST'])
@jwt_required()
def end_interview(session_id):
    """End interview session and get summary"""
    try:
        user_id = get_jwt_identity()
        session = InterviewSession.query.get_or_404(session_id)
        
        if session.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        if session.is_completed:
            return jsonify({
                'message': 'Interview already completed',
                'session': session.to_dict()
            }), 200
        
        # Generate summary if not already generated
        conversation = json.loads(session.conversation) if session.conversation else []
        if not session.evaluation_summary:
            summary = generate_interview_summary(
                conversation_history=conversation,
                resume_text=session.resume_text,
                job_description=session.job_description
            )
            session.evaluation_summary = summary
        
        # Mark as completed
        session.is_completed = True
        session.ended_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Interview ended',
            'session': session.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/extract-text', methods=['POST'])
@jwt_required()
def extract_text():
    """Extract text from uploaded file (PDF, JPG, PNG)"""
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
        
        if file_ext not in ['pdf', 'jpg', 'jpeg', 'png']:
            return jsonify({'error': 'Unsupported file type. Please upload PDF, JPG, or PNG'}), 400
        
        # Save file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{user_id}_{filename}")
        file.save(temp_file_path)
        
        try:
            # Extract text from file
            extracted_text = extract_text_from_file(temp_file_path, file_ext)
            
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            return jsonify({
                'text': extracted_text,
                'filename': filename
            }), 200
        
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({'error': f'Error extracting text: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
