"""
Leaderboard routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.leaderboard import get_leaderboard, update_leaderboard
from models import Leaderboard

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/top', methods=['GET'])
@jwt_required()
def get_top_users():
    """Get top users from leaderboard"""
    try:
        limit = int(request.args.get('limit', 100))
        
        leaderboard = get_leaderboard(limit)
        
        return jsonify({
            'leaderboard': leaderboard
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leaderboard_bp.route('/my-rank', methods=['GET'])
@jwt_required()
def get_my_rank():
    """Get current user's rank"""
    try:
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        
        entry = Leaderboard.query.filter_by(user_id=user_id).first()
        
        if not entry:
            return jsonify({
                'rank': None,
                'message': 'No ranking data available'
            }), 200
        
        return jsonify({
            'rank': entry.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

