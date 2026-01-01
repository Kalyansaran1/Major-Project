"""
Configuration settings for the Interview Preparation Platform
"""
import os
from datetime import timedelta

def _get_database_url():
    """Get database URL with proper formatting and fallback"""
    # Check if we're in build phase (Railway sets this)
    is_build_phase = os.environ.get('RAILWAY_ENVIRONMENT') == 'build' or \
                    os.environ.get('NIXPACKS_BUILD') == '1'
    
    # Only try to get DATABASE_URL if not in build phase
    if not is_build_phase:
        database_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
        if database_url and not database_url.startswith('mysql+pymysql://'):
            # Convert mysql:// to mysql+pymysql:// if needed
            database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
        if database_url:
            return database_url
    
    # Fallback for build phase or when DATABASE_URL is not set
    return 'mysql+pymysql://root:2004@localhost:3306/cursor_platform'

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Get DATABASE_URL - Railway provides this during build/deploy
    # Try DATABASE_URL first, then MYSQL_URL, then fallback to local
    # During Railway build, DATABASE_URL might not be available, so use fallback
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # Verify connections before using
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 10,
            'charset': 'utf8mb4'
        }
    }
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
    
    # Compiler API settings (using online compiler API)
    COMPILER_API_URL = 'https://api.jdoodle.com/v1/execute'
    COMPILER_CLIENT_ID = os.environ.get('COMPILER_CLIENT_ID') or ''
    COMPILER_CLIENT_SECRET = os.environ.get('COMPILER_CLIENT_SECRET') or ''
    
    # AI Chatbot settings (using OpenAI or similar)
    AI_API_KEY = os.environ.get('AI_API_KEY') or ''
    AI_API_URL = os.environ.get('AI_API_URL') or 'https://api.openai.com/v1/chat/completions'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
