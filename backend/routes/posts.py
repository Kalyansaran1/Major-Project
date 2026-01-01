"""
Posts routes for company-related posts
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Post, Company, User
from utils.auth import role_required
from werkzeug.utils import secure_filename
from config import Config
import os

posts_bp = Blueprint('posts', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf', 'jpg', 'jpeg', 'png']

@posts_bp.route('/posts', methods=['POST'])
@jwt_required()
@role_required(['student', 'faculty', 'admin'])
def create_post():
    """Create a new company post with text content or file upload"""
    try:
        user_id = get_jwt_identity()
        
        # Get form data
        title = request.form.get('title')
        company_name = request.form.get('company_name')
        content_type = request.form.get('content_type', 'text')  # 'text' or 'file'
        content = request.form.get('content', '')
        post_type = request.form.get('post_type', 'experience')
        tags = request.form.get('tags', '')
        
        # Validate required fields
        if not title or not company_name:
            return jsonify({'error': 'Title and company name are required'}), 400
        
        # Find or create company
        company = Company.query.filter_by(name=company_name).first()
        if not company:
            # Create new company if it doesn't exist
            company = Company(
                name=company_name,
                description=f'Company: {company_name}'
            )
            db.session.add(company)
            db.session.flush()  # Get the ID without committing
        
        company_id = company.id
        
        # Handle file upload
        file_path = None
        file_type = None
        
        if content_type == 'file':
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                
                # Ensure upload folder exists
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(Config.UPLOAD_FOLDER, f"post_{user_id}_{filename}")
                file.save(file_path)
                file_path = os.path.abspath(file_path)
                file_type = file_ext
            else:
                return jsonify({'error': 'Invalid file type. Only PDF, JPG, PNG are allowed'}), 400
        else:
            # Text content
            if not content:
                return jsonify({'error': 'Content is required'}), 400
        
        post = Post(
            title=title,
            content=content if content_type == 'text' else None,
            file_path=file_path,
            file_type=file_type,
            company_id=int(company_id),
            user_id=user_id,
            post_type=post_type,
            tags=tags
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@posts_bp.route('/posts', methods=['GET'])
@jwt_required()
def list_posts():
    """List all posts, optionally filtered by company"""
    try:
        company_id = request.args.get('company_id', type=int)
        post_type = request.args.get('post_type')
        limit = request.args.get('limit', type=int, default=50)
        
        query = Post.query.filter_by(is_active=True)
        
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        if post_type:
            query = query.filter_by(post_type=post_type)
        
        posts = query.order_by(Post.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'posts': [post.to_dict() for post in posts]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    """Get a specific post"""
    try:
        post = Post.query.get_or_404(post_id)
        
        if not post.is_active:
            return jsonify({'error': 'Post not found'}), 404
        
        return jsonify({
            'post': post.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/posts/<int:post_id>/file', methods=['GET'])
@jwt_required()
def get_post_file(post_id):
    """Download a post's attached file"""
    try:
        from flask import send_file
        post = Post.query.get_or_404(post_id)
        
        if not post.is_active or not post.file_path:
            return jsonify({'error': 'File not found'}), 404
        
        if not os.path.exists(post.file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        return send_file(post.file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
@role_required(['faculty', 'admin'])
def delete_post(post_id):
    """Delete a post (soft delete)"""
    try:
        user_id = get_jwt_identity()
        post = Post.query.get_or_404(post_id)
        
        # Check if user created the post or is admin
        user = User.query.get(user_id)
        if post.user_id != user_id and user.role != 'admin':
            return jsonify({'error': 'You do not have permission to delete this post'}), 403
        
        # Soft delete
        post.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Post deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

