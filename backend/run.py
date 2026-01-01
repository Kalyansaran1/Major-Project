"""
Run script for the Flask application
"""
from app import create_app

if __name__ == '__main__':
    app = create_app('development')
    print("Starting Interview Preparation Platform...")
    print("Backend running on http://localhost:5000")
    print("Open frontend/index.html in your browser or use a local server")
    app.run(debug=True, host='0.0.0.0', port=5000)

