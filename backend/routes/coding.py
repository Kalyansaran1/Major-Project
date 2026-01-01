"""
Coding routes for live coding practice
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Question, CodeSubmission, db
from utils.auth import role_required
from utils.compiler import execute_code, run_test_cases
from utils.judge_v2 import (
    ExecutionMode,
    execute_run_mode,
    execute_submit_mode
)
from utils.leaderboard import update_leaderboard
import json

coding_bp = Blueprint('coding', __name__)

@coding_bp.route('/questions/<int:question_id>', methods=['GET'])
@jwt_required()
def get_question(question_id):
    """Get coding question details"""
    try:
        question = Question.query.get_or_404(question_id)
        
        if question.type != 'coding':
            return jsonify({'error': 'Not a coding question'}), 400
        
        return jsonify({
            'question': question.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coding_bp.route('/execute', methods=['POST'])
@jwt_required()
def execute():
    """
    RUN MODE: Practice execution
    - Allow main() or equivalent
    - Execute code normally
    - Capture and show stdout
    - Do not judge correctness strictly
    """
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        stdin = data.get('stdin', '')
        question_id = data.get('question_id')
        
        if not code or not language:
            return jsonify({'error': 'Code and language required'}), 400
        
        if language not in ['c', 'cpp', 'python', 'java']:
            return jsonify({'error': 'Unsupported language'}), 400
        
        # Get sample input from first test case if question_id provided
        sample_input = None
        if question_id:
            question = Question.query.get(question_id)
            if question and question.test_cases:
                test_cases = json.loads(question.test_cases) if isinstance(question.test_cases, str) else question.test_cases
                if test_cases:
                    sample_input = test_cases[0].get('input')
        
        # Execute in RUN mode - just execute code, show output
        # Run mode = user program controls input/output (like normal compiler)
        result = execute_run_mode(code, language, stdin, sample_input)
        
        # Format output - if empty, show "(no output)"
        if not result.get('output') or result.get('output').strip() == '':
            result['output'] = '(no output)'
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coding_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit():
    """
    SUBMIT MODE: Function-based judging
    - Do NOT execute user code as a program
    - Do NOT rely on printed output
    - Do NOT require main()
    - Platform supplies inputs
    - Extract solution function
    - Call it programmatically
    - Capture return value
    - Compare with expected output
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        question_id = data.get('question_id')
        code = data.get('code')
        language = data.get('language')
        
        if not question_id or not code or not language:
            return jsonify({'error': 'Missing required fields'}), 400
        
        question = Question.query.get_or_404(question_id)
        
        if question.type != 'coding':
            return jsonify({'error': 'Not a coding question'}), 400
        
        # Get test cases
        test_cases = json.loads(question.test_cases) if question.test_cases else []
        
        if not test_cases:
            return jsonify({'error': 'No test cases available'}), 400
        
        # Execute in SUBMIT mode (function-based judging)
        result = execute_submit_mode(code, language, test_cases)
        
        # Create submission record
        submission = CodeSubmission(
            user_id=user_id,
            question_id=question_id,
            language=language,
            code=code,
            output=json.dumps(result.get('results', [])),
            status=result.get('status', 'wrong_answer'),
            execution_time=result.get('execution_time', 0.0),
            test_cases_passed=result.get('passed', 0),
            total_test_cases=result.get('total', 0)
        )
        
        db.session.add(submission)
        db.session.commit()
        
        # Update leaderboard
        update_leaderboard(user_id)
        
        return jsonify({
            'submission': submission.to_dict(),
            'test_results': result.get('results', []),
            'passed': result.get('passed', 0),
            'total': result.get('total', 0),
            'status': result.get('status', 'wrong_answer')
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@coding_bp.route('/submissions', methods=['GET'])
@jwt_required()
def get_submissions():
    """Get user's code submissions"""
    try:
        user_id = get_jwt_identity()
        question_id = request.args.get('question_id')
        
        query = CodeSubmission.query.filter_by(user_id=user_id)
        
        if question_id:
            query = query.filter_by(question_id=question_id)
        
        submissions = query.order_by(CodeSubmission.submitted_at.desc()).all()
        
        return jsonify({
            'submissions': [s.to_dict() for s in submissions]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@coding_bp.route('/submissions/last', methods=['GET'])
@jwt_required()
def get_last_submission():
    """
    Get the last submitted code for a question
    LeetCode-style: Retrieve last submitted code into editor
    """
    try:
        user_id = get_jwt_identity()
        question_id = request.args.get('question_id')
        language = request.args.get('language')  # Optional: filter by language
        
        if not question_id:
            return jsonify({'error': 'question_id required'}), 400
        
        query = CodeSubmission.query.filter_by(
            user_id=user_id,
            question_id=question_id
        )
        
        if language:
            query = query.filter_by(language=language)
        
        # Get the most recent submission
        last_submission = query.order_by(CodeSubmission.submitted_at.desc()).first()
        
        if not last_submission:
            return jsonify({
                'submission': None,
                'message': 'No previous submission found'
            }), 200
        
        return jsonify({
            'submission': last_submission.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

