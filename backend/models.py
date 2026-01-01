"""
Database models for the Interview Preparation Platform
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
import pymysql

# Register PyMySQL as MySQLdb for SQLAlchemy compatibility
pymysql.install_as_MySQLdb()

# Initialize SQLAlchemy with engine options support
db = SQLAlchemy()

# Note: SQLALCHEMY_ENGINE_OPTIONS from config.py will be automatically used
# by Flask-SQLAlchemy when db.init_app() is called

class User(db.Model):
    """User model for Students, Faculty, and Admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'faculty', 'admin'
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    submissions = db.relationship('CodeSubmission', backref='user', lazy=True, cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True, cascade='all, delete-orphan')
    resources = db.relationship('Resource', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Company(db.Model):
    """Company model for company-wise interview preparation"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='company', lazy=True)
    resources = db.relationship('Resource', backref='company', lazy=True)
    quizzes = db.relationship('Quiz', backref='company', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'logo_url': self.logo_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Question(db.Model):
    """Question model for coding and non-coding questions"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'coding', 'mcq', 'fill_blank'
    difficulty = db.Column(db.String(20))  # 'easy', 'medium', 'hard'
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    tags = db.Column(db.String(200))  # Comma-separated tags
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # For coding questions
    test_cases = db.Column(db.Text)  # JSON string of test cases
    starter_code = db.Column(db.Text)
    solution = db.Column(db.Text)
    
    # For MCQ questions
    options = db.Column(db.Text)  # JSON string of options
    correct_answer = db.Column(db.String(10))  # Option index like 'A', 'B', 'C', 'D'
    marks = db.Column(db.Integer, default=1)  # Marks for the question
    
    # For fill-in-the-blank
    blanks = db.Column(db.Text)  # JSON string of blank positions and answers
    
    # Relationships
    submissions = db.relationship('CodeSubmission', backref='question', lazy=True)
    quiz_questions = db.relationship('QuizQuestion', backref='question', lazy=True)
    
    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'difficulty': self.difficulty,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
        
        if self.type == 'coding':
            data['test_cases'] = json.loads(self.test_cases) if self.test_cases else []
            data['starter_code'] = self.starter_code
        elif self.type == 'mcq':
            data['options'] = json.loads(self.options) if self.options else []
            data['correct_answer'] = self.correct_answer
            data['marks'] = self.marks if self.marks else 1
        elif self.type == 'fill_blank':
            data['blanks'] = json.loads(self.blanks) if self.blanks else []
        
        return data

class CodeSubmission(db.Model):
    """Code submission model for tracking student coding attempts"""
    __tablename__ = 'code_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    language = db.Column(db.String(20), nullable=False)  # 'c', 'cpp', 'python', 'java'
    code = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text)
    status = db.Column(db.String(20))  # 'accepted', 'wrong_answer', 'runtime_error', 'timeout'
    execution_time = db.Column(db.Float)  # Time in seconds
    memory_used = db.Column(db.Float)  # Memory in MB
    test_cases_passed = db.Column(db.Integer, default=0)
    total_test_cases = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'language': self.language,
            'code': self.code,
            'output': self.output,
            'status': self.status,
            'execution_time': self.execution_time,
            'memory_used': self.memory_used,
            'test_cases_passed': self.test_cases_passed,
            'total_test_cases': self.total_test_cases,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }

class Quiz(db.Model):
    """Quiz model for creating assessments"""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    duration_minutes = db.Column(db.Integer, default=60)
    total_marks = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_by': self.created_by,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'duration_minutes': self.duration_minutes,
            'total_marks': self.total_marks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active
        }

class QuizQuestion(db.Model):
    """Many-to-many relationship between Quiz and Question"""
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    marks = db.Column(db.Integer, default=10)
    order = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'question_id': self.question_id,
            'question': self.question.to_dict() if self.question else None,
            'marks': self.marks,
            'order': self.order
        }

class QuizAttempt(db.Model):
    """Quiz attempt model for tracking student quiz submissions"""
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    answers = db.Column(db.Text)  # JSON string of answers
    score = db.Column(db.Float, default=0)
    total_marks = db.Column(db.Float)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    time_taken_minutes = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'quiz_id': self.quiz_id,
            'answers': json.loads(self.answers) if self.answers else {},
            'score': self.score,
            'total_marks': self.total_marks,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'time_taken_minutes': self.time_taken_minutes
        }

class InterviewSession(db.Model):
    """AI Interview Session model - Enhanced for TR/HR types"""
    __tablename__ = 'interview_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resume_text = db.Column(db.Text)
    job_description = db.Column(db.Text)
    interview_type = db.Column(db.String(20), default='TR')  # 'TR' (Technical), 'HR' (HR Interview)
    experience_level = db.Column(db.String(20), default='fresher')  # 'fresher', 'intermediate', 'experienced'
    
    # File paths
    resume_file_path = db.Column(db.String(500))
    jd_file_path = db.Column(db.String(500))
    
    # Interview state
    current_phase = db.Column(db.String(20), default='introduction')  # 'introduction', 'resume', 'programming', 'jd_skills', 'scenario'
    question_number = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=8)  # Default 8 questions
    
    # Results
    total_questions_asked = db.Column(db.Integer, default=0)
    total_answers = db.Column(db.Integer, default=0)
    final_score = db.Column(db.Float, default=0.0)  # Out of 100
    conversation = db.Column(db.Text)  # JSON string of conversation
    evaluation_summary = db.Column(db.Text)  # Final AI summary
    
    # Detailed scoring breakdown (JSON)
    score_breakdown = db.Column(db.Text)  # JSON with component scores
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='interview_sessions')
    resume_data = db.relationship('ResumeData', backref='session', uselist=False, cascade='all, delete-orphan')
    jd_data = db.relationship('JobDescriptionData', backref='session', uselist=False, cascade='all, delete-orphan')
    answers = db.relationship('InterviewAnswer', backref='session', lazy=True, cascade='all, delete-orphan')
    result = db.relationship('InterviewResult', backref='session', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resume_text': self.resume_text,
            'job_description': self.job_description,
            'interview_type': self.interview_type,
            'experience_level': self.experience_level,
            'resume_file_path': self.resume_file_path,
            'jd_file_path': self.jd_file_path,
            'current_phase': self.current_phase,
            'question_number': self.question_number,
            'total_questions': self.total_questions,
            'total_questions_asked': self.total_questions_asked,
            'total_answers': self.total_answers,
            'final_score': self.final_score,
            'conversation': json.loads(self.conversation) if self.conversation else [],
            'evaluation_summary': self.evaluation_summary,
            'score_breakdown': json.loads(self.score_breakdown) if self.score_breakdown else {},
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'is_completed': self.is_completed
        }

class ResumeData(db.Model):
    """Extracted data from resume"""
    __tablename__ = 'resume_data'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False, unique=True)
    
    # Extracted information
    skills = db.Column(db.Text)  # JSON array of skills
    programming_languages = db.Column(db.Text)  # JSON array of languages
    projects = db.Column(db.Text)  # JSON array of projects
    certificates = db.Column(db.Text)  # JSON array of certificates
    experience_years = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'skills': json.loads(self.skills) if self.skills else [],
            'programming_languages': json.loads(self.programming_languages) if self.programming_languages else [],
            'projects': json.loads(self.projects) if self.projects else [],
            'certificates': json.loads(self.certificates) if self.certificates else [],
            'experience_years': self.experience_years,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class JobDescriptionData(db.Model):
    """Extracted data from job description"""
    __tablename__ = 'jd_data'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False, unique=True)
    
    # Extracted information
    required_skills = db.Column(db.Text)  # JSON array of required skills
    matching_skills = db.Column(db.Text)  # JSON array of skills matching resume
    missing_skills = db.Column(db.Text)  # JSON array of missing/weak skills (HIGH PRIORITY)
    job_title = db.Column(db.String(200))
    experience_required = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'required_skills': json.loads(self.required_skills) if self.required_skills else [],
            'matching_skills': json.loads(self.matching_skills) if self.matching_skills else [],
            'missing_skills': json.loads(self.missing_skills) if self.missing_skills else [],
            'job_title': self.job_title,
            'experience_required': self.experience_required,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class InterviewAnswer(db.Model):
    """Individual interview answer with evaluation"""
    __tablename__ = 'interview_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    
    # Question and answer
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    phase = db.Column(db.String(50))  # 'introduction', 'resume', 'programming', 'jd_skills', 'scenario'
    
    # Evaluation scores (out of 10, will be converted to percentage)
    correctness_score = db.Column(db.Float)  # 0-10
    clarity_score = db.Column(db.Float)  # 0-10
    confidence_score = db.Column(db.Float)  # 0-10
    overall_score = db.Column(db.Float)  # 0-10 (weighted average)
    
    # Feedback
    feedback = db.Column(db.Text)
    
    # Time tracking
    time_taken_seconds = db.Column(db.Integer)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question_number': self.question_number,
            'question': self.question,
            'answer': self.answer,
            'phase': self.phase,
            'correctness_score': self.correctness_score,
            'clarity_score': self.clarity_score,
            'confidence_score': self.confidence_score,
            'overall_score': self.overall_score,
            'feedback': self.feedback,
            'time_taken_seconds': self.time_taken_seconds,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }

class InterviewResult(db.Model):
    """Final interview result with detailed scoring breakdown"""
    __tablename__ = 'interview_results'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False, unique=True)
    
    # Final score (out of 100)
    total_score = db.Column(db.Float, nullable=False)  # 0-100
    
    # Component scores (for TR interviews)
    introduction_score = db.Column(db.Float, default=0.0)  # 0-10 converted to percentage
    projects_resume_score = db.Column(db.Float, default=0.0)
    programming_score = db.Column(db.Float, default=0.0)
    jd_gap_skills_score = db.Column(db.Float, default=0.0)
    communication_score = db.Column(db.Float, default=0.0)
    
    # Component scores (for HR interviews)
    hr_introduction_score = db.Column(db.Float, default=0.0)
    hr_communication_score = db.Column(db.Float, default=0.0)
    hr_confidence_score = db.Column(db.Float, default=0.0)
    hr_behavioral_score = db.Column(db.Float, default=0.0)
    
    # Feedback data (JSON)
    strengths = db.Column(db.Text)  # JSON array
    weaknesses = db.Column(db.Text)  # JSON array
    improvements = db.Column(db.Text)  # JSON array
    suggested_resources = db.Column(db.Text)  # JSON array
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'total_score': self.total_score,
            'introduction_score': self.introduction_score,
            'projects_resume_score': self.projects_resume_score,
            'programming_score': self.programming_score,
            'jd_gap_skills_score': self.jd_gap_skills_score,
            'communication_score': self.communication_score,
            'hr_introduction_score': self.hr_introduction_score,
            'hr_communication_score': self.hr_communication_score,
            'hr_confidence_score': self.hr_confidence_score,
            'hr_behavioral_score': self.hr_behavioral_score,
            'strengths': json.loads(self.strengths) if self.strengths else [],
            'weaknesses': json.loads(self.weaknesses) if self.weaknesses else [],
            'improvements': json.loads(self.improvements) if self.improvements else [],
            'suggested_resources': json.loads(self.suggested_resources) if self.suggested_resources else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Resource(db.Model):
    """Learning resources model"""
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20), nullable=False)  # 'pdf', 'code_snippet', 'flashcard', 'notes'
    file_path = db.Column(db.String(255))
    content = db.Column(db.Text)  # For flashcards, code snippets, notes
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    tags = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'file_path': self.file_path,
            'content': self.content,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_public': self.is_public
        }

class Notification(db.Model):
    """Notification model"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20))  # 'feedback', 'quiz_result', 'assignment', 'general'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(255))  # Optional link to related content
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'link': self.link
        }

class Post(db.Model):
    """Post model for company-related posts (interview experiences, tips, etc.)"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)  # Can be null if file is uploaded
    file_path = db.Column(db.String(500))  # Path to uploaded file (PDF, JPG, PNG)
    file_type = db.Column(db.String(20))  # 'pdf', 'jpg', 'png'
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_type = db.Column(db.String(50), default='experience')  # 'experience', 'tip', 'question', 'discussion'
    tags = db.Column(db.String(200))  # Comma-separated tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    company = db.relationship('Company', backref='posts')
    user = db.relationship('User', backref='posts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'company_id': self.company_id,
            'user_id': self.user_id,
            'post_type': self.post_type,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'company_name': self.company.name if self.company else None,
            'user_name': self.user.full_name if self.user else None
        }

class Leaderboard(db.Model):
    """Leaderboard model for tracking rankings"""
    __tablename__ = 'leaderboard'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    total_score = db.Column(db.Float, default=0)
    quiz_score = db.Column(db.Float, default=0)
    coding_score = db.Column(db.Float, default=0)
    accuracy = db.Column(db.Float, default=0)  # Percentage
    total_submissions = db.Column(db.Integer, default=0)
    total_quizzes = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'total_score': self.total_score,
            'quiz_score': self.quiz_score,
            'coding_score': self.coding_score,
            'accuracy': self.accuracy,
            'total_submissions': self.total_submissions,
            'total_quizzes': self.total_quizzes,
            'rank': self.rank,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

