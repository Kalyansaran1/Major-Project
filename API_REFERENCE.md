# API Reference Guide

Complete API endpoint documentation for the Interview Preparation Platform.

**Base URL:** `http://localhost:5000/api`

**Authentication:** Most endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

---

## Authentication Endpoints

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string (optional)",
  "role": "student|faculty|admin"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}

Response: {
  "access_token": "string",
  "refresh_token": "string",
  "user": {...}
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

### Refresh Token
```http
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

---

## Student Endpoints

### Get Dashboard
```http
GET /student/dashboard
Authorization: Bearer <token>
```

### Get Performance Analytics
```http
GET /student/performance
Authorization: Bearer <token>
```

### Get Questions
```http
GET /student/questions?type=coding&difficulty=easy&company_id=1&page=1&per_page=20
Authorization: Bearer <token>
```

### Get Resources
```http
GET /student/resources?type=pdf&company_id=1
Authorization: Bearer <token>
```

---

## Coding Practice Endpoints

### Get Question Details
```http
GET /coding/questions/<question_id>
Authorization: Bearer <token>
```

### Execute Code
```http
POST /coding/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "print('Hello World')",
  "language": "python",
  "stdin": ""
}
```

### Submit Code
```http
POST /coding/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "question_id": 1,
  "code": "def solution(): ...",
  "language": "python"
}
```

### Get Submissions
```http
GET /coding/submissions?question_id=1
Authorization: Bearer <token>
```

---

## Quiz Endpoints

### List Quizzes
```http
GET /quiz/list?is_active=true&company_id=1
Authorization: Bearer <token>
```

### Get Quiz Details
```http
GET /quiz/<quiz_id>
Authorization: Bearer <token>
```

### Attempt Quiz
```http
POST /quiz/<quiz_id>/attempt
Authorization: Bearer <token>
Content-Type: application/json

{
  "answers": {
    "1": "A",  // For MCQ
    "2": {     // For fill-in-the-blank
      "1": "answer1",
      "2": "answer2"
    }
  }
}
```

### Get Quiz Attempts
```http
GET /quiz/attempts?quiz_id=1
Authorization: Bearer <token>
```

---

## Faculty Endpoints

### Get Dashboard
```http
GET /faculty/dashboard
Authorization: Bearer <token>
```

### Create Quiz
```http
POST /faculty/quizzes
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Quiz Title",
  "description": "Description",
  "company_id": 1,
  "duration_minutes": 60,
  "total_marks": 100,
  "question_ids": [1, 2, 3],
  "marks_per_question": 10,
  "start_time": "2024-01-01T00:00:00",
  "end_time": "2024-01-02T00:00:00"
}
```

### Create Question
```http
POST /faculty/questions
Authorization: Bearer <token>
Content-Type: application/json

// For Coding Question
{
  "title": "Two Sum",
  "description": "Find two numbers...",
  "type": "coding",
  "difficulty": "easy",
  "company_id": 1,
  "tags": ["array", "hashmap"],
  "test_cases": [
    {"input": "[2,7,11,15]\n9", "output": "[0,1]"}
  ],
  "starter_code": "def twoSum(nums, target):\n    pass",
  "solution": "def twoSum(nums, target):\n    ..."
}

// For MCQ Question
{
  "title": "What is time complexity?",
  "description": "Select the correct answer",
  "type": "mcq",
  "difficulty": "easy",
  "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
  "correct_answer": "B"
}

// For Fill-in-the-Blank
{
  "title": "Python Data Types",
  "description": "Fill in the blanks",
  "type": "fill_blank",
  "difficulty": "easy",
  "blanks": [
    {"id": 1, "text": "Lists are", "answer": "mutable"},
    {"id": 2, "text": "Tuples are", "answer": "immutable"}
  ]
}
```

### Get Student Performance
```http
GET /faculty/students/performance?student_id=1
Authorization: Bearer <token>
```

### Provide Feedback
```http
POST /faculty/feedback
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": 1,
  "title": "Feedback Title",
  "message": "Feedback message",
  "link": "/quiz/1/result/1"
}
```

---

## Admin Endpoints

### Get Dashboard
```http
GET /admin/dashboard
Authorization: Bearer <token>
```

### List Users
```http
GET /admin/users?role=student&is_active=true
Authorization: Bearer <token>
```

### Update User
```http
PUT /admin/users/<user_id>
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_active": true,
  "role": "student",
  "full_name": "New Name"
}
```

### Delete User
```http
DELETE /admin/users/<user_id>
Authorization: Bearer <token>
```

### Create Company
```http
POST /admin/companies
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Google",
  "description": "Tech company",
  "logo_url": "https://..."
}
```

### List Companies
```http
GET /admin/companies
Authorization: Bearer <token>
```

### Approve Question
```http
POST /admin/questions/<question_id>/approve
Authorization: Bearer <token>
```

### Reject Question
```http
POST /admin/questions/<question_id>/reject
Authorization: Bearer <token>
```

---

## Resources Endpoints

### Upload Resource
```http
POST /resources/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

title: string
description: string
type: pdf|code_snippet|flashcard|notes
company_id: integer (optional)
tags: string (comma-separated)
is_public: boolean
file: file (optional)
content: string (for code_snippet, flashcard, notes)
```

### Get Resource
```http
GET /resources/<resource_id>
Authorization: Bearer <token>
```

### Delete Resource
```http
DELETE /resources/<resource_id>
Authorization: Bearer <token>
```

---

## Leaderboard Endpoints

### Get Top Users
```http
GET /leaderboard/top?limit=100
Authorization: Bearer <token>
```

### Get My Rank
```http
GET /leaderboard/my-rank
Authorization: Bearer <token>
```

---

## Notification Endpoints

### Get Notifications
```http
GET /notifications?is_read=false
Authorization: Bearer <token>
```

### Mark as Read
```http
PUT /notifications/<notification_id>/read
Authorization: Bearer <token>
```

### Mark All as Read
```http
PUT /notifications/read-all
Authorization: Bearer <token>
```

### Get Unread Count
```http
GET /notifications/unread-count
Authorization: Bearer <token>
```

---

## Chatbot Endpoints

### Start Interview
```http
POST /chatbot/start-interview
Authorization: Bearer <token>
Content-Type: application/json

{
  "resume_text": "Resume content...",
  "job_description": "Job description..."
}

Response: {
  "session_id": "string",
  "question": "string",
  "question_type": "technical|hr|behavioral"
}
```

### Submit Answer
```http
POST /chatbot/answer
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "string",
  "answer": "My answer..."
}

Response: {
  "feedback": "Feedback text",
  "next_question": "Next question",
  "question_type": "technical|hr|behavioral",
  "conversation": [...]
}
```

### Get Session
```http
GET /chatbot/session/<session_id>
Authorization: Bearer <token>
```

### End Interview
```http
POST /chatbot/end-interview/<session_id>
Authorization: Bearer <token>
```

---

## Error Responses

All endpoints may return these error responses:

```json
{
  "error": "Error message"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## Response Formats

### Success Response
```json
{
  "message": "Success message",
  "data": {...}
}
```

### List Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

### Error Response
```json
{
  "error": "Error message"
}
```

---

## Testing with cURL

### Login Example
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"student123"}'
```

### Get Dashboard Example
```bash
curl -X GET http://localhost:5000/api/student/dashboard \
  -H "Authorization: Bearer <your_token>"
```

### Submit Code Example
```bash
curl -X POST http://localhost:5000/api/coding/submit \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": 1,
    "code": "def solution(): return True",
    "language": "python"
  }'
```

---

## Postman Collection

You can import these endpoints into Postman:
1. Create a new collection
2. Set base URL: `http://localhost:5000/api`
3. Add environment variable: `token` for JWT token
4. Use Pre-request Script to add token to headers:
```javascript
pm.request.headers.add({
    key: 'Authorization',
    value: 'Bearer ' + pm.environment.get('token')
});
```

