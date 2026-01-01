"""
Leaderboard calculation utilities
"""
from models import Leaderboard, User, CodeSubmission, QuizAttempt, db
from sqlalchemy import func

def update_leaderboard(user_id):
    """Update leaderboard entry for a user"""
    user = User.query.get(user_id)
    if not user or user.role != 'student':
        return
    
    # Calculate coding score
    coding_submissions = CodeSubmission.query.filter_by(user_id=user_id).all()
    coding_score = 0
    total_submissions = len(coding_submissions)
    correct_submissions = 0
    
    for submission in coding_submissions:
        if submission.status == 'accepted':
            correct_submissions += 1
            # Score based on difficulty and efficiency
            question = submission.question
            base_score = 10 if question.difficulty == 'easy' else (20 if question.difficulty == 'medium' else 30)
            efficiency_bonus = max(0, 10 - submission.execution_time) if submission.execution_time else 0
            coding_score += base_score + efficiency_bonus
    
    # Calculate quiz score
    quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
    quiz_score = sum(attempt.score for attempt in quiz_attempts)
    total_quizzes = len(quiz_attempts)
    
    # Calculate accuracy
    accuracy = (correct_submissions / total_submissions * 100) if total_submissions > 0 else 0
    
    # Total score
    total_score = coding_score + quiz_score
    
    # Update or create leaderboard entry
    leaderboard_entry = Leaderboard.query.filter_by(user_id=user_id).first()
    if not leaderboard_entry:
        leaderboard_entry = Leaderboard(user_id=user_id)
        db.session.add(leaderboard_entry)
    
    leaderboard_entry.total_score = total_score
    leaderboard_entry.coding_score = coding_score
    leaderboard_entry.quiz_score = quiz_score
    leaderboard_entry.accuracy = accuracy
    leaderboard_entry.total_submissions = total_submissions
    leaderboard_entry.total_quizzes = total_quizzes
    
    db.session.commit()
    
    # Update ranks
    update_ranks()

def update_ranks():
    """Update ranks for all users"""
    leaderboard_entries = Leaderboard.query.order_by(
        Leaderboard.total_score.desc(),
        Leaderboard.accuracy.desc()
    ).all()
    
    for rank, entry in enumerate(leaderboard_entries, start=1):
        entry.rank = rank
    
    db.session.commit()

def get_leaderboard(limit=100):
    """Get top users from leaderboard"""
    entries = Leaderboard.query.order_by(
        Leaderboard.rank.asc()
    ).limit(limit).all()
    
    return [entry.to_dict() for entry in entries]

