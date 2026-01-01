// ================= API Configuration =================

// Get API URL from index.html script tag, or fallback to Railway backend
const getApiBaseUrl = () => {
    // Check for config script tag in index.html (set in index.html)
    const configScript = document.getElementById('api-config');
    if (configScript && configScript.dataset.apiUrl) {
        return configScript.dataset.apiUrl;
    }
    // Fallback: Use Railway backend URL
    return "https://major-project-production-8ebb.up.railway.app/api";
};

const API_BASE_URL = getApiBaseUrl();

// ================= Auth State =================

let authToken = localStorage.getItem('authToken') || '';
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

// ================= API Helper =================

async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    if (authToken) {
        config.headers['Authorization'] = `Bearer ${authToken}`;
    }

    try {
        const response = await fetch(url, config);
        
        // Check if response is JSON
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            throw new Error(text || `HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.ok) {
            throw new Error(data.error || data.message || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        // Provide better error messages
        if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
            throw new Error('Cannot connect to server. Please check if the backend is running.');
        }
        throw error;
    }
}

// ================= Auth API =================

const authAPI = {
    login: async (username, password) => {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));

        return data;
    },

    register: async (username, email, password, full_name, role) => {
        const data = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password, full_name, role })
        });

        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));

        return data;
    },

    logout: () => {
        authToken = '';
        currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
    },

    getCurrentUser: async () => {
        return await apiRequest('/auth/me');
    }
};

// ================= Student API =================

const studentAPI = {
    getDashboard: async () => apiRequest('/student/dashboard'),
    
    getPerformance: async () => apiRequest('/student/performance'),

    getQuestions: async (filters = {}) => {
        const params = new URLSearchParams(filters);
        return apiRequest(`/student/questions?${params}`);
    },

    getResources: async (filters = {}) => {
        const params = new URLSearchParams(filters);
        return apiRequest(`/student/resources?${params}`);
    },

    getPlacementReadiness: async (userId = null) => {
        const url = userId ? `/student/placement-readiness?user_id=${userId}` : '/student/placement-readiness';
        return apiRequest(url);
    }
};

// ================= Coding API =================

const codingAPI = {
    getQuestion: async (questionId) =>
        apiRequest(`/coding/questions/${questionId}`),

    executeCode: async (code, language, stdin = '', questionId = null) => {
        const body = { code, language, stdin };
        if (questionId) {
            body.question_id = questionId;
        }
        return apiRequest('/coding/execute', {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    submitCode: async (questionId, code, language) =>
        apiRequest('/coding/submit', {
            method: 'POST',
            body: JSON.stringify({ question_id: questionId, code, language })
        }),

    getSubmissions: async (questionId = null) => {
        const params = questionId ? `?question_id=${questionId}` : '';
        return apiRequest(`/coding/submissions${params}`);
    },

    getLastSubmission: async (questionId, language = null) => {
        const params = new URLSearchParams({ question_id: questionId });
        if (language) {
            params.append('language', language);
        }
        return apiRequest(`/coding/submissions/last?${params}`);
    }
};

// ================= Quiz API =================

const quizAPI = {
    listQuizzes: async (filters = {}) => {
        const params = new URLSearchParams(filters);
        return apiRequest(`/quiz/list?${params}`);
    },

    getQuiz: async (quizId) => apiRequest(`/quiz/${quizId}`),

    attemptQuiz: async (quizId, answers) =>
        apiRequest(`/quiz/${quizId}/attempt`, {
            method: 'POST',
            body: JSON.stringify({ answers })
        }),

    getAttempts: async (quizId = null) => {
        const params = quizId ? `?quiz_id=${quizId}` : '';
        return apiRequest(`/quiz/attempts${params}`);
    }
};

// ================= Company API =================

const companyAPI = {
    listCompanies: async () => apiRequest('/admin/companies'),
    
    deleteCompany: async (companyId) => {
        return apiRequest(`/admin/companies/${companyId}`, {
            method: 'DELETE'
        });
    }
};

// ================= Resources API =================

const resourcesAPI = {
    uploadResource: async (formData) => {
        const url = `${API_BASE_URL}/resources/upload`;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to upload resource');
        }

        return await response.json();
    },

    getResources: async (filters = {}) => {
        const params = new URLSearchParams(filters);
        return apiRequest(`/student/resources?${params}`);
    },

    deleteResource: async (resourceId) =>
        apiRequest(`/resources/${resourceId}`, { method: 'DELETE' })
};

// ================= Leaderboard API =================

const leaderboardAPI = {
    getTopUsers: async (limit = 100) =>
        apiRequest(`/leaderboard/top?limit=${limit}`),

    getMyRank: async () => apiRequest('/leaderboard/my-rank')
};

// ================= Notifications API =================

const notificationsAPI = {
    getNotifications: async (isRead = null) => {
        const params = isRead !== null ? `?is_read=${isRead}` : '';
        return apiRequest(`/notifications${params}`);
    },

    markAsRead: async (notificationId) =>
        apiRequest(`/notifications/${notificationId}/read`, { method: 'PUT' }),

    markAllAsRead: async () =>
        apiRequest('/notifications/read-all', { method: 'PUT' }),

    getUnreadCount: async () =>
        apiRequest('/notifications/unread-count')
};

// ================= Interview API =================

const interviewAPI = {
    selectInterviewType: async (interviewType) => {
        return apiRequest('/interview/select-interview-type', {
            method: 'POST',
            body: JSON.stringify({ interview_type: interviewType })
        });
    },

    uploadResume: async (file) => {
        const url = `${API_BASE_URL}/interview/upload-resume`;
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to upload resume');
        }
        
        return await response.json();
    },

    uploadJD: async (file, resumeSkills = null) => {
        const url = `${API_BASE_URL}/interview/upload-jd`;
        const formData = new FormData();
        formData.append('file', file);
        if (resumeSkills) {
            formData.append('resume_skills', JSON.stringify(resumeSkills));
        }
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to upload job description');
        }
        
        return await response.json();
    },

    startInterview: async (data) => {
        return apiRequest('/interview/start-interview', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    submitAnswer: async (sessionId, answer, timeTakenSeconds = 0) => {
        return apiRequest('/interview/submit-answer', {
            method: 'POST',
            body: JSON.stringify({ 
                session_id: sessionId, 
                answer: answer,
                time_taken_seconds: timeTakenSeconds
            })
        });
    },

    endInterview: async (sessionId) => {
        return apiRequest(`/interview/end-interview/${sessionId}`, {
            method: 'POST'
        });
    },

    getInterviewResult: async (sessionId) => {
        return apiRequest(`/interview/interview-result/${sessionId}`);
    },

    getSession: async (sessionId) => {
        return apiRequest(`/interview/session/${sessionId}`);
    },

    getPracticeRecommendations: async (sessionId) => {
        return apiRequest(`/interview/practice-recommendations/${sessionId}`);
    }
};

// ================= Chatbot API (Legacy) =================

const chatbotAPI = {
    startInterview: async (resumeText, jobDescription, interviewType = 'technical', experienceLevel = 'fresher', totalQuestions = 5) => {
        return apiRequest('/chatbot/start-interview', {
            method: 'POST',
            body: JSON.stringify({ 
                resume_text: resumeText, 
                job_description: jobDescription,
                interview_type: interviewType,
                experience_level: experienceLevel,
                total_questions: totalQuestions
            })
        });
    },

    submitAnswer: async (sessionId, answer) =>
        apiRequest('/chatbot/answer', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId, answer })
        }),

    getSession: async (sessionId) =>
        apiRequest(`/chatbot/session/${sessionId}`),

    endInterview: async (sessionId) =>
        apiRequest(`/chatbot/end-interview/${sessionId}`, { method: 'POST' }),

    extractText: async (file) => {
        const url = `${API_BASE_URL}/chatbot/extract-text`;
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to extract text');
        }
        
        return await response.json();
    }
};

// ================= Faculty API =================

const facultyAPI = {
    getDashboard: async () => apiRequest('/faculty/dashboard'),
    
    getStudentPerformance: async (studentId = null) => {
        const url = studentId ? `/faculty/students/performance?student_id=${studentId}` : '/faculty/students/performance';
        return apiRequest(url);
    },

    getBatchWeakAreas: async () => apiRequest('/faculty/batch/weak-areas'),

    createQuestion: async (question) => {
        return apiRequest('/faculty/questions', {
            method: 'POST',
            body: JSON.stringify(question)
        });
    },

    createQuiz: async (quiz) => {
        return apiRequest('/faculty/quizzes', {
            method: 'POST',
            body: JSON.stringify(quiz)
        });
    },

    deleteQuiz: async (quizId) => {
        return apiRequest(`/faculty/quizzes/${quizId}`, {
            method: 'DELETE'
        });
    },

    deleteQuestion: async (questionId) => {
        return apiRequest(`/faculty/questions/${questionId}`, {
            method: 'DELETE'
        });
    }
};

// ================= Admin API =================

const adminAPI = {
    getDashboard: async () => apiRequest('/admin/dashboard'),
    
    getUsers: async (role = null, isActive = null) => {
        const params = new URLSearchParams();
        if (role) params.append('role', role);
        if (isActive !== null) params.append('is_active', isActive);
        const url = params.toString() ? `/admin/users?${params}` : '/admin/users';
        return apiRequest(url);
    },

    updateUser: async (userId, data) => {
        return apiRequest(`/admin/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    deleteUser: async (userId) => {
        return apiRequest(`/admin/users/${userId}`, {
            method: 'DELETE'
        });
    }
};

// ================= Posts API =================

const postsAPI = {
    createPost: async (formData) => {
        const url = `${API_BASE_URL}/posts`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create post');
        }
        
        return await response.json();
    },

    getPosts: async (companyId = null) => {
        const url = companyId ? `/posts?company_id=${companyId}` : '/posts';
        return apiRequest(url);
    },

    getPost: async (postId) => apiRequest(`/posts/${postId}`),

    deletePost: async (postId) => {
        return apiRequest(`/posts/${postId}`, {
            method: 'DELETE'
        });
    }
};
