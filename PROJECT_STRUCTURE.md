# Project Structure Documentation

## Overview
This document describes the complete structure of the Interview Preparation Platform project.

## Directory Structure

```
Demo.D/
│
├── backend/                    # Flask Backend Application
│   ├── app.py                 # Main Flask application entry point
│   ├── config.py              # Configuration settings
│   ├── models.py              # Database models (SQLAlchemy)
│   ├── seed_data.py           # Initial database seeding
│   ├── run.py                 # Alternative run script
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment variables template
│   │
│   ├── routes/                # API Route Handlers
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── student.py        # Student-specific endpoints
│   │   ├── faculty.py        # Faculty endpoints
│   │   ├── admin.py          # Admin endpoints
│   │   ├── coding.py         # Coding practice endpoints
│   │   ├── quiz.py           # Quiz endpoints
│   │   ├── resources.py      # Learning resources endpoints
│   │   ├── leaderboard.py    # Leaderboard endpoints
│   │   ├── notifications.py  # Notification endpoints
│   │   └── chatbot.py        # AI chatbot endpoints
│   │
│   ├── utils/                 # Utility Functions
│   │   ├── auth.py           # Authentication utilities
│   │   ├── compiler.py       # Code execution utilities
│   │   ├── leaderboard.py    # Leaderboard calculations
│   │   └── chatbot.py        # AI chatbot utilities
│   │
│   └── uploads/               # File uploads directory (created at runtime)
│
├── frontend/                   # Frontend Application
│   ├── index.html            # Main HTML file (Single Page Application)
│   │
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   │
│   └── js/
│       ├── api.js            # API client functions
│       └── app.js            # Main application logic
│
├── README.md                   # Main project documentation
├── SETUP.md                   # Quick setup guide
├── PROJECT_STRUCTURE.md       # This file
└── .gitignore                 # Git ignore rules

```

## Backend Architecture

### Models (Database Schema)

1. **User** - Stores user information (students, faculty, admins)
2. **Company** - Company information for company-wise questions
3. **Question** - Coding, MCQ, and fill-in-the-blank questions
4. **CodeSubmission** - Student code submissions and results
5. **Quiz** - Quiz/assessment definitions
6. **QuizQuestion** - Many-to-many relationship between Quiz and Question
7. **QuizAttempt** - Student quiz attempts and scores
8. **Resource** - Learning resources (PDFs, flashcards, etc.)
9. **Notification** - User notifications
10. **Leaderboard** - User rankings and scores

### API Routes Structure

All routes are prefixed with `/api`:

- **Authentication** (`/api/auth`)
  - POST `/register` - User registration
  - POST `/login` - User login
  - POST `/refresh` - Refresh JWT token
  - GET `/me` - Get current user info
  - POST `/logout` - Logout

- **Student** (`/api/student`)
  - GET `/dashboard` - Dashboard data
  - GET `/performance` - Performance analytics
  - GET `/questions` - Get questions with filters
  - GET `/resources` - Get learning resources

- **Coding** (`/api/coding`)
  - GET `/questions/<id>` - Get question details
  - POST `/execute` - Execute code
  - POST `/submit` - Submit code for evaluation
  - GET `/submissions` - Get user submissions

- **Quiz** (`/api/quiz`)
  - GET `/list` - List available quizzes
  - GET `/<id>` - Get quiz details
  - POST `/<id>/attempt` - Submit quiz attempt
  - GET `/attempts` - Get user attempts

- **Faculty** (`/api/faculty`)
  - GET `/dashboard` - Faculty dashboard
  - POST `/quizzes` - Create quiz
  - POST `/questions` - Create question
  - GET `/students/performance` - Student performance
  - POST `/feedback` - Provide feedback

- **Admin** (`/api/admin`)
  - GET `/dashboard` - Admin dashboard
  - GET `/users` - List users
  - PUT `/users/<id>` - Update user
  - DELETE `/users/<id>` - Delete user
  - POST `/companies` - Create company
  - GET `/companies` - List companies
  - POST `/questions/<id>/approve` - Approve question
  - POST `/questions/<id>/reject` - Reject question

- **Resources** (`/api/resources`)
  - POST `/upload` - Upload resource
  - GET `/<id>` - Get resource
  - DELETE `/<id>` - Delete resource

- **Leaderboard** (`/api/leaderboard`)
  - GET `/top` - Get top users
  - GET `/my-rank` - Get user rank

- **Notifications** (`/api/notifications`)
  - GET `/` - Get notifications
  - PUT `/<id>/read` - Mark as read
  - PUT `/read-all` - Mark all as read
  - GET `/unread-count` - Get unread count

- **Chatbot** (`/api/chatbot`)
  - POST `/start-interview` - Start interview session
  - POST `/answer` - Submit answer
  - GET `/session/<id>` - Get session details
  - POST `/end-interview/<id>` - End interview

## Frontend Architecture

### Single Page Application (SPA)

The frontend is a single-page application built with vanilla JavaScript:

1. **index.html** - Contains all page templates
2. **api.js** - API client with all API functions
3. **app.js** - Main application logic and page navigation

### Page Sections

- Authentication Page (Login/Register)
- Dashboard
- Coding Practice
- Quizzes
- Companies
- Resources
- Leaderboard
- AI Chatbot Interview

### State Management

- Authentication token stored in localStorage
- Current user info stored in localStorage
- Page state managed in JavaScript variables
- API calls handled through centralized API client

## Database Schema

### Relationships

- User → CodeSubmission (One-to-Many)
- User → QuizAttempt (One-to-Many)
- User → Resource (One-to-Many)
- User → Notification (One-to-Many)
- Company → Question (One-to-Many)
- Company → Resource (One-to-Many)
- Question → CodeSubmission (One-to-Many)
- Quiz → QuizQuestion (One-to-Many)
- Quiz → QuizAttempt (One-to-Many)
- Question → QuizQuestion (One-to-Many)
- User → Leaderboard (One-to-One)

## Security Features

1. **JWT Authentication** - Token-based authentication
2. **Password Hashing** - Bcrypt for password security
3. **Role-Based Access Control** - Different permissions for different roles
4. **CORS Configuration** - Cross-origin resource sharing setup
5. **Input Validation** - Server-side validation
6. **SQL Injection Prevention** - SQLAlchemy ORM protection

## Key Features Implementation

### Live Coding
- Code editor with syntax highlighting (via textarea)
- Language selection (C, C++, Python, Java)
- Code execution via compiler API or local execution
- Test case evaluation
- Real-time output display

### Quiz System
- MCQ questions with multiple options
- Fill-in-the-blank questions
- Auto-evaluation
- Score calculation
- Time tracking

### Performance Analytics
- Submission tracking
- Accuracy calculation
- Language-wise statistics
- Difficulty-wise statistics
- Quiz performance metrics

### Leaderboard
- Score calculation based on:
  - Coding submissions
  - Quiz scores
  - Accuracy percentage
- Ranking system
- Real-time updates

### AI Chatbot
- Interview session management
- Question generation based on resume/JD
- Answer evaluation
- Feedback provision
- Conversation history

## Development Workflow

1. **Backend Development**
   - Modify models in `models.py`
   - Add routes in `routes/` directory
   - Add utilities in `utils/` directory
   - Test with API client or Postman

2. **Frontend Development**
   - Modify HTML in `index.html`
   - Update styles in `css/style.css`
   - Add functionality in `js/app.js`
   - Add API calls in `js/api.js`

3. **Database Changes**
   - Modify models in `models.py`
   - Delete `interview_platform.db` to reset
   - Restart server to recreate database

## Deployment Considerations

1. **Environment Variables**
   - Set production SECRET_KEY
   - Configure database URL
   - Set compiler API credentials
   - Set AI API credentials

2. **Database Migration**
   - Migrate from SQLite to PostgreSQL
   - Set up database backups

3. **File Storage**
   - Use cloud storage for uploads
   - Configure CDN for static files

4. **Security**
   - Enable HTTPS
   - Set up rate limiting
   - Configure CORS properly
   - Regular security updates

5. **Performance**
   - Add caching layer
   - Optimize database queries
   - Use production WSGI server (Gunicorn)
   - Set up load balancing if needed

## Testing Strategy

1. **Manual Testing**
   - Test all user flows
   - Test different user roles
   - Test error scenarios

2. **API Testing**
   - Use Postman or similar tool
   - Test all endpoints
   - Verify authentication
   - Check error handling

3. **Frontend Testing**
   - Test in multiple browsers
   - Test responsive design
   - Verify API integration

## Future Enhancements

1. Unit tests and integration tests
2. Real-time notifications (WebSockets)
3. Advanced code editor (Monaco Editor)
4. Video interview support
5. Mobile app version
6. Advanced analytics dashboard
7. Social features (discussions, forums)
8. Certificate generation
9. Payment integration for premium features
10. Multi-language support

