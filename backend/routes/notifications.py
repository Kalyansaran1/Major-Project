"""
Notification routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Notification, db

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user notifications"""
    try:
        user_id = get_jwt_identity()
        is_read = request.args.get('is_read')
        
        query = Notification.query.filter_by(user_id=user_id)
        
        if is_read is not None:
            query = query.filter_by(is_read=is_read.lower() == 'true')
        
        notifications = query.order_by(Notification.created_at.desc()).all()
        
        return jsonify({
            'notifications': [n.to_dict() for n in notifications]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark notification as read"""
    try:
        user_id = get_jwt_identity()
        notification = Notification.query.get_or_404(notification_id)
        
        if notification.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'message': 'Notification marked as read',
            'notification': notification.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read"""
    try:
        user_id = get_jwt_identity()
        
        # Get count before update for response
        unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        
        # Update all unread notifications
        updated = Notification.query.filter_by(user_id=user_id, is_read=False)\
            .update({'is_read': True}, synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'message': 'All notifications marked as read',
            'updated_count': updated
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def unread_count():
    """Get count of unread notifications"""
    try:
        user_id = get_jwt_identity()
        
        count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        
        return jsonify({
            'count': count
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

