# Quick Setup Guide

## Prerequisites
- Python 3.8+
- Modern web browser

## Step-by-Step Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
# OR
python run.py
```

The backend will start on `http://localhost:5000`

### 2. Frontend Setup

**Option 1: Direct File Access**
- Simply open `frontend/index.html` in your web browser

**Option 2: Local Server (Recommended)**
```bash
# Navigate to frontend directory
cd frontend

# Using Python
python -m http.server 8000

# Then open http://localhost:8000 in browser
```

### 3. First Login

Use these default credentials:

**Admin:**
- Username: `admin`
- Password: `admin123`

**Faculty:**
- Username: `faculty1`
- Password: `faculty123`

**Student:**
- Username: `student1`
- Password: `student123`

## Troubleshooting

### Backend Issues

1. **Port already in use**
   - Change port in `app.py`: `app.run(port=5001)`

2. **Module not found**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt` again

3. **Database errors**
   - Delete `interview_platform.db` and restart the server
   - Database will be recreated automatically

### Frontend Issues

1. **CORS errors**
   - Ensure backend is running on port 5000
   - Check `API_BASE_URL` in `frontend/js/api.js`

2. **API not connecting**
   - Verify backend is running: `http://localhost:5000/api/auth/me`
   - Check browser console for errors

## Testing the Application

1. **Login** with student account
2. **Navigate to Coding Practice** - select a question and try coding
3. **Take a Quiz** - attempt MCQ questions
4. **View Leaderboard** - check rankings
5. **Try AI Interview** - start a virtual interview session

## Production Deployment

For production:
1. Set strong `SECRET_KEY` and `JWT_SECRET_KEY` in environment variables
2. Use PostgreSQL instead of SQLite
3. Configure proper compiler API credentials
4. Set up OpenAI API key for chatbot
5. Use HTTPS
6. Set up proper file storage (AWS S3, etc.)

## Support

For issues or questions, check:
- README.md for detailed documentation
- Code comments for implementation details
- API endpoints documentation in README.md

