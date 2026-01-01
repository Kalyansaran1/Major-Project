"""
Main Flask application entry point
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from dotenv import load_dotenv
import os
import pymysql
import sys

# Load environment variables from .env file
load_dotenv()

# Register PyMySQL as MySQLdb for SQLAlchemy compatibility
pymysql.install_as_MySQLdb()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }}, supports_credentials=True)
    jwt = JWTManager(app)
    
    # Handle OPTIONS requests for CORS preflight (before JWT validation)
    # This must run before JWT validation to prevent redirects on preflight requests
    @app.before_request
    def handle_preflight():
        from flask import request, jsonify
        if request.method == "OPTIONS":
            response = jsonify({})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
            response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            response.headers.add("Access-Control-Max-Age", "3600")
            return response
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.faculty import faculty_bp
    from routes.admin import admin_bp
    from routes.quiz import quiz_bp
    from routes.coding import coding_bp
    from routes.resources import resources_bp
    from routes.leaderboard import leaderboard_bp
    from routes.notifications import notifications_bp
    from routes.chatbot import chatbot_bp
    from routes.posts import posts_bp
    from routes.interview import interview_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
    app.register_blueprint(coding_bp, url_prefix='/api/coding')
    app.register_blueprint(posts_bp, url_prefix='/api')
    app.register_blueprint(resources_bp, url_prefix='/api/resources')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(interview_bp, url_prefix='/api/interview')
    
    # Initialize database with error handling
    from models import db
    db.init_app(app)
    
    # Initialize database lazily (don't connect during build)
    # This prevents Railway build failures when DATABASE_URL isn't available
    initialized = False
    
    def initialize_database():
        """Initialize database - called on first request"""
        nonlocal initialized
        if initialized:
            return
        
        with app.app_context():
            try:
                # Test database connection
                with db.engine.connect() as conn:
                    conn.close()
                print("[OK] Database connection established successfully!")
                
                # Create all tables
                db.create_all()
                print("[OK] Database tables created/verified!")
                
                # Seed initial data (only once)
                from seed_data import seed_initial_data
                seed_initial_data()
                print("[OK] Initial data seeded!")
                
                initialized = True
            except Exception as e:
                print(f"\n[ERROR] Database connection error: {str(e)}")
                print("\nPlease ensure:")
                print("1. MySQL server is running")
                print("2. Database exists")
                print("3. Connection credentials are correct")
                print("4. DATABASE_URL environment variable is set\n")
                # Don't fail - will retry on next request
    
    # Initialize on first request
    @app.before_request
    def before_request():
        initialize_database()
    
    return app

# Create app instance for gunicorn/WSGI servers
# This is used when running in production (Railway, Render, etc.)
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

if __name__ == '__main__':
    # Use production config in production, development in dev
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    
    # Get port from environment variable (for Railway/Render) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = env == 'development'
    
    app.run(debug=debug, host='0.0.0.0', port=port)

