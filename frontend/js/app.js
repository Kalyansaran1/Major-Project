// Application State
let currentQuestion = null;
let currentQuiz = null;
// Note: currentSessionId and interview-related variables are now in interview_enhanced.js
// Access them via window.currentSessionId if needed for backward compatibility
let companies = [];
let questions = [];
let codingQuestions = [];
let codingFilter = 'all';
let codingSearch = '';
let cpTopicTags = [];
const cpErrors = {
    question: null,
    testcases: null,
    topics: null,
    title: null
};

// Interview state variables moved to interview_enhanced.js to avoid conflicts
// If you need to access them, use the variables from interview_enhanced.js or window object

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadCompanies();
    setupCodingUI();
});

// Authentication Functions
function checkAuth() {
    if (authToken && currentUser) {
        showMainApp();
        loadDashboard();
        // Load notification badge count (only if logged in)
        if (authToken && currentUser) {
            loadNotificationBadge();
        }
    } else {
        showAuthPage();
    }
}

function showAuthPage() {
    document.getElementById('auth-page').classList.add('active');
    document.getElementById('main-app').classList.remove('active');
}

function showMainApp() {
    document.getElementById('auth-page').classList.remove('active');
    document.getElementById('main-app').classList.add('active');
    const userInfoEl = document.getElementById('user-info');
    if (userInfoEl) {
        userInfoEl.textContent = `Welcome, ${currentUser?.username || 'User'}`;
    }
    // Show dashboard by default after login
    updateActiveNav('Dashboard');
    showOnlyDashboard();
    updateAddButtonVisibility();
}

function updateAddButtonVisibility() {
    if (!currentUser) {
        // Hide buttons if no user
        const addNonTechBtn = document.getElementById('add-nontech-btn');
        const addQuizBtn = document.getElementById('add-quiz-btn');
        if (addNonTechBtn) addNonTechBtn.style.display = 'none';
        if (addQuizBtn) addQuizBtn.style.display = 'none';
        return;
    }
    
    // Show add buttons based on user role
    const addNonTechBtn = document.getElementById('add-nontech-btn');
    const addQuizBtn = document.getElementById('add-quiz-btn');
    
    // Non-technical questions - all users can add
    if (addNonTechBtn) {
        addNonTechBtn.style.display = 'block';
    }
    
    // Quiz - only faculty and admin can add (students can only attempt)
    if (addQuizBtn) {
        if (currentUser && currentUser.role === 'student') {
            addQuizBtn.style.display = 'none';
        } else {
            addQuizBtn.style.display = 'block';
        }
    }
}

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');
    
    try {
        await authAPI.login(username, password);
        showMainApp();
        loadDashboard();
        // Load notification badge count (only if logged in)
        if (authToken && currentUser) {
            loadNotificationBadge();
        }
        // Load notification badge count
        loadNotificationBadge();
        errorDiv.textContent = '';
        errorDiv.style.display = 'none';
    } catch (error) {
        errorDiv.textContent = error.message || 'Login failed';
        errorDiv.style.display = 'block';
    }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const fullName = document.getElementById('reg-fullname').value;
    const role = document.getElementById('reg-role').value;
    const errorDiv = document.getElementById('register-error');
    
    try {
        await authAPI.register(username, email, password, fullName, role);
        showMainApp();
        loadDashboard();
        // Load notification badge count (only if logged in)
        if (authToken && currentUser) {
            loadNotificationBadge();
        }
        errorDiv.textContent = '';
        errorDiv.style.display = 'none';
    } catch (error) {
        errorDiv.textContent = error.message || 'Registration failed';
        errorDiv.style.display = 'block';
    }
}

function logout() {
    authAPI.logout();
    showAuthPage();
}

// Toggle password visibility
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const icon = input.nextElementSibling;
    if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = '🙈';
    } else {
        input.type = 'password';
        icon.textContent = '👁️';
    }
}

// Toggle between login and register forms
function toggleAuthForm() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const switchText = document.getElementById('auth-switch-text');
    const switchLink = document.getElementById('auth-switch-link');
    const authTitle = document.querySelector('.auth-title');
    
    if (loginForm.classList.contains('active')) {
        // Switch to register
        loginForm.classList.remove('active');
        registerForm.classList.add('active');
        authTitle.textContent = 'Register';
        switchText.textContent = 'Already have an account? ';
        switchLink.textContent = 'Login here!';
    } else {
        // Switch to login
        registerForm.classList.remove('active');
        loginForm.classList.add('active');
        authTitle.textContent = 'Login';
        switchText.textContent = "Don't have account? ";
        switchLink.textContent = "Let's Get Started For Free!";
    }
}

// Show forgot password (placeholder)
function showForgotPassword() {
    alert('Forgot password feature coming soon!');
}

function showAuthTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(form => form.classList.remove('active'));
    
    if (tab === 'login') {
        document.querySelector('.tab-btn').classList.add('active');
        document.getElementById('login-form').classList.add('active');
    } else {
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        document.getElementById('register-form').classList.add('active');
    }
}

// Navigation
function showPage(pageName) {
    // Check if we're leaving the interview page
    const currentPage = document.querySelector('.page-content[style*="block"]');
    const isLeavingInterview = currentPage && currentPage.id === 'chatbot-page';
    
    // If leaving interview page, cleanup camera and mic
    if (isLeavingInterview && pageName !== 'chatbot') {
        if (typeof cleanupInterviewMedia === 'function') {
            cleanupInterviewMedia();
        }
    }
    
    document.querySelectorAll('.page-content').forEach(page => {
        page.style.display = 'none';
    });
    
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
        targetPage.style.display = 'block';
        
        // Close all dropdown menus when navigating
        closeNonTechnicalMenu();
        closeInterviewMenu();
        
        // Load page-specific data
        switch(pageName) {
            case 'dashboard':
                loadDashboard();
        // Load notification badge count (only if logged in)
        if (authToken && currentUser) {
            loadNotificationBadge();
        }
                // Placement Readiness Score is loaded within loadDashboard()
                break;
            case 'coding':
                loadCodingPage();
                break;
            case 'quizzes':
                loadQuizzesPage();
                break;
            case 'non-technical':
                loadNonTechnicalPage();
                break;
            case 'companies':
                loadCompaniesPage();
                break;
            case 'resources':
                loadResourcesPage();
                break;
            case 'leaderboard':
                loadLeaderboard();
                break;
            case 'chatbot':
            case 'ai-interview':
                loadChatbotPage();
                break;
        }
        
        // Update +Add button visibility based on role
        updateAddButtonVisibility();
    }
}

function hideAllPages() {
    document.querySelectorAll('.page-content').forEach(page => page.style.display = 'none');
}

function showOnlyDashboard() {
    hideAllPages();
    const dash = document.getElementById('dashboard-page');
    if (dash) dash.style.display = 'block';
    loadDashboard();
}

function showDashboard() {
    updateActiveNav('Dashboard');
    showOnlyDashboard();
}
function showNonTechnical() { 
    // Close dropdown menu
    closeNonTechnicalMenu();
    updateActiveNav('Non-Technical');
    showPage('non-technical'); 
}

function showQuizPage() {
    // Close dropdown menu
    closeNonTechnicalMenu();
    updateActiveNav('Non-Technical');
    showPage('quizzes');
}

function toggleNonTechnicalMenu() {
    const menu = document.getElementById('non-technical-menu');
    if (menu) {
        menu.parentElement.classList.toggle('open');
    }
}

function closeNonTechnicalMenu() {
    const menu = document.getElementById('non-technical-menu');
    if (menu) {
        menu.parentElement.classList.remove('open');
    }
}
function showResources() { 
    updateActiveNav('Resources');
    showPage('resources');
    loadResourcesPage();
    // Hide upload form by default
    closeResourceUploadForm();
}
function showInterview() { 
    // Close dropdown menu
    closeInterviewMenu();
    updateActiveNav('Interview');
    
    // Cleanup any existing media before showing interview page
    if (typeof cleanupInterviewMedia === 'function') {
        cleanupInterviewMedia();
    }
    
    showPage('chatbot');
    
    // Ensure interview sections are properly initialized
    const typeSelection = document.getElementById('interview-type-selection');
    const uploadSection = document.getElementById('interview-upload');
    const chatSection = document.getElementById('interview-chat');
    const resultsSection = document.getElementById('interview-results');
    
    // Show type selection, hide others
    if (typeSelection) typeSelection.style.display = 'block';
    if (uploadSection) uploadSection.style.display = 'none';
    if (chatSection) chatSection.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'none';
    
    // Reset interview state and show type selection
    if (typeof startNewInterview === 'function') {
        startNewInterview();
    }
}
function showCompanies() { 
    // Close dropdown menu
    closeInterviewMenu();
    updateActiveNav('Interview');
    showPage('companies'); 
}
function showLeaderboard() { 
    updateActiveNav('Leaderboard');
    showPage('leaderboard'); 
}
function showCodePractice() { 
    updateActiveNav('CodePractice');
    showPage('coding'); 
}

// Navigation functions for Placement Readiness Score links
function navigateToCodePractice() {
    showCodePractice();
}

function navigateToNonTechnical() {
    showNonTechnical();
}

function navigateToInterview() {
    showInterview();
}

function updateActiveNav(activeName) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        const linkText = link.textContent.trim();
        // Handle dropdown toggle button separately
        if (link.classList.contains('dropdown-toggle')) {
            return;
        }
        if (linkText === activeName) {
            link.classList.add('active');
        }
    });
}

function toggleInterviewMenu() {
    const menu = document.getElementById('interview-menu');
    if (menu) {
        menu.parentElement.classList.toggle('open');
    }
}

function closeInterviewMenu() {
    const menu = document.getElementById('interview-menu');
    if (menu) {
        menu.parentElement.classList.remove('open');
    }
}

// Dashboard
async function loadDashboard() {
    try {
        // Check user role and load appropriate dashboard
        if (currentUser && (currentUser.role === 'faculty' || currentUser.role === 'admin')) {
            await loadFacultyAdminDashboard();
            return;
        }
        
        // Student dashboard
        const data = await studentAPI.getDashboard();
        
        // Recent Submissions
        const submissionsDiv = document.getElementById('recent-submissions');
        submissionsDiv.innerHTML = data.recent_submissions.length > 0
            ? data.recent_submissions.map(s => `
                <div class="notification-item">
                    <strong>${s.status}</strong> - Question ${s.question_id}
                    <small>${new Date(s.submitted_at).toLocaleDateString()}</small>
                </div>
            `).join('')
            : 'No submissions yet';
        
        // Available Quizzes
        const quizzesDiv = document.getElementById('available-quizzes');
        quizzesDiv.innerHTML = data.available_quizzes.length > 0
            ? data.available_quizzes.map(q => `
                <div class="quiz-item" onclick="takeQuiz(${q.id})">
                    <h4>${q.title}</h4>
                    <p>${q.description || ''}</p>
                </div>
            `).join('')
            : 'No quizzes available';
        
        // Performance Summary
        const perfData = await studentAPI.getPerformance();
        const perfDiv = document.getElementById('performance-summary');
        if (perfDiv) {
            perfDiv.innerHTML = `
                <div class="performance-stack">
                    <div class="metric-card">
                        <p>Total Submissions</p>
                        <strong>${perfData.total_submissions || 0}</strong>
                    </div>
                    <div class="metric-card">
                        <p>Accuracy</p>
                        <strong>${(perfData.accuracy || 0).toFixed(1)}%</strong>
                    </div>
                    <div class="metric-card">
                        <p>Quizzes Taken</p>
                        <strong>${perfData.total_quizzes || 0}</strong>
                    </div>
                    <div class="metric-card">
                        <p>Avg Quiz Score</p>
                        <strong>${(perfData.avg_quiz_score || 0).toFixed(1)}</strong>
                    </div>
                </div>
            `;
        }
        
        // Load Placement Readiness Score
        await loadPlacementReadinessScore();
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Faculty/Admin Dashboard
async function loadFacultyAdminDashboard() {
    try {
        // Show faculty/admin dashboard, hide student dashboard
        const studentDashboard = document.getElementById('student-dashboard');
        const facultyDashboard = document.getElementById('faculty-admin-dashboard');
        
        if (studentDashboard) studentDashboard.style.display = 'none';
        if (facultyDashboard) facultyDashboard.style.display = 'block';
        
        // Load dashboard data based on role
        let dashboardData;
        if (currentUser && currentUser.role === 'admin') {
            dashboardData = await adminAPI.getDashboard();
        } else {
            dashboardData = await facultyAPI.getDashboard();
        }
        
        // Update batch overview
        if (dashboardData.batch_analytics) {
            const analytics = dashboardData.batch_analytics;
            const totalStudentsEl = document.getElementById('batch-total-students');
            const totalSubmissionsEl = document.getElementById('batch-total-submissions');
            const totalQuizzesEl = document.getElementById('batch-total-quizzes');
            const avgAccuracyEl = document.getElementById('batch-avg-accuracy');
            const avgQuizScoreEl = document.getElementById('batch-avg-quiz-score');
            
            if (totalStudentsEl) totalStudentsEl.textContent = analytics.total_students || 0;
            if (totalSubmissionsEl) totalSubmissionsEl.textContent = analytics.total_submissions || 0;
            if (totalQuizzesEl) totalQuizzesEl.textContent = analytics.total_quiz_attempts || 0;
            if (avgAccuracyEl) avgAccuracyEl.textContent = `${analytics.batch_avg_accuracy || 0}%`;
            if (avgQuizScoreEl) avgQuizScoreEl.textContent = analytics.batch_avg_quiz_score || 0;
        }
        
        // Load student performance
        await loadStudentPerformanceTable();
        
        // Load weak areas
        await loadWeakAreas();
        
        // Load Placement Readiness Score (for current user)
        await loadPlacementReadinessScore();
        
    } catch (error) {
        console.error('Error loading faculty/admin dashboard:', error);
    }
}

// Load Placement Readiness Score
async function loadPlacementReadinessScore(userId = null) {
    try {
        const data = await studentAPI.getPlacementReadiness(userId);
        
        console.log('Placement Readiness Data:', data); // Debug log
        
        // Determine which elements to update based on dashboard type
        const isFacultyDashboard = document.getElementById('faculty-admin-dashboard')?.style.display !== 'none';
        const scoreValueId = isFacultyDashboard ? 'faculty-placement-score-value' : 'placement-score-value';
        const codePracticeId = isFacultyDashboard ? 'faculty-code-practice-score' : 'code-practice-score';
        const nonTechnicalId = isFacultyDashboard ? 'faculty-non-technical-score' : 'non-technical-score';
        const interviewId = isFacultyDashboard ? 'faculty-interview-score' : 'interview-score';
        const contentId = isFacultyDashboard ? 'faculty-placement-readiness-content' : 'placement-readiness-content';
        
        // Update main score
        const scoreValueEl = document.getElementById(scoreValueId);
        if (scoreValueEl) {
            const score = Math.round(data.placement_readiness_score || 0);
            scoreValueEl.textContent = score;
            console.log(`Updated ${scoreValueId} to ${score}`); // Debug log
            
            // Add color class based on score
            scoreValueEl.className = '';
            if (score >= 80) {
                scoreValueEl.classList.add('score-excellent');
            } else if (score >= 60) {
                scoreValueEl.classList.add('score-good');
            } else if (score >= 40) {
                scoreValueEl.classList.add('score-medium');
            } else {
                scoreValueEl.classList.add('score-poor');
            }
        }
        
        // Update breakdown scores
        const breakdown = data.breakdown || {};
        const codePracticeEl = document.getElementById(codePracticeId);
        const nonTechnicalEl = document.getElementById(nonTechnicalId);
        const interviewEl = document.getElementById(interviewId);
        
        if (codePracticeEl) {
            const codePracticeScore = Math.round(breakdown.code_practice || 0);
            codePracticeEl.textContent = `${codePracticeScore}%`;
            codePracticeEl.className = 'breakdown-value ' + getScoreClass(breakdown.code_practice || 0);
        }
        if (nonTechnicalEl) {
            const nonTechnicalScore = Math.round(breakdown.non_technical || 0);
            nonTechnicalEl.textContent = `${nonTechnicalScore}%`;
            nonTechnicalEl.className = 'breakdown-value ' + getScoreClass(breakdown.non_technical || 0);
        }
        if (interviewEl) {
            const interviewScore = Math.round(breakdown.interview || 0);
            interviewEl.textContent = `${interviewScore}%`;
            interviewEl.className = 'breakdown-value ' + getScoreClass(breakdown.interview || 0);
        }
        
        // Show/hide message based on data availability
        // Note: Don't clear innerHTML as it contains the score display elements
        const contentEl = document.getElementById(contentId);
        if (contentEl) {
            // Check if there's a "no data" message element
            let noDataMsg = contentEl.querySelector('.no-data-message');
            
            // Check if any data is available
            const hasData = data.data_available && (
                data.data_available.code_practice || 
                data.data_available.non_technical || 
                data.data_available.interview
            );
            
            if (!hasData) {
                // Show no data message (only if it doesn't exist and score elements don't exist)
                const hasScoreElements = contentEl.querySelector('#placement-score-value') || 
                                       contentEl.querySelector('#faculty-placement-score-value');
                
                if (!hasScoreElements) {
                    // If score elements don't exist, show full message
                    if (!noDataMsg) {
                        contentEl.innerHTML = '<p class="no-data-message" style="text-align: center; color: rgba(232,236,243,0.6); padding: 20px;">Complete Code Practice challenges, Non-Technical quizzes, and AI Virtual Interviews to see your Placement Readiness Score</p>';
                    }
                } else {
                    // Score elements exist, just add message below
                    if (!noDataMsg) {
                        const msgEl = document.createElement('p');
                        msgEl.className = 'no-data-message';
                        msgEl.style.cssText = 'text-align: center; color: rgba(232,236,243,0.6); padding: 20px; margin-top: 20px;';
                        msgEl.textContent = 'Complete more Code Practice, Non-Technical quizzes, or AI Virtual Interviews to improve your score';
                        contentEl.appendChild(msgEl);
                    }
                }
            } else {
                // Data is available - remove no data message if it exists
                if (noDataMsg) {
                    noDataMsg.remove();
                }
            }
        }
    } catch (error) {
        console.error('Error loading placement readiness score:', error);
        const isFacultyDashboard = document.getElementById('faculty-admin-dashboard')?.style.display !== 'none';
        const contentId = isFacultyDashboard ? 'faculty-placement-readiness-content' : 'placement-readiness-content';
        const contentEl = document.getElementById(contentId);
        if (contentEl) {
            let errorMsg = 'Error loading Placement Readiness Score';
            if (error.message) {
                if (error.message.includes('Cannot connect to server')) {
                    errorMsg = 'Cannot connect to server. Please ensure the backend is running.';
                } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
                    errorMsg = 'Please log in again to view your Placement Readiness Score.';
                } else {
                    errorMsg = error.message;
                }
            }
            contentEl.innerHTML = `<p style="text-align: center; color: #ff6b6b; padding: 20px;">${errorMsg}</p>`;
        }
    }
}

// Helper function to get score class for styling
function getScoreClass(score) {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    if (score >= 40) return 'score-medium';
    return 'score-poor';
}

// Load Student Performance Table
async function loadStudentPerformanceTable() {
    try {
        const performanceData = await facultyAPI.getStudentPerformance();
        const tableBody = document.getElementById('student-performance-table');
        
        if (!tableBody) return;
        
        if (performanceData.performance && performanceData.performance.length > 0) {
            tableBody.innerHTML = performanceData.performance.map(perf => {
                const student = perf.student;
                return `
                    <tr>
                        <td>${student.full_name || 'N/A'}</td>
                        <td>${student.username}</td>
                        <td>${perf.total_submissions || 0}</td>
                        <td>
                            <span class="accuracy-badge ${perf.accuracy >= 70 ? 'good' : perf.accuracy >= 50 ? 'medium' : 'poor'}">
                                ${perf.accuracy || 0}%
                            </span>
                        </td>
                        <td>${perf.total_quizzes || 0}</td>
                        <td>${perf.avg_quiz_score || 0}</td>
                    </tr>
                `;
            }).join('');
        } else {
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No student data available</td></tr>';
        }
    } catch (error) {
        console.error('Error loading student performance:', error);
        const tableBody = document.getElementById('student-performance-table');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #ff6b6b;">Error loading student data</td></tr>';
        }
    }
}

// Load Weak Areas
async function loadWeakAreas() {
    try {
        const weakAreasData = await facultyAPI.getBatchWeakAreas();
        
        // Display weak difficulties
        const difficultiesDiv = document.getElementById('weak-difficulties');
        if (difficultiesDiv && weakAreasData.weak_difficulties) {
            if (weakAreasData.weak_difficulties.length > 0) {
                difficultiesDiv.innerHTML = weakAreasData.weak_difficulties.slice(0, 5).map(area => `
                    <div class="weak-area-item ${area.needs_improvement ? 'needs-improvement' : ''}">
                        <span class="area-name">${area.area}</span>
                        <span class="area-stats">${area.accepted}/${area.total_attempts} (${area.accuracy}%)</span>
                    </div>
                `).join('');
            } else {
                difficultiesDiv.innerHTML = '<p style="color: rgba(232,236,243,0.6);">No data available</p>';
            }
        }
        
        // Display weak languages
        const languagesDiv = document.getElementById('weak-languages');
        if (languagesDiv && weakAreasData.weak_languages) {
            if (weakAreasData.weak_languages.length > 0) {
                languagesDiv.innerHTML = weakAreasData.weak_languages.slice(0, 5).map(area => `
                    <div class="weak-area-item ${area.needs_improvement ? 'needs-improvement' : ''}">
                        <span class="area-name">${area.area}</span>
                        <span class="area-stats">${area.accepted}/${area.total_attempts} (${area.accuracy}%)</span>
                    </div>
                `).join('');
            } else {
                languagesDiv.innerHTML = '<p style="color: rgba(232,236,243,0.6);">No data available</p>';
            }
        }
        
        // Display weak topics
        const topicsDiv = document.getElementById('weak-topics');
        if (topicsDiv && weakAreasData.weak_topics) {
            if (weakAreasData.weak_topics.length > 0) {
                topicsDiv.innerHTML = weakAreasData.weak_topics.slice(0, 8).map(area => `
                    <div class="weak-area-item ${area.needs_improvement ? 'needs-improvement' : ''}">
                        <span class="area-name">${area.area}</span>
                        <span class="area-stats">${area.accepted}/${area.total_attempts} (${area.accuracy}%)</span>
                    </div>
                `).join('');
            } else {
                topicsDiv.innerHTML = '<p style="color: rgba(232,236,243,0.6);">No data available</p>';
            }
        }
        
        // Display weak question types
        const questionTypesDiv = document.getElementById('weak-question-types');
        if (questionTypesDiv && weakAreasData.weak_question_types) {
            if (weakAreasData.weak_question_types.length > 0) {
                questionTypesDiv.innerHTML = weakAreasData.weak_question_types.map(area => `
                    <div class="weak-area-item ${area.needs_improvement ? 'needs-improvement' : ''}">
                        <span class="area-name">${area.area}</span>
                        <span class="area-stats">${area.accepted}/${area.total_attempts} (${area.accuracy}%)</span>
                    </div>
                `).join('');
            } else {
                questionTypesDiv.innerHTML = '<p style="color: rgba(232,236,243,0.6);">No data available</p>';
            }
        }
        
    } catch (error) {
        console.error('Error loading weak areas:', error);
    }
}

// Coding Page (New UI)
function setupCodingUI() {
    const searchInput = document.getElementById('cp-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            codingSearch = e.target.value.toLowerCase();
            renderCodingQuestions();
        });
    }

    const topicsInput = document.getElementById('cp-topics');
    if (topicsInput) {
        topicsInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && topicsInput.value.trim()) {
                e.preventDefault();
                addTopicChip(topicsInput.value.trim());
                topicsInput.value = '';
            }
        });
    }

    // Suggested chips click handled inline; ensure focus on open
    const addBtn = document.querySelector('.add-btn');
    if (addBtn) {
        addBtn.addEventListener('click', () => {
            setTimeout(() => {
                const t = document.getElementById('cp-topics');
                if (t) t.focus();
            }, 50);
        });
    }
}

function addTopicChip(label) {
    if (cpTopicTags.includes(label)) return;
    cpTopicTags.push(label);
    const chips = document.getElementById('cp-topic-chips');
    chips.innerHTML = cpTopicTags.map(t => `<span class="tag">${t}</span>`).join('');
    clearError('topics');
}

async function loadCodingPage() {
    try {
        const [questionRes, submissionsRes] = await Promise.all([
            studentAPI.getQuestions({ type: 'coding', per_page: 200 }),
            codingAPI.getSubmissions()
        ]);

        const solvedIds = new Set(
            (submissionsRes.submissions || [])
                .filter(s => s.status === 'accepted')
                .map(s => s.question_id)
        );

        codingQuestions = questionRes.questions.map(q => ({
            ...q,
            status: solvedIds.has(q.id) ? 'solved' : 'unsolved',
            company_name: q.company_name || 'General',
            tags: q.tags || []
        }));

        renderCodingQuestions();
    } catch (error) {
        console.error('Error loading coding page:', error);
    }
}

function renderCodingQuestions() {
    const listEl = document.getElementById('cp-question-list');
    if (!listEl) return;

    const total = codingQuestions.length;
    const solved = codingQuestions.filter(q => q.status === 'solved').length;
    const unsolved = total - solved;
    const progress = total ? Math.round((solved / total) * 100) : 0;

    setText('cp-total', total);
    setText('cp-solved', solved);
    setText('cp-unsolved', unsolved);

    const filtered = codingQuestions.filter(q => {
        const matchesFilter = codingFilter === 'all' ? true : q.status === codingFilter;
        const matchesSearch = !codingSearch || (
            q.title.toLowerCase().includes(codingSearch) ||
            q.company_name.toLowerCase().includes(codingSearch) ||
            (q.tags || []).some(t => t.toLowerCase().includes(codingSearch))
        );
        return matchesFilter && matchesSearch;
    });

    if (filtered.length === 0) {
        listEl.innerHTML = `<div class="card">No questions found.</div>`;
        return;
    }

    listEl.innerHTML = filtered.map(q => `
        <div class="cp-card" onclick="openCodingQuestion(${q.id})" style="cursor: pointer;">
            <div class="cp-card-header">
                <div class="cp-title-row">
                    <span class="cp-status-dot ${q.status === 'unsolved' ? 'status-unsolved' : ''}"></span>
                    <div>
                        <div>${q.title}</div>
                        <div class="cp-company">🏢 ${q.company_name}</div>
                    </div>
                </div>
                <div class="cp-card-right">
                    ${q.status === 'solved' 
                        ? `<span class="btn btn-sm btn-solved" style="cursor: default;">✅ Solved</span>` 
                        : `<span class="cp-pill pill-unsolved">Unsolved</span>
                           <button class="btn btn-sm btn-open" onclick="event.stopPropagation(); openCodingQuestion(${q.id})">Open</button>`
                    }
                </div>
            </div>
            <div class="cp-tags">
                ${(q.tags || []).map(t => `<span class="tag">${t}</span>`).join('')}
            </div>
            <div class="cp-card-footer">
                <span>Difficulty: ${q.difficulty || 'n/a'}</span>
                ${q.type ? `<span>Type: ${q.type}</span>` : ''}
                <span class="cp-star">☆</span>
            </div>
        </div>
    `).join('');
}

async function loadQuestion(questionId) {
    try {
        const local = codingQuestions.find(q => q.id === questionId);
        if (local) {
            currentQuestion = local;
            return;
        }
        const data = await codingAPI.getQuestion(questionId);
        currentQuestion = data.question;
    } catch (e) {
        console.error('Error loading question', e);
    }
}

// Store current coding question
let currentCodingQuestion = null;

// Get starter code based on language
function getStarterCodeForLanguage(language) {
    const templates = {
        'python': `# Write your solution here
def solution():
    # Your code here
    pass

# Example usage
if __name__ == "__main__":
    result = solution()
    print(result)`,
        
        'java': `public class Solution {
    public static void main(String[] args) {
        // Your code here
        Solution solution = new Solution();
        // Call your method
    }
    
    // Add your methods here
}`,
        
        'cpp': `#include <iostream>
#include <vector>
#include <string>
using namespace std;

int main() {
    // Your code here
    
    return 0;
}`,
        
        'c': `#include <stdio.h>
#include <stdlib.h>

int main() {
    // Your code here
    
    return 0;
}`
    };
    
    return templates[language] || templates['python'];
}

// Open Coding Question in Full Page View
async function openCodingQuestion(questionId) {
    try {
        // Hide question list
        document.getElementById('cp-question-list').style.display = 'none';
        document.querySelector('.cp-stats').style.display = 'none';
        document.querySelector('.cp-toolbar').style.display = 'none';
        
        // Show full page view
        const fullPageView = document.getElementById('coding-question-view');
        fullPageView.style.display = 'block';
        
        // Load question data
        const data = await codingAPI.getQuestion(questionId);
        const question = data.question;
        
        if (!question) {
            alert('Question not found');
            return;
        }
        
        // Store question globally
        currentCodingQuestion = question;
        currentQuestion = question;
        
        // Populate question details on left side
        document.getElementById('coding-question-title').textContent = question.title || 'Coding Question';
        
        const metaDiv = document.getElementById('coding-question-meta');
        const tags = question.tags ? (Array.isArray(question.tags) ? question.tags : question.tags.split(',')) : [];
        metaDiv.innerHTML = `
            <div class="question-meta-info">
                <span class="meta-badge">Company: ${question.company_name || 'General'}</span>
                <span class="meta-badge">Difficulty: ${question.difficulty || 'N/A'}</span>
            </div>
            ${tags.length > 0 ? `<div class="question-tags-view">
                ${tags.map(t => `<span class="tag">${t.trim()}</span>`).join('')}
            </div>` : ''}
        `;
        
        const contentDiv = document.getElementById('coding-question-content');
        const testCases = question.test_cases ? (typeof question.test_cases === 'string' ? JSON.parse(question.test_cases) : question.test_cases) : [];
        
        contentDiv.innerHTML = `
            <div class="question-description-view">
                <h4>Problem Description</h4>
                <p>${question.description || 'No description available.'}</p>
            </div>
            ${testCases.length > 0 ? `
            <div class="test-cases-view">
                <h4>Test Cases</h4>
                ${testCases.map((tc, idx) => `
                    <div class="test-case-item">
                        <strong>Test Case ${idx + 1}:</strong>
                        <div class="test-case-content">
                            <div><strong>Input:</strong> <code>${tc.input || ''}</code></div>
                            <div><strong>Expected Output:</strong> <code>${tc.output || ''}</code></div>
                        </div>
                    </div>
                `).join('')}
            </div>
            ` : ''}
        `;
        
        // Set starter code in editor based on selected language
        const codeEditor = document.getElementById('code-editor');
        const languageSelect = document.getElementById('code-language');
        
        if (codeEditor && languageSelect) {
            const selectedLanguage = languageSelect.value;
            // Always use language-specific template, ignore question.starter_code
            const starterCode = getStarterCodeForLanguage(selectedLanguage);
            codeEditor.value = starterCode;
            
            // Remove any existing event listeners by cloning the select
            const newSelect = languageSelect.cloneNode(true);
            languageSelect.parentNode.replaceChild(newSelect, languageSelect);
            
            // Add event listener to language selector to update code when language changes
            newSelect.addEventListener('change', function() {
                const selectedLanguage = this.value;
                const codeEditor = document.getElementById('code-editor');
                if (codeEditor) {
                    // Check if user has written custom code
                    const currentCode = codeEditor.value.trim();
                    const previousLanguage = this.dataset.previousLang || 'python';
                    const previousStarter = getStarterCodeForLanguage(previousLanguage);
                    
                    // Only replace if code is still the starter template or empty
                    if (!currentCode || currentCode === previousStarter || currentCode.length < 50) {
                        // User hasn't written much, just replace with new language template
                        const starterCode = getStarterCodeForLanguage(selectedLanguage);
                        codeEditor.value = starterCode;
                    } else {
                        // Ask user if they want to replace their code
                        if (confirm('Changing language will replace your current code with the new language template. Continue?')) {
                            const starterCode = getStarterCodeForLanguage(selectedLanguage);
                            codeEditor.value = starterCode;
                        } else {
                            // Revert to previous language
                            this.value = previousLanguage;
                            return;
                        }
                    }
                    this.dataset.previousLang = selectedLanguage;
                }
            });
            
            // Load editor settings
            loadEditorSettings();
            
            // Store initial language
            newSelect.dataset.previousLang = selectedLanguage;
        }
        
        // Clear output
        const outputDiv = document.getElementById('code-output');
        if (outputDiv) {
            outputDiv.innerHTML = '<div class="output-placeholder">Output will appear here...</div>';
        }
        
    } catch (error) {
        console.error('Error loading coding question:', error);
        alert('Failed to load question');
    }
}

function closeCodingQuestionView() {
    // Hide full page view
    const fullPageView = document.getElementById('coding-question-view');
    fullPageView.style.display = 'none';
    
    // Show question list
    document.getElementById('cp-question-list').style.display = 'flex';
    document.querySelector('.cp-stats').style.display = 'grid';
    document.querySelector('.cp-toolbar').style.display = 'flex';
    
    currentCodingQuestion = null;
    currentQuestion = null;
}

async function runCode() {
    const codeEditor = document.getElementById('code-editor');
    const languageSelect = document.getElementById('code-language');
    const outputDiv = document.getElementById('code-output');
    
    if (!codeEditor || !languageSelect || !outputDiv) return;
    
    const code = codeEditor.value.trim();
    const language = languageSelect.value;
    
    if (!code) {
        outputDiv.innerHTML = '<div class="output-error">Please write some code first.</div>';
        return;
    }
    
    // Show loading
    outputDiv.innerHTML = '<div class="output-loading">Running code...</div>';
    
    try {
        // If we have a current question, run test cases
        let result;
        if (currentCodingQuestion && currentCodingQuestion.id) {
            result = await codingAPI.executeCode(code, language, '', currentCodingQuestion.id);
        } else {
            result = await codingAPI.executeCode(code, language);
        }
        
        // Run mode: Just show program output (like normal compiler)
        // User program controls input/output - if no print, show "(no output)"
        if (result.output !== undefined) {
            outputDiv.innerHTML = `
                <div class="output-success">
                    <div class="output-label">Output:</div>
                    <pre>${result.output || '(no output)'}</pre>
                </div>
            `;
        } else if (result.error) {
            outputDiv.innerHTML = `
                <div class="output-error">
                    <div class="output-label">Error:</div>
                    <pre>${result.error}</pre>
                </div>
            `;
        } else {
            outputDiv.innerHTML = '<div class="output-placeholder">(no output)</div>';
        }
    } catch (error) {
        outputDiv.innerHTML = `
            <div class="output-error">
                <div class="output-label">Error:</div>
                <pre>${error.message || 'Failed to execute code'}</pre>
            </div>
        `;
    }
}

async function submitCode() {
    if (!currentCodingQuestion) {
        alert('No question loaded');
        return;
    }
    
    const codeEditor = document.getElementById('code-editor');
    const languageSelect = document.getElementById('code-language');
    const outputDiv = document.getElementById('code-output');
    
    if (!codeEditor || !languageSelect || !outputDiv) return;
    
    const code = codeEditor.value.trim();
    const language = languageSelect.value;
    
    if (!code) {
        alert('Please write some code before submitting');
        return;
    }
    
    // Show loading
    outputDiv.innerHTML = '<div class="output-loading">Submitting code...</div>';
    
    try {
        const result = await codingAPI.submitCode(currentCodingQuestion.id, code, language);
        
        // Refresh Placement Readiness Score after code submission
        if (typeof loadPlacementReadinessScore === 'function') {
            loadPlacementReadinessScore();
        }
        
        // Display test results - Submit mode shows test case results with ✅/❌
        if (result.test_results && result.test_results.length > 0) {
            const testResultsHtml = result.test_results.map((tr, idx) => {
                const statusIcon = tr.passed ? '✅' : '❌';
                return `
                    <div class="test-result-display ${tr.passed ? 'test-passed' : 'test-failed'}">
                        <div class="test-result-header">
                            <span class="test-case-number">Test Case ${idx + 1}</span>
                            <span class="test-status">${statusIcon}</span>
                        </div>
                        ${!tr.passed ? `
                            <div class="test-result-details">
                                <div class="test-detail-item">
                                    <strong>Expected:</strong> <code>${tr.expected_output || 'N/A'}</code>
                                </div>
                                <div class="test-detail-item">
                                    <strong>Got:</strong> <code>${tr.actual_output || 'N/A'}</code>
                                </div>
                                ${tr.status && tr.status !== 'accepted' ? `
                                    <div class="test-detail-item">
                                        <strong>Status:</strong> <span class="test-status-badge">${tr.status}</span>
                                    </div>
                                ` : ''}
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
            
            const summaryHtml = `
                <div class="test-summary ${result.status === 'accepted' ? 'summary-success' : 'summary-error'}">
                    <strong>${result.status === 'accepted' ? '✅ Accepted!' : '❌ Wrong Answer'}</strong>
                    <span>Test Cases: ${result.test_cases_passed || result.passed || 0} / ${result.total_test_cases || result.total || 0} passed</span>
                    ${result.execution_time ? `<span>Execution Time: ${result.execution_time.toFixed(2)}s</span>` : ''}
                </div>
            `;
            
            outputDiv.innerHTML = `
                <div class="output-test-results">
                    ${summaryHtml}
                    <div class="test-results-list">
                        ${testResultsHtml}
                    </div>
                </div>
            `;
            
            // Reload coding page to update solved status if accepted
            if (result.status === 'accepted') {
                setTimeout(() => {
                    loadCodingPage();
                    // Refresh Placement Readiness Score after successful code submission
                    if (typeof loadPlacementReadinessScore === 'function') {
                        loadPlacementReadinessScore();
                    }
                }, 1000);
            }
        } else if (result.status === 'accepted') {
            outputDiv.innerHTML = `
                <div class="output-success">
                    <div class="output-label">✅ Accepted!</div>
                    <div>Test Cases Passed: ${result.test_cases_passed || result.passed || 0} / ${result.total_test_cases || result.total || 0}</div>
                    ${result.execution_time ? `<div>Execution Time: ${result.execution_time.toFixed(2)}s</div>` : ''}
                </div>
            `;
            
            // Reload coding page to update solved status
            setTimeout(() => {
                loadCodingPage();
            }, 1000);
        } else {
            outputDiv.innerHTML = `
                <div class="output-error">
                    <div class="output-label">❌ Wrong Answer</div>
                    <div>Test Cases Passed: ${result.test_cases_passed || result.passed || 0} / ${result.total_test_cases || result.total || 0}</div>
                </div>
            `;
        }
    } catch (error) {
        outputDiv.innerHTML = `
            <div class="output-error">
                <div class="output-label">Error:</div>
                <pre>${error.message || 'Failed to submit code'}</pre>
            </div>
        `;
    }
}

// ==================== LeetCode-Style Features ====================

// 1. Retrieve Last Submitted Code
async function retrieveLastCode() {
    if (!currentCodingQuestion) {
        alert('No question loaded');
        return;
    }
    
    const codeEditor = document.getElementById('code-editor');
    const languageSelect = document.getElementById('code-language');
    
    if (!codeEditor || !languageSelect) return;
    
    const language = languageSelect.value;
    
    try {
        const result = await codingAPI.getLastSubmission(currentCodingQuestion.id, language);
        
        if (result.submission && result.submission.code) {
            // Confirm before replacing current code
            const currentCode = codeEditor.value.trim();
            if (currentCode && currentCode !== result.submission.code) {
                if (!confirm('This will replace your current code with the last submitted code. Continue?')) {
                    return;
                }
            }
            
            codeEditor.value = result.submission.code;
            
            // Update language if different
            if (result.submission.language && result.submission.language !== language) {
                languageSelect.value = result.submission.language;
            }
            
            // Show success message
            const outputDiv = document.getElementById('code-output');
            if (outputDiv) {
                outputDiv.innerHTML = `
                    <div class="output-success">
                        <div class="output-label">Last submitted code loaded</div>
                        <div style="font-size: 12px; color: rgba(232, 236, 243, 0.7); margin-top: 8px;">
                            Submitted: ${new Date(result.submission.submitted_at).toLocaleString()}
                        </div>
                    </div>
                `;
            }
        } else {
            alert('No previous submission found for this question');
        }
    } catch (error) {
        alert(`Failed to retrieve last code: ${error.message}`);
    }
}

// 2. Reset to Default Template
function resetToTemplate() {
    const codeEditor = document.getElementById('code-editor');
    const languageSelect = document.getElementById('code-language');
    
    if (!codeEditor || !languageSelect) return;
    
    const currentCode = codeEditor.value.trim();
    const language = languageSelect.value;
    
    // Confirm before resetting
    if (currentCode) {
        if (!confirm('This will replace your current code with the default template. Continue?')) {
            return;
        }
    }
    
    // Get default template for current language
    const template = getStarterCodeForLanguage(language);
    codeEditor.value = template;
    
    // Show message
    const outputDiv = document.getElementById('code-output');
    if (outputDiv) {
        outputDiv.innerHTML = `
            <div class="output-success">
                <div class="output-label">Reset to default template</div>
            </div>
        `;
    }
}

// 3. Editor Settings
function openEditorSettings() {
    const modal = document.getElementById('editor-settings-modal');
    if (!modal) return;
    
    // Load saved settings
    const settings = getEditorSettings();
    document.getElementById('editor-font-size').value = settings.fontSize || '14';
    document.getElementById('editor-theme').value = settings.theme || 'dark';
    document.getElementById('editor-key-bindings').value = settings.keyBindings || 'default';
    document.getElementById('editor-tab-size').value = settings.tabSize || '4';
    document.getElementById('editor-word-wrap').value = settings.wordWrap || 'on';
    
    modal.classList.remove('hidden');
}

function closeEditorSettings() {
    const modal = document.getElementById('editor-settings-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function saveEditorSettings() {
    const settings = {
        fontSize: document.getElementById('editor-font-size').value,
        theme: document.getElementById('editor-theme').value,
        keyBindings: document.getElementById('editor-key-bindings').value,
        tabSize: document.getElementById('editor-tab-size').value,
        wordWrap: document.getElementById('editor-word-wrap').value
    };
    
    // Save to localStorage
    localStorage.setItem('editorSettings', JSON.stringify(settings));
    
    // Apply settings
    applyEditorSettings(settings);
    
    closeEditorSettings();
    
    // Show success message
    const outputDiv = document.getElementById('code-output');
    if (outputDiv) {
        outputDiv.innerHTML = `
            <div class="output-success">
                <div class="output-label">Editor settings saved</div>
            </div>
        `;
    }
}

function getEditorSettings() {
    const saved = localStorage.getItem('editorSettings');
    if (saved) {
        try {
            return JSON.parse(saved);
        } catch (e) {
            return getDefaultEditorSettings();
        }
    }
    return getDefaultEditorSettings();
}

function getDefaultEditorSettings() {
    return {
        fontSize: '14',
        theme: 'dark',
        keyBindings: 'default',
        tabSize: '4',
        wordWrap: 'on'
    };
}

function applyEditorSettings(settings) {
    const codeEditor = document.getElementById('code-editor');
    if (!codeEditor) return;
    
    // Apply font size
    codeEditor.style.fontSize = `${settings.fontSize}px`;
    
    // Apply theme (affects background/colors)
    if (settings.theme === 'light') {
        codeEditor.style.backgroundColor = '#ffffff';
        codeEditor.style.color = '#000000';
    } else if (settings.theme === 'dark') {
        codeEditor.style.backgroundColor = '#0c1322';
        codeEditor.style.color = '#66e3c4';
    } else if (settings.theme === 'monokai') {
        codeEditor.style.backgroundColor = '#272822';
        codeEditor.style.color = '#f8f8f2';
    } else if (settings.theme === 'solarized') {
        codeEditor.style.backgroundColor = '#002b36';
        codeEditor.style.color = '#839496';
    }
    
    // Apply word wrap
    if (settings.wordWrap === 'on') {
        codeEditor.style.whiteSpace = 'pre-wrap';
        codeEditor.style.wordWrap = 'break-word';
    } else {
        codeEditor.style.whiteSpace = 'pre';
        codeEditor.style.wordWrap = 'normal';
    }
    
    // Tab size is handled via CSS (tab-size property)
    codeEditor.style.tabSize = settings.tabSize;
    codeEditor.style.MozTabSize = settings.tabSize;
}

// Load editor settings on page load
function loadEditorSettings() {
    const settings = getEditorSettings();
    applyEditorSettings(settings);
}

function setCodingFilter(filter) {
    codingFilter = filter;
    document.querySelectorAll('.chip').forEach(chip => {
        chip.classList.toggle('active', chip.dataset.filter === filter);
    });
    renderCodingQuestions();
}

function openQuestionModal() {
    const modal = document.getElementById('cp-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeQuestionModal() {
    const modal = document.getElementById('cp-modal');
    if (modal) modal.classList.add('hidden');
    document.getElementById('cp-company').value = '';
    document.getElementById('cp-title').value = '';
    document.getElementById('cp-description').value = '';
    document.getElementById('cp-topics').value = '';
    cpTopicTags = [];
    const chips = document.getElementById('cp-topic-chips');
    if (chips) chips.innerHTML = '';
    
    // Reset test cases container
    const testCasesContainer = document.getElementById('cp-testcases-container');
    if (testCasesContainer) {
        testCasesContainer.innerHTML = `
            <div class="test-case-row">
                <div class="test-case-input-group">
                    <label class="test-case-label">Input:</label>
                    <input type="text" class="test-case-input" placeholder="e.g., 2 3" data-test-case="input">
                </div>
                <div class="test-case-input-group">
                    <label class="test-case-label">Output:</label>
                    <input type="text" class="test-case-output" placeholder="e.g., 5" data-test-case="output">
                </div>
                <button type="button" class="btn-remove-testcase" onclick="removeTestCase(this)" style="display: none;">✕</button>
            </div>
        `;
    }
    
    clearAllErrors();
}

// Test Case Management Functions
function addTestCase() {
    const container = document.getElementById('cp-testcases-container');
    if (!container) return;
    
    const testCaseRow = document.createElement('div');
    testCaseRow.className = 'test-case-row';
    testCaseRow.innerHTML = `
        <div class="test-case-input-group">
            <label class="test-case-label">Input:</label>
            <input type="text" class="test-case-input" placeholder="e.g., 2 3" data-test-case="input">
        </div>
        <div class="test-case-input-group">
            <label class="test-case-label">Output:</label>
            <input type="text" class="test-case-output" placeholder="e.g., 5" data-test-case="output">
        </div>
        <button type="button" class="btn-remove-testcase" onclick="removeTestCase(this)">✕</button>
    `;
    container.appendChild(testCaseRow);
    
    // Update remove button visibility
    updateTestCaseRemoveButtons();
}

function removeTestCase(btn) {
    const container = document.getElementById('cp-testcases-container');
    if (!container) return;
    
    const rows = container.querySelectorAll('.test-case-row');
    if (rows.length <= 1) {
        alert('At least one test case is required');
        return;
    }
    
    btn.closest('.test-case-row').remove();
    updateTestCaseRemoveButtons();
}

function updateTestCaseRemoveButtons() {
    const container = document.getElementById('cp-testcases-container');
    if (!container) return;
    
    const rows = container.querySelectorAll('.test-case-row');
    rows.forEach(row => {
        const removeBtn = row.querySelector('.btn-remove-testcase');
        if (removeBtn) {
            removeBtn.style.display = rows.length > 1 ? 'block' : 'none';
        }
    });
}

function parseTestCases() {
    const container = document.getElementById('cp-testcases-container');
    if (!container) return [];
    
    const rows = container.querySelectorAll('.test-case-row');
    const cases = [];
    
    rows.forEach(row => {
        const inputField = row.querySelector('.test-case-input');
        const outputField = row.querySelector('.test-case-output');
        
        if (inputField && outputField) {
            let input = inputField.value.trim();
            let output = outputField.value.trim();
            
            // Clean up input/output - remove labels if present
            input = input.replace(/^Input:\s*/i, '').replace(/^nums\s*=\s*/i, '').trim();
            output = output.replace(/^Output:\s*/i, '').trim();
            
            if (input && output) {
                cases.push({ input, output });
            }
        }
    });
    
    return cases;
}

function findCompanyIdByName(name) {
    if (!name) return null;
    const found = companies.find(c => c.name.toLowerCase() === name.toLowerCase());
    return found ? found.id : null;
}

async function submitNewQuestion() {
    const title = document.getElementById('cp-title').value.trim();
    const description = document.getElementById('cp-description').value.trim();
    const companyName = document.getElementById('cp-company').value.trim();

    let hasError = false;
    clearAllErrors();
    if (!title) { setError('title', 'Title is required'); hasError = true; }
    if (!description) { setError('question', 'Question is required'); hasError = true; }
    if (cpTopicTags.length === 0) { setError('topics', 'Please add at least one topic'); hasError = true; }
    
    const parsedCases = parseTestCases();
    if (!parsedCases.length) {
        setError('testcases', 'Please provide at least one valid Input/Output pair');
        hasError = true;
    }
    
    if (hasError) return;

    const payload = {
        title,
        description,
        type: 'coding',
        difficulty: 'medium',
        company_id: findCompanyIdByName(companyName),
        tags: cpTopicTags,
        test_cases: parsedCases,
        starter_code: '',  // Optional but include it
        solution: ''  // Optional but include it
    };

    try {
        const result = await facultyAPI.createQuestion(payload);
        closeQuestionModal();
        await loadCodingPage();
        alert('Question added successfully.');
    } catch (error) {
        console.error('Error creating question:', error);
        const errorMessage = error.message || 'Failed to add question';
        setError('question', errorMessage);
        // Also show alert for visibility
        alert(`Error: ${errorMessage}`);
    }
}

function setError(field, message) {
    const el = document.getElementById(`cp-error-${field}`);
    if (el) el.textContent = message;
}

function clearError(field) {
    const el = document.getElementById(`cp-error-${field}`);
    if (el) el.textContent = '';
}

function clearAllErrors() {
    ['question', 'testcases', 'topics', 'title'].forEach(clearError);
}

// Non-Technical Questions Page
async function loadNonTechnicalPage() {
    try {
        // Check user role for +Add button visibility
        const addBtn = document.getElementById('add-nontech-btn');
        if (addBtn) {
            // Allow all users (students, faculty, admin) to add questions
            addBtn.style.display = 'block';
        }
        
        // Load non-technical questions (MCQ type) - exclude quiz questions
        const data = await studentAPI.getQuestions({ type: 'mcq', per_page: 200, exclude_quiz_questions: 'true' });
        const questionsDiv = document.getElementById('non-technical-questions-list');
        
        // Check if user is faculty or admin (can delete questions)
        const canDelete = currentUser && (currentUser.role === 'faculty' || currentUser.role === 'admin');
        
        if (data.questions && data.questions.length > 0) {
            questionsDiv.innerHTML = data.questions.map(q => `
                <div class="question-card" onclick="openNonTechQuestion(${q.id})" style="cursor: pointer;">
                    <div class="question-card-content">
                        <div class="question-card-left">
                            <h4 class="question-title-clickable">${q.title}</h4>
                            <p>${q.description || ''}</p>
                            ${q.options ? `<div class="options-preview">Options: ${q.options.join(', ')}</div>` : ''}
                            <small>Marks: ${q.marks || 1}</small>
                        </div>
                        <div class="question-card-right" onclick="event.stopPropagation();">
                            <button class="btn btn-sm btn-open" onclick="openNonTechQuestion(${q.id})">Open</button>
                            ${canDelete ? `
                                <button class="btn btn-sm btn-delete-question" onclick="deleteNonTechQuestion(${q.id}, '${q.title.replace(/'/g, "\\'")}')" title="Delete Question">
                                    🗑️
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            questionsDiv.innerHTML = '<p>No non-technical questions available yet.</p>';
        }
    } catch (error) {
        console.error('Error loading non-technical page:', error);
    }
}

// Non-Technical Question Modal Functions
let ntOptionCount = 2; // Start with A and B

function openNonTechQuestionModal() {
    const modal = document.getElementById('nontech-modal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Reset form
        document.getElementById('nt-question').value = '';
        document.getElementById('nt-marks').value = '1';
        document.getElementById('nt-correct-answer').value = '';
        
        // Reset options container
        const container = document.getElementById('nt-options-container');
        if (container) {
            container.innerHTML = `
                <div class="option-row">
                    <input type="text" class="option-input" placeholder="Option A" data-option="A">
                    <button class="btn-remove-option" onclick="removeOption(this)" style="display: none;">✕</button>
                </div>
                <div class="option-row">
                    <input type="text" class="option-input" placeholder="Option B" data-option="B">
                    <button class="btn-remove-option" onclick="removeOption(this)" style="display: none;">✕</button>
                </div>
            `;
        }
        
        ntOptionCount = 2;
        updateOptionLabels();
        updateCorrectAnswerOptions();
        clearNonTechErrors();
        
        // Close on outside click
        modal.onclick = (e) => {
            if (e.target === modal) closeNonTechQuestionModal();
        };
    }
}

function closeNonTechQuestionModal() {
    const modal = document.getElementById('nontech-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function addOption() {
    if (ntOptionCount >= 10) {
        alert('Maximum 10 options allowed');
        return;
    }
    ntOptionCount++;
    updateOptionsContainer();
}

function removeOption(btn) {
    const container = document.getElementById('nt-options-container');
    const rows = container.querySelectorAll('.option-row');
    if (rows.length <= 2) {
        alert('Minimum 2 options required');
        return;
    }
    btn.closest('.option-row').remove();
    ntOptionCount--;
    updateOptionLabels();
}

function updateOptionsContainer() {
    const container = document.getElementById('nt-options-container');
    if (!container) return;
    
    // Get current number of rows
    let currentRowCount = container.querySelectorAll('.option-row').length;
    
    // Add new rows if needed
    while (currentRowCount < ntOptionCount) {
        const row = document.createElement('div');
        row.className = 'option-row';
        const letter = String.fromCharCode(65 + currentRowCount);
        row.innerHTML = `
            <input type="text" class="option-input" placeholder="Option ${letter}" data-option="${letter}">
            <button class="btn-remove-option" onclick="removeOption(this)">✕</button>
        `;
        container.appendChild(row);
        currentRowCount++;
    }
    
    updateOptionLabels();
    updateCorrectAnswerOptions();
}

function updateOptionLabels() {
    const rows = document.querySelectorAll('#nt-options-container .option-row');
    rows.forEach((row, idx) => {
        const letter = String.fromCharCode(65 + idx);
        const input = row.querySelector('.option-input');
        input.setAttribute('data-option', letter);
        input.placeholder = `Option ${letter}`;
        const removeBtn = row.querySelector('.btn-remove-option');
        removeBtn.style.display = rows.length > 2 ? 'block' : 'none';
    });
    updateCorrectAnswerOptions();
}

function updateCorrectAnswerOptions() {
    const select = document.getElementById('nt-correct-answer');
    if (!select) return;
    
    const currentValue = select.value;
    select.innerHTML = '<option value="">Select correct answer</option>';
    
    const rows = document.querySelectorAll('#nt-options-container .option-row');
    rows.forEach((row, idx) => {
        const letter = String.fromCharCode(65 + idx);
        const option = document.createElement('option');
        option.value = letter;
        option.textContent = letter;
        select.appendChild(option);
    });
    
    if (currentValue && Array.from(select.options).some(opt => opt.value === currentValue)) {
        select.value = currentValue;
    }
}

function clearNonTechErrors() {
    ['question', 'options', 'answer', 'marks'].forEach(field => {
        const el = document.getElementById(`nt-error-${field}`);
        if (el) el.textContent = '';
    });
}

async function submitNonTechQuestion() {
    const question = document.getElementById('nt-question').value.trim();
    const marks = parseInt(document.getElementById('nt-marks').value) || 1;
    const correctAnswer = document.getElementById('nt-correct-answer').value;
    
    // Get options
    const optionInputs = document.querySelectorAll('#nt-options-container .option-input');
    const options = Array.from(optionInputs)
        .map(input => input.value.trim())
        .filter(val => val.length > 0);
    
    let hasError = false;
    clearNonTechErrors();
    
    if (!question) {
        document.getElementById('nt-error-question').textContent = 'Question is required';
        hasError = true;
    }
    if (options.length < 2) {
        document.getElementById('nt-error-options').textContent = 'At least 2 options are required';
        hasError = true;
    }
    if (!correctAnswer) {
        document.getElementById('nt-error-answer').textContent = 'Please select the correct answer';
        hasError = true;
    }
    if (marks < 1) {
        document.getElementById('nt-error-marks').textContent = 'Marks must be at least 1';
        hasError = true;
    }
    
    if (hasError) return;
    
    // Create question payload
    const payload = {
        title: question.substring(0, 100), // Use first 100 chars as title
        description: question,
        type: 'mcq',
        difficulty: 'medium',
        options: options,
        correct_answer: correctAnswer,
        marks: marks
    };
    
    try {
        await facultyAPI.createQuestion(payload);
        closeNonTechQuestionModal();
        await loadNonTechnicalPage();
        alert('Question added successfully!');
    } catch (error) {
        document.getElementById('nt-error-question').textContent = error.message || 'Failed to add question';
    }
}

// Store current question for submission
let currentNonTechQuestion = null;

// Open Non-Technical Question in Modal
async function openNonTechQuestion(questionId) {
    try {
        const data = await studentAPI.getQuestions({ per_page: 1000 });
        const question = data.questions.find(q => q.id === questionId);
        
        if (!question) {
            alert('Question not found');
            return;
        }
        
        // Store question globally
        currentNonTechQuestion = question;
        
        // Create or get modal
        let modal = document.getElementById('nontech-view-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'nontech-view-modal';
            modal.className = 'cp-modal hidden';
            modal.innerHTML = `
                <div class="cp-modal-content" onclick="event.stopPropagation()" style="max-width: 600px;">
                    <div class="cp-modal-header">
                        <div><h3>Question</h3></div>
                        <button class="cp-close" onclick="closeNonTechQuestionView()">✕</button>
                    </div>
                    <div class="cp-modal-body" id="nontech-view-content">
                        <!-- Content will be inserted here -->
                    </div>
                    <div class="cp-modal-footer" id="nontech-view-footer">
                        <!-- Footer buttons will be inserted here -->
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Close on outside click
            modal.onclick = (e) => {
                if (e.target === modal) closeNonTechQuestionView();
            };
        }
        
        // Populate modal content
        const content = document.getElementById('nontech-view-content');
        const footer = document.getElementById('nontech-view-footer');
        
        // Check if question has been answered
        const isAnswered = currentNonTechQuestion.user_answer !== undefined;
        const showResult = isAnswered;
        
        content.innerHTML = `
            <div class="question-view" id="question-view-container">
                <h4>${question.title}</h4>
                ${question.description && question.description.trim() !== question.title.trim() && question.description.trim() !== '' ? `<p class="question-description">${question.description}</p>` : ''}
                <div class="question-options-view">
                    <label>Select your answer:</label>
                    ${question.options ? question.options.map((opt, idx) => {
                        const letter = String.fromCharCode(65 + idx);
                        return `
                            <div class="option-item-view" onclick="selectNonTechOption('view-opt-${questionId}-${idx}')" style="cursor: pointer;">
                                <input type="radio" name="view-question-${questionId}" value="${letter}" id="view-opt-${questionId}-${idx}">
                                <label for="view-opt-${questionId}-${idx}" onclick="event.stopPropagation();" style="cursor: pointer;">
                                    <strong>${letter}.</strong> ${opt}
                                </label>
                            </div>
                        `;
                    }).join('') : ''}
                </div>
                <div class="question-meta">
                    <small>Marks: ${question.marks || 1}</small>
                </div>
                <div id="question-result" style="display: none; margin-top: 20px;"></div>
            </div>
        `;
        
        // Footer buttons
        footer.innerHTML = `
            <button class="btn" onclick="closeNonTechQuestionView()">Close</button>
            <button class="btn btn-primary" onclick="submitNonTechAnswer(${questionId})" id="submit-answer-btn">Submit Answer</button>
        `;
        
        // Show modal
        modal.classList.remove('hidden');
    } catch (error) {
        console.error('Error loading question:', error);
        alert('Failed to load question');
    }
}

function selectNonTechOption(radioId) {
    const radio = document.getElementById(radioId);
    if (radio) {
        radio.checked = true;
        radio.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

function closeNonTechQuestionView() {
    const modal = document.getElementById('nontech-view-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
    currentNonTechQuestion = null;
}

async function deleteNonTechQuestion(questionId, questionTitle) {
    if (!confirm(`Are you sure you want to delete the question "${questionTitle}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        await facultyAPI.deleteQuestion(questionId);
        alert('Question deleted successfully!');
        await loadNonTechnicalPage();
    } catch (error) {
        console.error('Error deleting question:', error);
        alert(`Error deleting question: ${error.message || 'Failed to delete question'}`);
    }
}

async function submitNonTechAnswer(questionId) {
    if (!currentNonTechQuestion) {
        alert('Question not loaded');
        return;
    }
    
    // Get selected answer
    const selectedRadio = document.querySelector(`input[name="view-question-${questionId}"]:checked`);
    if (!selectedRadio) {
        alert('Please select an answer before submitting');
        return;
    }
    
    const userAnswer = selectedRadio.value;
    const correctAnswer = currentNonTechQuestion.correct_answer;
    const isCorrect = userAnswer === correctAnswer;
    const marks = currentNonTechQuestion.marks || 1;
    const obtainedMarks = isCorrect ? marks : 0;
    const score = isCorrect ? 100 : 0;
    
    // Disable all radio buttons
    document.querySelectorAll(`input[name="view-question-${questionId}"]`).forEach(radio => {
        radio.disabled = true;
    });
    
    // Hide submit button
    const submitBtn = document.getElementById('submit-answer-btn');
    if (submitBtn) {
        submitBtn.style.display = 'none';
    }
    
    // Display result with score
    const resultDiv = document.getElementById('question-result');
    if (resultDiv) {
        const correctAnswerText = currentNonTechQuestion.options 
            ? currentNonTechQuestion.options[correctAnswer.charCodeAt(0) - 65] 
            : correctAnswer;
        
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <div class="question-result-card ${isCorrect ? 'result-correct-card' : 'result-wrong-card'}" style="
                background: ${isCorrect ? 'rgba(40, 167, 69, 0.2)' : 'rgba(220, 53, 69, 0.2)'};
                border: 2px solid ${isCorrect ? '#28a745' : '#dc3545'};
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
            ">
                <div style="text-align: center; margin-bottom: 15px;">
                    ${isCorrect 
                        ? '<div style="font-size: 48px; margin-bottom: 10px;">✅</div><h3 style="color: #28a745; margin: 8px 0;">Correct Answer!</h3>' 
                        : '<div style="font-size: 48px; margin-bottom: 10px;">❌</div><h3 style="color: #dc3545; margin: 8px 0;">Wrong Answer</h3>'}
                </div>
                
                <div style="background: rgba(0, 0, 0, 0.3); padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span style="color: #b8b8d1;">Marks Obtained:</span>
                        <strong style="color: #f2f4ff; font-size: 18px;">${obtainedMarks}/${marks}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #b8b8d1;">Score:</span>
                        <strong style="color: ${isCorrect ? '#28a745' : '#dc3545'}; font-size: 24px;">${score}%</strong>
                    </div>
                </div>
                
                <p style="margin: 15px 0 0 0; color: rgba(242, 244, 255, 0.9); text-align: center;">
                    ${isCorrect 
                        ? '🎉 Congratulations! You got it right!' 
                        : `The correct answer is: <strong style="color: #667eea;">${correctAnswer}. ${correctAnswerText}</strong>`}
                </p>
            </div>
        `;
    }
    
    // Store the answer in the question object
    currentNonTechQuestion.user_answer = userAnswer;
    currentNonTechQuestion.is_correct = isCorrect;
}

// Quiz Modal Functions
let quizQuestions = []; // Array to store quiz questions
let quizQuestionCounter = 0;

function openQuizModal() {
    const modal = document.getElementById('quiz-modal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Reset form
        document.getElementById('quiz-modal-title').value = '';
        document.getElementById('quiz-modal-description').value = '';
        document.getElementById('quiz-modal-duration').value = '60';
        quizQuestions = [];
        quizQuestionCounter = 0;
        
        // Clear questions container
        const container = document.getElementById('quiz-questions-container');
        if (container) {
            container.innerHTML = '';
        }
        
        // Add first question by default
        addQuizQuestion();
        
        clearQuizErrors();
        
        // Close on outside click
        modal.onclick = (e) => {
            if (e.target === modal) closeQuizModal();
        };
    }
}

function closeQuizModal() {
    const modal = document.getElementById('quiz-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function addQuizQuestion() {
    const container = document.getElementById('quiz-questions-container');
    if (!container) return;
    
    const questionId = `quiz-q-${quizQuestionCounter++}`;
    const questionData = {
        id: questionId,
        question: '',
        options: ['', ''],
        correctAnswer: '',
        marks: 1
    };
    quizQuestions.push(questionData);
    
    const questionDiv = document.createElement('div');
    questionDiv.className = 'quiz-question-builder';
    questionDiv.id = questionId;
    questionDiv.innerHTML = `
        <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="margin: 0; color: #f2f4ff;">Question ${quizQuestions.length}</h4>
                <button type="button" class="btn-remove-option" onclick="removeQuizQuestion('${questionId}')" ${quizQuestions.length <= 1 ? 'style="display: none;"' : ''}>✕ Remove</button>
            </div>
            
            <label>Question <span class="required-star">★</span></label>
            <textarea class="quiz-q-input" data-field="question" rows="2" placeholder="Enter question text"></textarea>
            <div class="cp-error quiz-q-error" data-field="question"></div>

            <label>Options <span class="required-star">★</span></label>
            <div class="quiz-options-container" data-question-id="${questionId}">
                <div class="option-row">
                    <input type="text" class="option-input quiz-option-input" placeholder="Option A" data-option="A">
                    <button class="btn-remove-option" onclick="removeQuizOption(this, '${questionId}')" style="display: none;">✕</button>
                </div>
                <div class="option-row">
                    <input type="text" class="option-input quiz-option-input" placeholder="Option B" data-option="B">
                    <button class="btn-remove-option" onclick="removeQuizOption(this, '${questionId}')" style="display: none;">✕</button>
                </div>
            </div>
            <button type="button" class="btn btn-sm" onclick="addQuizOption('${questionId}')" style="margin-top: 8px;">+ Add Option</button>
            <div class="cp-error quiz-q-error" data-field="options"></div>

            <label>Correct Answer <span class="required-star">★</span></label>
            <select class="quiz-q-select" data-field="correctAnswer" data-question-id="${questionId}">
                <option value="">Select correct answer</option>
                <option value="A">A</option>
                <option value="B">B</option>
            </select>
            <div class="cp-error quiz-q-error" data-field="correctAnswer"></div>

            <label>Marks <span class="required-star">★</span></label>
            <input type="number" class="quiz-q-input" data-field="marks" min="1" value="1" placeholder="Marks">
            <div class="cp-error quiz-q-error" data-field="marks"></div>
        </div>
    `;
    
    container.appendChild(questionDiv);
    
    // Add event listeners
    setupQuizQuestionListeners(questionId);
    updateQuizCorrectAnswerOptions(questionId);
}

function setupQuizQuestionListeners(questionId) {
    const questionDiv = document.getElementById(questionId);
    if (!questionDiv) return;
    
    // Update question data on input change
    questionDiv.querySelectorAll('.quiz-q-input, .quiz-q-select').forEach(input => {
        input.addEventListener('input', () => updateQuizQuestionData(questionId));
        input.addEventListener('change', () => updateQuizQuestionData(questionId));
    });
    
    // Update options on input
    questionDiv.querySelectorAll('.quiz-option-input').forEach(input => {
        input.addEventListener('input', () => {
            updateQuizQuestionData(questionId);
            updateQuizCorrectAnswerOptions(questionId);
        });
    });
}

function updateQuizQuestionData(questionId) {
    const questionDiv = document.getElementById(questionId);
    if (!questionDiv) return;
    
    const questionData = quizQuestions.find(q => q.id === questionId);
    if (!questionData) return;
    
    // Update question text
    const questionInput = questionDiv.querySelector('[data-field="question"]');
    if (questionInput) questionData.question = questionInput.value.trim();
    
    // Update options
    const optionInputs = questionDiv.querySelectorAll('.quiz-option-input');
    questionData.options = Array.from(optionInputs).map(input => input.value.trim());
    
    // Update correct answer
    const correctAnswerSelect = questionDiv.querySelector('[data-field="correctAnswer"]');
    if (correctAnswerSelect) questionData.correctAnswer = correctAnswerSelect.value;
    
    // Update marks
    const marksInput = questionDiv.querySelector('[data-field="marks"]');
    if (marksInput) questionData.marks = parseInt(marksInput.value) || 1;
}

function addQuizOption(questionId) {
    const container = document.querySelector(`[data-question-id="${questionId}"]`);
    if (!container) return;
    
    const questionData = quizQuestions.find(q => q.id === questionId);
    if (!questionData) return;
    
    if (questionData.options.length >= 10) {
        alert('Maximum 10 options allowed per question');
        return;
    }
    
    const currentOptions = container.querySelectorAll('.option-row');
    const letter = String.fromCharCode(65 + currentOptions.length);
    
    const row = document.createElement('div');
    row.className = 'option-row';
    row.innerHTML = `
        <input type="text" class="option-input quiz-option-input" placeholder="Option ${letter}" data-option="${letter}">
        <button class="btn-remove-option" onclick="removeQuizOption(this, '${questionId}')">✕</button>
    `;
    container.appendChild(row);
    
    questionData.options.push('');
    updateQuizCorrectAnswerOptions(questionId);
    
    // Add event listener
    row.querySelector('.quiz-option-input').addEventListener('input', () => {
        updateQuizQuestionData(questionId);
        updateQuizCorrectAnswerOptions(questionId);
    });
}

function removeQuizOption(btn, questionId) {
    const container = document.querySelector(`[data-question-id="${questionId}"]`);
    if (!container) return;
    
    const rows = container.querySelectorAll('.option-row');
    if (rows.length <= 2) {
        alert('Minimum 2 options required');
        return;
    }
    
    btn.closest('.option-row').remove();
    updateQuizQuestionData(questionId);
    updateQuizOptionLabels(questionId);
    updateQuizCorrectAnswerOptions(questionId);
}

function updateQuizOptionLabels(questionId) {
    const container = document.querySelector(`[data-question-id="${questionId}"]`);
    if (!container) return;
    
    const rows = container.querySelectorAll('.option-row');
    rows.forEach((row, idx) => {
        const letter = String.fromCharCode(65 + idx);
        const input = row.querySelector('.quiz-option-input');
        if (input) {
            input.setAttribute('data-option', letter);
            input.placeholder = `Option ${letter}`;
        }
        const removeBtn = row.querySelector('.btn-remove-option');
        if (removeBtn) {
            removeBtn.style.display = rows.length > 2 ? 'block' : 'none';
        }
    });
}

function updateQuizCorrectAnswerOptions(questionId) {
    const questionDiv = document.getElementById(questionId);
    if (!questionDiv) return;
    
    const select = questionDiv.querySelector('[data-field="correctAnswer"]');
    if (!select) return;
    
    const container = document.querySelector(`[data-question-id="${questionId}"]`);
    if (!container) return;
    
    const currentValue = select.value;
    const rows = container.querySelectorAll('.option-row');
    
    select.innerHTML = '<option value="">Select correct answer</option>';
    rows.forEach((row, idx) => {
        const letter = String.fromCharCode(65 + idx);
        const option = document.createElement('option');
        option.value = letter;
        option.textContent = letter;
        select.appendChild(option);
    });
    
    if (currentValue && Array.from(select.options).some(opt => opt.value === currentValue)) {
        select.value = currentValue;
    }
}

function removeQuizQuestion(questionId) {
    if (quizQuestions.length <= 1) {
        alert('At least one question is required');
        return;
    }
    
    const questionDiv = document.getElementById(questionId);
    if (questionDiv) {
        questionDiv.remove();
    }
    
    quizQuestions = quizQuestions.filter(q => q.id !== questionId);
    
    // Renumber questions
    const container = document.getElementById('quiz-questions-container');
    if (container) {
        const questions = container.querySelectorAll('.quiz-question-builder');
        questions.forEach((q, idx) => {
            const title = q.querySelector('h4');
            if (title) title.textContent = `Question ${idx + 1}`;
        });
    }
}

function clearQuizErrors() {
    document.getElementById('quiz-error-title').textContent = '';
    document.getElementById('quiz-error-questions').textContent = '';
    document.querySelectorAll('.quiz-q-error').forEach(el => el.textContent = '');
}

async function submitQuizCreation() {
    const title = document.getElementById('quiz-modal-title').value.trim();
    const description = document.getElementById('quiz-modal-description').value.trim();
    const duration = parseInt(document.getElementById('quiz-modal-duration').value) || 60;
    
    let hasError = false;
    clearQuizErrors();
    
    if (!title) {
        document.getElementById('quiz-error-title').textContent = 'Quiz title is required';
        hasError = true;
    }
    
    // Validate all questions
    quizQuestions.forEach((qData, idx) => {
        const questionDiv = document.getElementById(qData.id);
        if (!questionDiv) return;
        
        if (!qData.question) {
            const errorEl = questionDiv.querySelector('[data-field="question"].quiz-q-error');
            if (errorEl) errorEl.textContent = 'Question is required';
            hasError = true;
        }
        
        const validOptions = qData.options.filter(opt => opt.trim().length > 0);
        if (validOptions.length < 2) {
            const errorEl = questionDiv.querySelector('[data-field="options"].quiz-q-error');
            if (errorEl) errorEl.textContent = 'At least 2 options are required';
            hasError = true;
        }
        
        if (!qData.correctAnswer) {
            const errorEl = questionDiv.querySelector('[data-field="correctAnswer"].quiz-q-error');
            if (errorEl) errorEl.textContent = 'Please select the correct answer';
            hasError = true;
        }
        
        if (qData.marks < 1) {
            const errorEl = questionDiv.querySelector('[data-field="marks"].quiz-q-error');
            if (errorEl) errorEl.textContent = 'Marks must be at least 1';
            hasError = true;
        }
    });
    
    if (quizQuestions.length === 0) {
        document.getElementById('quiz-error-questions').textContent = 'At least one question is required';
        hasError = true;
    }
    
    if (hasError) return;
    
    try {
        // First, create all questions
        const questionIds = [];
        for (let i = 0; i < quizQuestions.length; i++) {
            const qData = quizQuestions[i];
            const validOptions = qData.options.filter(opt => opt.trim().length > 0);
            
            if (validOptions.length < 2) {
                throw new Error(`Question ${i + 1} must have at least 2 options`);
            }
            
            if (!qData.correctAnswer || qData.correctAnswer.trim() === '') {
                throw new Error(`Question ${i + 1} must have a correct answer`);
            }
            
            const questionPayload = {
                title: qData.question.substring(0, 100),
                description: qData.question,
                type: 'mcq',
                difficulty: 'medium',
                options: validOptions,
                correct_answer: qData.correctAnswer,
                marks: qData.marks || 1
            };
            
            console.log(`Creating question ${i + 1}:`, questionPayload);
            const result = await facultyAPI.createQuestion(questionPayload);
            console.log(`Question ${i + 1} created:`, result);
            
            if (!result || !result.question || !result.question.id) {
                throw new Error(`Failed to create question ${i + 1}: Invalid response from server`);
            }
            
            questionIds.push(result.question.id);
        }
        
        if (questionIds.length === 0) {
            throw new Error('No questions were created');
        }
        
        // Create a map of question IDs to their marks
        const questionMarksMap = {};
        quizQuestions.forEach((qData, idx) => {
            if (questionIds[idx]) {
                questionMarksMap[questionIds[idx]] = qData.marks || 1;
            }
        });
        
        // Calculate total marks
        const totalMarks = quizQuestions.reduce((sum, q) => sum + (q.marks || 1), 0);
        
        // Then create the quiz with these questions
        const quizPayload = {
            title: title,
            description: description,
            duration_minutes: parseInt(duration) || 15,
            question_ids: questionIds,
            question_marks: questionMarksMap,
            total_marks: totalMarks,
            marks_per_question: 1  // Fallback default
        };
        
        console.log('Creating quiz with payload:', quizPayload);
        const quizResult = await facultyAPI.createQuiz(quizPayload);
        console.log('Quiz created:', quizResult);
        
        closeQuizModal();
        await loadQuizzesPage();
        alert('Quiz created successfully!');
    } catch (error) {
        console.error('Quiz creation error:', error);
        const errorMsg = error.message || 'Failed to create quiz';
        const errorEl = document.getElementById('quiz-error-title');
        if (errorEl) {
            errorEl.textContent = errorMsg;
        }
        alert(`Error creating quiz: ${errorMsg}\n\nPlease check:\n1. Backend server is running\n2. Database connection is working\n3. All required fields are filled`);
    }
}

// Quiz Page
let deleteMode = false;
let selectedQuizIds = new Set();

async function loadQuizzesPage() {
    try {
        // Reset delete mode
        deleteMode = false;
        selectedQuizIds.clear();
        
        // Show quiz list and hide quiz taking view
        const quizzesList = document.getElementById('quizzes-list');
        const quizTaking = document.getElementById('quiz-taking');
        if (quizzesList) quizzesList.style.display = 'block';
        if (quizTaking) quizTaking.style.display = 'none';
        
        // Check user role for +Add button visibility
        const addBtn = document.getElementById('add-quiz-btn');
        if (addBtn) {
            // Hide "Add Quiz" button for students - they can only attempt quizzes
            if (currentUser && currentUser.role === 'student') {
                addBtn.style.display = 'none';
            } else {
                // Show for faculty and admin
                addBtn.style.display = 'block';
            }
        }
        
        const data = await quizAPI.listQuizzes({ is_active: 'true' });
        const quizzesDiv = document.getElementById('quizzes-list');
        
        // Check if user is faculty or admin (can delete quizzes)
        const canDelete = currentUser && (currentUser.role === 'faculty' || currentUser.role === 'admin');
        
        // Update delete button visibility - only show in quiz list view
        const deleteBtn = document.getElementById('delete-mode-btn');
        if (deleteBtn) {
            deleteBtn.style.display = canDelete ? 'block' : 'none';
        }
        
        // Hide selection controls initially
        updateDeleteModeUI();
        
        if (data.quizzes && data.quizzes.length > 0) {
            renderQuizzesList(data.quizzes, canDelete);
        } else {
            quizzesDiv.innerHTML = '<p>No quizzes available yet.</p>';
        }
    } catch (error) {
        console.error('Error loading quizzes:', error);
    }
}

function renderQuizzesList(quizzes, canDelete) {
    const quizzesDiv = document.getElementById('quizzes-list');
    if (!quizzesDiv) return;
    
    quizzesDiv.innerHTML = quizzes.map(q => `
        <div class="quiz-item ${deleteMode ? 'delete-mode' : ''}" data-quiz-id="${q.id}">
            ${deleteMode && canDelete ? `
                <input type="checkbox" class="quiz-select-checkbox" 
                       onchange="toggleQuizSelection(${q.id})" 
                       ${selectedQuizIds.has(q.id) ? 'checked' : ''}>
            ` : ''}
            <div class="quiz-item-content" onclick="${deleteMode ? 'event.stopPropagation();' : `openQuiz(${q.id})`}">
                <h4 class="quiz-title-clickable">${q.title}</h4>
                <p>${q.description || ''}</p>
                <small>Duration: ${q.duration_minutes} minutes | Total Marks: ${q.total_marks}</small>
            </div>
            ${!deleteMode ? `
                <button class="btn-open-quiz" onclick="event.stopPropagation(); openQuiz(${q.id})" title="Open Quiz">
                    Open
                </button>
            ` : ''}
        </div>
    `).join('');
}

async function toggleDeleteMode() {
    deleteMode = !deleteMode;
    selectedQuizIds.clear();
    updateDeleteModeUI();
    
    try {
        const data = await quizAPI.listQuizzes({ is_active: 'true' });
        const canDelete = currentUser && (currentUser.role === 'faculty' || currentUser.role === 'admin');
        renderQuizzesList(data.quizzes || [], canDelete);
    } catch (err) {
        console.error('Error reloading quizzes:', err);
    }
}

function toggleQuizSelection(quizId) {
    if (selectedQuizIds.has(quizId)) {
        selectedQuizIds.delete(quizId);
    } else {
        selectedQuizIds.add(quizId);
    }
    updateDeleteButtonState();
    
    // Update checkbox state visually
    const checkbox = document.querySelector(`.quiz-select-checkbox[onchange*="${quizId}"]`);
    if (checkbox) {
        checkbox.checked = selectedQuizIds.has(quizId);
    }
}

function updateDeleteModeUI() {
    const deleteBtn = document.getElementById('delete-mode-btn');
    const cancelBtn = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    
    if (deleteMode) {
        if (deleteBtn) deleteBtn.textContent = 'Cancel';
        if (cancelBtn) cancelBtn.style.display = 'none';
        if (confirmDeleteBtn) confirmDeleteBtn.style.display = selectedQuizIds.size > 0 ? 'block' : 'none';
    } else {
        if (deleteBtn) deleteBtn.textContent = 'Delete';
        if (cancelBtn) cancelBtn.style.display = 'none';
        if (confirmDeleteBtn) confirmDeleteBtn.style.display = 'none';
    }
}

function updateDeleteButtonState() {
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.style.display = selectedQuizIds.size > 0 ? 'block' : 'none';
        confirmDeleteBtn.textContent = `Delete Selected (${selectedQuizIds.size})`;
    }
}

function cancelDeleteMode() {
    deleteMode = false;
    selectedQuizIds.clear();
    updateDeleteModeUI();
    loadQuizzesPage();
}

async function confirmDeleteSelected() {
    if (selectedQuizIds.size === 0) {
        alert('Please select at least one quiz to delete');
        return;
    }
    
    const count = selectedQuizIds.size;
    if (!confirm(`Are you sure you want to delete ${count} quiz${count > 1 ? 'es' : ''}?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        const deletePromises = Array.from(selectedQuizIds).map(quizId => 
            facultyAPI.deleteQuiz(quizId).catch(err => {
                console.error(`Error deleting quiz ${quizId}:`, err);
                return { error: true, quizId };
            })
        );
        
        const results = await Promise.all(deletePromises);
        const errors = results.filter(r => r && r.error);
        
        if (errors.length > 0) {
            alert(`Deleted ${count - errors.length} quiz${count - errors.length > 1 ? 'es' : ''}, but ${errors.length} failed.`);
        } else {
            alert(`Successfully deleted ${count} quiz${count > 1 ? 'es' : ''}!`);
        }
        
        cancelDeleteMode();
    } catch (error) {
        console.error('Error deleting quizzes:', error);
        alert(`Error deleting quizzes: ${error.message || 'Failed to delete quizzes'}`);
    }
}


function selectQuizOption(radioId) {
    const radio = document.getElementById(radioId);
    if (radio) {
        radio.checked = true;
        // Trigger change event to ensure form state is updated
        radio.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

function openQuiz(quizId) {
    takeQuiz(quizId);
}

async function takeQuiz(quizId) {
    try {
        const data = await quizAPI.getQuiz(quizId);
        currentQuiz = data.quiz;
        currentQuizId = quizId;
        
        // Hide delete button when taking quiz
        const deleteBtn = document.getElementById('delete-mode-btn');
        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        if (deleteBtn) deleteBtn.style.display = 'none';
        if (confirmDeleteBtn) confirmDeleteBtn.style.display = 'none';
        
        document.getElementById('quizzes-list').style.display = 'none';
        document.getElementById('quiz-taking').style.display = 'block';
        document.getElementById('quiz-results').style.display = 'none';
        document.getElementById('quiz-title').textContent = currentQuiz.title;
        
        const questionsDiv = document.getElementById('quiz-questions');
        questionsDiv.innerHTML = currentQuiz.questions.map((qq, idx) => {
            const q = qq.question;
            let html = `<div class="quiz-question" data-question-id="${q.id}">
                <h4>Question ${idx + 1}: ${q.title}</h4>`;
            
            // Only show description if it's different from title and not empty
            if (q.description && q.description.trim() !== q.title.trim() && q.description.trim() !== '') {
                html += `<p>${q.description}</p>`;
            }
            
            if (q.type === 'mcq') {
                html += q.options.map((opt, i) => `
                    <div class="quiz-option" onclick="selectQuizOption('q${q.id}_${i}')">
                        <input type="radio" name="q${q.id}" value="${String.fromCharCode(65 + i)}" id="q${q.id}_${i}">
                        <label for="q${q.id}_${i}" onclick="event.stopPropagation();">${opt}</label>
                    </div>
                `).join('');
            } else if (q.type === 'fill_blank') {
                html += q.blanks.map(blank => `
                    <div>
                        <label>${blank.text}</label>
                        <input type="text" name="q${q.id}_${blank.id}" placeholder="Your answer">
                    </div>
                `).join('');
            }
            
            html += '</div>';
            return html;
        }).join('');
    } catch (error) {
        console.error('Error loading quiz:', error);
    }
}

async function submitQuiz() {
    if (!currentQuiz) return;
    
    const answers = {};
    const questionElements = document.querySelectorAll('.quiz-question');
    
    questionElements.forEach(qDiv => {
        const radios = qDiv.querySelectorAll('input[type="radio"]:checked');
        const textInputs = qDiv.querySelectorAll('input[type="text"]');
        
        if (radios.length > 0) {
            const qId = radios[0].name.replace('q', '');
            answers[qId] = radios[0].value;
        } else if (textInputs.length > 0) {
            const qId = textInputs[0].name.split('_')[0].replace('q', '');
            if (!answers[qId]) answers[qId] = {};
            textInputs.forEach(input => {
                const blankId = input.name.split('_')[1];
                answers[qId][blankId] = input.value;
            });
        }
    });
    
    try {
        const result = await quizAPI.attemptQuiz(currentQuiz.id, answers);
        
        // Display results with ✅/❌
        displayQuizResults(result, currentQuiz);
        
        // Refresh Placement Readiness Score after quiz submission
        // Use setTimeout to ensure the backend has processed the quiz attempt
        setTimeout(() => {
            if (typeof loadPlacementReadinessScore === 'function') {
                loadPlacementReadinessScore();
            }
        }, 1000);
        
        loadDashboard();
        // Load notification badge count (only if logged in)
        if (authToken && currentUser) {
            loadNotificationBadge();
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function displayQuizResults(result, quiz) {
    const resultsDiv = document.getElementById('quiz-results');
    const questionsDiv = document.getElementById('quiz-questions');
    
    // Hide submit button
    const submitBtn = document.querySelector('#quiz-taking button[onclick="submitQuiz()"]');
    if (submitBtn) submitBtn.style.display = 'none';
    
    // Get results from backend
    const questionResults = result.question_results || {};
    const obtainedMarks = result.obtained_marks || 0;
    const totalMarks = result.total_marks || 0;
    const score = result.score || 0;
    
    // Update each question with result indicator
    quiz.questions.forEach((qq, idx) => {
        const q = qq.question;
        const questionDiv = questionsDiv.querySelector(`[data-question-id="${q.id}"]`);
        if (!questionDiv) return;
        
        // Get result for this question
        const qResult = questionResults[q.id];
        if (!qResult) return;
        
        const isCorrect = qResult.is_correct;
        const userAnswer = qResult.user_answer || '';
        const correctAnswer = qResult.correct_answer || q.correct_answer || '';
        
        // Format correct answer for display (convert A, B, C to option text if needed)
        let correctAnswerText = correctAnswer;
        if (q.type === 'mcq' && q.options && q.options.length > 0) {
            const answerIndex = correctAnswer.charCodeAt(0) - 65; // A=0, B=1, C=2, etc.
            if (answerIndex >= 0 && answerIndex < q.options.length) {
                correctAnswerText = `${correctAnswer} - ${q.options[answerIndex]}`;
            }
        }
        
        // Add result indicator
        const indicator = document.createElement('div');
        indicator.className = 'quiz-result-indicator';
        indicator.style.marginTop = '12px';
        indicator.style.padding = '10px';
        indicator.style.borderRadius = '5px';
        indicator.style.backgroundColor = isCorrect ? 'rgba(40, 167, 69, 0.2)' : 'rgba(220, 53, 69, 0.2)';
        indicator.style.border = `1px solid ${isCorrect ? '#28a745' : '#dc3545'}`;
        
        indicator.innerHTML = isCorrect 
            ? `<span class="result-correct" style="color: #28a745; font-weight: bold;">✅ Correct</span><br><small style="color: #b8b8d1;">Marks: ${qResult.marks_obtained}/${qResult.marks_total}</small>` 
            : `<span class="result-wrong" style="color: #dc3545; font-weight: bold;">❌ Wrong</span><br><small style="color: #b8b8d1;">Your answer: ${userAnswer || 'Not answered'}</small><br><small style="color: #b8b8d1;">Correct answer: ${correctAnswerText}</small><br><small style="color: #b8b8d1;">Marks: ${qResult.marks_obtained}/${qResult.marks_total}</small>`;
        
        questionDiv.appendChild(indicator);
        
        // Disable inputs
        questionDiv.querySelectorAll('input').forEach(input => {
            input.disabled = true;
        });
    });
    
    // Show results summary
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = `
        <h3 style="color: #f2f4ff; margin-bottom: 15px;">Quiz Results</h3>
        <div style="display: flex; gap: 20px; flex-wrap: wrap;">
            <div style="background: rgba(102, 126, 234, 0.2); padding: 15px; border-radius: 5px; border: 1px solid #667eea;">
                <p style="color: #b8b8d1; margin: 0 0 5px 0; font-size: 14px;">Marks Obtained</p>
                <p style="color: #f2f4ff; margin: 0; font-size: 24px; font-weight: bold;">${obtainedMarks}/${totalMarks}</p>
            </div>
            <div style="background: rgba(102, 126, 234, 0.2); padding: 15px; border-radius: 5px; border: 1px solid #667eea;">
                <p style="color: #b8b8d1; margin: 0 0 5px 0; font-size: 14px;">Score</p>
                <p style="color: #f2f4ff; margin: 0; font-size: 24px; font-weight: bold;">${score.toFixed(1)}%</p>
            </div>
        </div>
    `;
}

// Companies Page
async function loadCompanies() {
    try {
        const data = await companyAPI.listCompanies();
        companies = data.companies;
    } catch (error) {
        console.error('Error loading companies:', error);
    }
}

let companyDeleteMode = false;
let selectedCompanyIds = new Set();

async function loadCompaniesPage() {
    await loadCompanies();
    
    // Reset delete mode
    companyDeleteMode = false;
    selectedCompanyIds.clear();
    
    // Check user role and show delete button if faculty/admin
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const canDelete = currentUser && (currentUser.role === 'faculty' || currentUser.role === 'admin');
    const deleteBtn = document.getElementById('delete-company-btn');
    if (deleteBtn && canDelete) {
        deleteBtn.style.display = 'block';
    } else if (deleteBtn) {
        deleteBtn.style.display = 'none';
    }
    
    updateCompanyDeleteModeUI();
    renderCompanies();
}

function renderCompanies() {
    const companiesDiv = document.getElementById('companies-list');
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const canDelete = currentUser && (currentUser.role === 'faculty' || currentUser.role === 'admin');
    
    companiesDiv.innerHTML = companies.map(c => `
        <div class="company-card ${companyDeleteMode ? 'delete-mode' : ''}" data-company-id="${c.id}" 
             ${!companyDeleteMode ? `onclick="openCompanyQuestions(${c.id})" style="cursor: pointer;"` : ''}>
            ${companyDeleteMode && canDelete ? `
                <input type="checkbox" class="company-select-checkbox" 
                       onchange="toggleCompanySelection(${c.id})" 
                       ${selectedCompanyIds.has(c.id) ? 'checked' : ''}
                       style="margin-right: 15px;"
                       onclick="event.stopPropagation();">
            ` : ''}
            <div class="company-card-content">
                <h3>${c.name}</h3>
                <p>${c.description || ''}</p>
            </div>
        </div>
    `).join('');
}

async function openCompanyQuestions(companyId) {
    try {
        // Navigate to Code Practice page
        showCodePractice();
        
        // Filter questions by company
        const data = await studentAPI.getQuestions({ type: 'coding', company_id: companyId, per_page: 200 });
        const submissionsRes = await codingAPI.getSubmissions();
        
        const solvedIds = new Set(
            (submissionsRes.submissions || [])
                .filter(s => s.status === 'accepted')
                .map(s => s.question_id)
        );
        
        codingQuestions = data.questions.map(q => ({
            ...q,
            status: solvedIds.has(q.id) ? 'solved' : 'unsolved',
            company_name: q.company_name || 'General',
            tags: q.tags || []
        }));
        
        // Set filter to show only this company's questions
        codingFilter = 'all';
        codingSearch = '';
        renderCodingQuestions();
        
        // Show success message
        const company = companies.find(c => c.id === companyId);
        if (company) {
            console.log(`Loaded ${codingQuestions.length} questions for ${company.name}`);
        }
    } catch (error) {
        console.error('Error loading company questions:', error);
        alert(`Error loading questions: ${error.message || 'Failed to load questions'}`);
    }
}

function toggleCompanyDeleteMode() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const canDelete = currentUser && (currentUser.role === 'faculty' || currentUser.role === 'admin');
    
    if (!canDelete) {
        alert('You do not have permission to delete companies');
        return;
    }
    
    companyDeleteMode = !companyDeleteMode;
    selectedCompanyIds.clear();
    updateCompanyDeleteModeUI();
    renderCompanies();
}

function updateCompanyDeleteModeUI() {
    const deleteBtn = document.getElementById('delete-company-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-company-btn');
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const canDelete = currentUser && (currentUser.role === 'faculty' || currentUser.role === 'admin');
    
    if (deleteBtn) {
        if (canDelete) {
            deleteBtn.style.display = 'block';
            if (companyDeleteMode) {
                deleteBtn.textContent = '✕ Cancel';
                deleteBtn.classList.add('btn-secondary');
                deleteBtn.classList.remove('btn-delete-quiz');
            } else {
                deleteBtn.textContent = '🗑️ Delete';
                deleteBtn.classList.remove('btn-secondary');
                deleteBtn.classList.add('btn-delete-quiz');
            }
        } else {
            deleteBtn.style.display = 'none';
        }
    }
    
    if (confirmDeleteBtn) {
        confirmDeleteBtn.style.display = companyDeleteMode && selectedCompanyIds.size > 0 ? 'block' : 'none';
        confirmDeleteBtn.textContent = `Delete Selected (${selectedCompanyIds.size})`;
    }
}

function toggleCompanySelection(companyId) {
    if (selectedCompanyIds.has(companyId)) {
        selectedCompanyIds.delete(companyId);
    } else {
        selectedCompanyIds.add(companyId);
    }
    updateCompanyDeleteModeUI();
}

function cancelCompanyDeleteMode() {
    companyDeleteMode = false;
    selectedCompanyIds.clear();
    updateCompanyDeleteModeUI();
    renderCompanies();
}

async function confirmDeleteSelectedCompanies() {
    if (selectedCompanyIds.size === 0) {
        alert('Please select at least one company to delete');
        return;
    }
    
    const count = selectedCompanyIds.size;
    if (!confirm(`Are you sure you want to delete ${count} compan${count > 1 ? 'ies' : 'y'}?\n\nThis will also delete all related posts, questions, and resources.\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        const deletePromises = Array.from(selectedCompanyIds).map(async (companyId) => {
            try {
                const result = await companyAPI.deleteCompany(companyId);
                return { success: true, companyId, result };
            } catch (err) {
                console.error(`Error deleting company ${companyId}:`, err);
                const errorMessage = err.message || (err.error || 'Unknown error');
                return { error: true, companyId, message: errorMessage };
            }
        });
        
        const results = await Promise.all(deletePromises);
        const errors = results.filter(r => r && r.error);
        const successes = results.filter(r => r && r.success);
        
        if (errors.length > 0) {
            const errorDetails = errors.map(e => `Company ID ${e.companyId}: ${e.message}`).join('\n');
            alert(`Deleted ${successes.length} compan${successes.length > 1 ? 'ies' : 'y'}, but ${errors.length} failed:\n\n${errorDetails}`);
        } else {
            alert(`Successfully deleted ${count} compan${count > 1 ? 'ies' : 'y'}!`);
        }
        
        cancelCompanyDeleteMode();
        await loadCompanies();
        renderCompanies();
    } catch (error) {
        console.error('Error deleting companies:', error);
        alert(`Error deleting companies: ${error.message || 'Failed to delete companies'}`);
    }
}

async function loadPosts() {
    try {
        const data = await postsAPI.getPosts();
        const postsDiv = document.getElementById('posts-list');
        
        if (!data.posts || data.posts.length === 0) {
            postsDiv.innerHTML = '<p style="text-align: center; color: rgba(242, 244, 255, 0.6); padding: 20px;">No posts yet. Be the first to share your interview experience!</p>';
            return;
        }
        
        postsDiv.innerHTML = `
            <h3 style="margin-bottom: 20px; color: #f2f4ff;">Recent Posts</h3>
            ${data.posts.map(post => `
                <div class="post-card">
                    <div class="post-header">
                        <h4>${post.title}</h4>
                        <span class="post-type-badge">${post.post_type}</span>
                    </div>
                    <div class="post-meta">
                        <span>${post.company_name || 'Unknown Company'}</span>
                        <span>•</span>
                        <span>${post.user_name || 'Anonymous'}</span>
                        <span>•</span>
                        <span>${new Date(post.created_at).toLocaleDateString()}</span>
                    </div>
                    ${post.file_path ? `
                        <div class="post-file-attachment">
                            <a href="${getApiBaseUrl()}/posts/${post.id}/file" target="_blank" class="file-link">
                                📎 View ${post.file_type ? post.file_type.toUpperCase() : 'File'}
                            </a>
                        </div>
                    ` : ''}
                    ${post.content ? `<div class="post-content">${post.content}</div>` : ''}
                    ${post.tags ? `<div class="post-tags">${post.tags.split(',').map(tag => `<span class="tag">${tag.trim()}</span>`).join('')}</div>` : ''}
                </div>
            `).join('')}
        `;
    } catch (error) {
        console.error('Error loading posts:', error);
        const postsDiv = document.getElementById('posts-list');
        postsDiv.innerHTML = '<p style="color: #ff6b6b;">Error loading posts. Please try again later.</p>';
    }
}

function openPostModal() {
    const modal = document.getElementById('post-modal');
    modal.style.display = 'block';
}

function toggleContentInput() {
    const contentType = document.getElementById('post-content-type').value;
    const textGroup = document.getElementById('text-content-group');
    const fileGroup = document.getElementById('file-content-group');
    const textContent = document.getElementById('post-content');
    const fileInput = document.getElementById('post-file');
    
    if (contentType === 'file') {
        textGroup.style.display = 'none';
        fileGroup.style.display = 'block';
        textContent.removeAttribute('required');
        fileInput.setAttribute('required', 'required');
    } else {
        textGroup.style.display = 'block';
        fileGroup.style.display = 'none';
        textContent.setAttribute('required', 'required');
        fileInput.removeAttribute('required');
    }
}

function closePostModal() {
    const modal = document.getElementById('post-modal');
    const form = document.getElementById('post-form');
    const fileDisplay = document.getElementById('file-name-display');
    const contentTypeSelect = document.getElementById('post-content-type');
    
    modal.style.display = 'none';
    form.reset();
    
    // Reset content type to text
    if (contentTypeSelect) {
        contentTypeSelect.value = 'text';
    }
    
    if (fileDisplay) {
        fileDisplay.style.display = 'none';
        fileDisplay.textContent = '';
    }
    
    // Reset to text content by default
    toggleContentInput();
}

// Handle file input change
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('post-file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileDisplay = document.getElementById('file-name-display');
            if (e.target.files && e.target.files.length > 0) {
                const fileName = e.target.files[0].name;
                const fileSize = (e.target.files[0].size / (1024 * 1024)).toFixed(2);
                fileDisplay.textContent = `Selected: ${fileName} (${fileSize} MB)`;
                fileDisplay.style.display = 'block';
            } else {
                fileDisplay.style.display = 'none';
                fileDisplay.textContent = '';
            }
        });
    }
    
    // Handle post form submission
    const postForm = document.getElementById('post-form');
    if (postForm) {
        postForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(postForm);
            const contentType = formData.get('content_type');
            
            // Validate based on content type
            if (contentType === 'text') {
                const content = formData.get('content');
                if (!content || !content.trim()) {
                    alert('Please enter content');
                    return;
                }
            } else if (contentType === 'file') {
                const file = formData.get('file');
                if (!file || file.size === 0) {
                    alert('Please select a file to upload');
                    return;
                }
                // Check file size (16MB max)
                if (file.size > 16 * 1024 * 1024) {
                    alert('File size exceeds 16MB limit');
                    return;
                }
            }
            
            try {
                await postsAPI.createPost(formData);
                alert('Post created successfully!');
                closePostModal();
            } catch (error) {
                alert(`Error creating post: ${error.message}`);
            }
        });
    }
});

async function loadCompanyQuestions(companyId) {
    try {
        const data = await studentAPI.getQuestions({ company_id: companyId });
        const questionsDiv = document.getElementById('company-questions');
        
        questionsDiv.innerHTML = `
            <h3>Questions</h3>
            ${data.questions.map(q => `
                <div class="question-item" onclick="loadQuestion(${q.id})">
                    <h4>${q.title}</h4>
                    <p>${q.type} - ${q.difficulty}</p>
                </div>
            `).join('')}
        `;
    } catch (error) {
        console.error('Error loading company questions:', error);
    }
}

// Resources Page
async function loadResourcesPage() {
    try {
        const data = await resourcesAPI.getResources();
        const resourcesDiv = document.getElementById('resources-list');
        
        
        if (!data.resources || data.resources.length === 0) {
            resourcesDiv.innerHTML = '<p style="text-align: center; color: rgba(242, 244, 255, 0.6); padding: 40px;">No resources uploaded yet.</p>';
            return;
        }
        
        resourcesDiv.innerHTML = data.resources.map(r => {
            // Check if resource has a file (file_path exists and is not empty/null)
            const hasFile = r.file_path && r.file_path.trim() !== '' && r.file_path !== null && r.file_path !== 'None';
            const uploadDate = r.created_at ? new Date(r.created_at).toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            }) : 'N/A';
            
            return `
            <div class="resource-item">
                <div class="resource-content">
                    <div class="resource-header">
                        <h4>📄 ${r.title || 'Untitled'}</h4>
                        <span class="resource-type-badge">📎 ${r.type ? r.type.toUpperCase() : 'PDF'}</span>
                    </div>
                    ${r.description ? `<p class="resource-description">📝 ${r.description}</p>` : ''}
                    <div class="resource-meta">
                        <small>🕒 Uploaded: ${uploadDate}</small>
                    </div>
                    ${hasFile ? `
                        <div class="resource-actions">
                            <button onclick="viewResource(${r.id})" class="btn btn-sm btn-primary">🔗 View PDF</button>
                            <button onclick="downloadResource(${r.id})" class="btn btn-sm btn-secondary">⬇️ Download</button>
                        </div>
                    ` : `<div class="resource-no-file">⚠️ No file attached</div>`}
                </div>
                <button onclick="deleteResource(${r.id})" class="btn btn-sm btn-delete">🗑️ Delete</button>
            </div>
        `;
        }).join('');
    } catch (error) {
        console.error('Error loading resources:', error);
        const resourcesDiv = document.getElementById('resources-list');
        resourcesDiv.innerHTML = '<p style="color: #e74c3c;">Error loading resources. Please try again.</p>';
    }
}

function openResourceUploadForm() {
    const form = document.getElementById('resource-upload-form');
    const addBtn = document.getElementById('add-resource-btn');
    if (form) {
        form.style.display = 'block';
        if (addBtn) addBtn.style.display = 'none';
    }
}

function closeResourceUploadForm() {
    const form = document.getElementById('resource-upload-form');
    const addBtn = document.getElementById('add-resource-btn');
    if (form) {
        form.style.display = 'none';
        // Clear form fields
        document.getElementById('resource-title').value = '';
        document.getElementById('resource-description').value = '';
        document.getElementById('resource-type').value = 'pdf';
        document.getElementById('resource-file').value = '';
    }
    if (addBtn) addBtn.style.display = 'inline-block';
}

async function uploadResource() {
    const title = document.getElementById('resource-title').value.trim();
    const description = document.getElementById('resource-description').value.trim();
    const type = document.getElementById('resource-type').value;
    const file = document.getElementById('resource-file').files[0];
    
    if (!title) {
        alert('Please enter a title');
        return;
    }
    
    if (!file && type === 'pdf') {
        alert('Please select a file to upload');
        return;
    }
    
    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('type', type);
    if (file) formData.append('file', file);
    
    try {
        await resourcesAPI.uploadResource(formData);
        alert('Resource uploaded successfully!');
        
        // Clear form and close it
        document.getElementById('resource-title').value = '';
        document.getElementById('resource-description').value = '';
        document.getElementById('resource-type').value = 'pdf';
        document.getElementById('resource-file').value = '';
        
        // Close upload form
        closeResourceUploadForm();
        
        // Reload resources list
        await loadResourcesPage();
    } catch (error) {
        alert(`Error: ${error.message || 'Failed to upload resource'}`);
    }
}

async function viewResource(resourceId) {
    // Open PDF in new tab with authentication
    const url = `${API_BASE_URL}/resources/${resourceId}/download`;
    const token = localStorage.getItem('authToken');
    
    // Create a temporary link with Authorization header
    // Since we can't set headers on direct links, we'll fetch and open as blob
    try {
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load PDF');
        }
        
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        window.open(blobUrl, '_blank');
    } catch (error) {
        alert(`Error: ${error.message || 'Failed to view PDF'}`);
    }
}

async function downloadResource(resourceId) {
    // Download PDF with authentication
    const url = `${API_BASE_URL}/resources/${resourceId}/download`;
    const token = localStorage.getItem('authToken');
    
    try {
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to download PDF');
        }
        
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `resource_${resourceId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
    } catch (error) {
        alert(`Error: ${error.message || 'Failed to download PDF'}`);
    }
}

async function deleteResource(resourceId) {
    if (!confirm('Are you sure you want to delete this resource?')) return;
    
    try {
        await resourcesAPI.deleteResource(resourceId);
        loadResourcesPage();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Leaderboard
async function loadLeaderboard() {
    try {
        const data = await leaderboardAPI.getTopUsers(100);
        const tableDiv = document.getElementById('leaderboard-table');
        
        tableDiv.innerHTML = `
            <div class="leaderboard-row header">
                <div>Rank</div>
                <div>Username</div>
                <div>Total Score</div>
                <div>Coding Score</div>
                <div>Quiz Score</div>
                <div>Accuracy</div>
            </div>
            ${data.leaderboard.map(entry => `
                <div class="leaderboard-row">
                    <div>${entry.rank || '-'}</div>
                    <div>${entry.username}</div>
                    <div>${entry.total_score.toFixed(1)}</div>
                    <div>${entry.coding_score.toFixed(1)}</div>
                    <div>${entry.quiz_score.toFixed(1)}</div>
                    <div>${entry.accuracy.toFixed(1)}%</div>
                </div>
            `).join('')}
        `;
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// Chatbot
function loadChatbotPage() {
    const interviewSetup = document.getElementById('interview-setup');
    const interviewChat = document.getElementById('interview-chat');
    const resumeFileName = document.getElementById('resume-file-name');
    const jobFileName = document.getElementById('job-file-name');
    
    if (interviewSetup) {
        interviewSetup.style.display = 'block';
    }
    if (interviewChat) {
        interviewChat.style.display = 'none';
    }
    currentSessionId = null;
    
    // Stop any ongoing recording and camera
    stopVoiceRecording();
    if (interviewStream) {
        interviewStream.getTracks().forEach(track => track.stop());
        interviewStream = null;
    }
    const videoElement = document.getElementById('interview-video');
    if (videoElement) {
        videoElement.srcObject = null;
    }
    
    // Clear file names
    if (resumeFileName) {
        resumeFileName.textContent = '';
    }
    if (jobFileName) {
        jobFileName.textContent = '';
    }
    
    // Reset transcript
    currentTranscript = '';
    const transcriptDiv = document.getElementById('voice-transcript');
    if (transcriptDiv) transcriptDiv.innerHTML = '';
}

async function handleResumeUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileNameDiv = document.getElementById('resume-file-name');
    const resumeTextarea = document.getElementById('resume-text');
    
    // Show loading
    fileNameDiv.textContent = `Uploading ${file.name}...`;
    fileNameDiv.style.color = '#66e3c4';
    
    try {
        const result = await chatbotAPI.extractText(file);
        resumeTextarea.value = result.text;
        fileNameDiv.textContent = `✓ ${file.name} - Text extracted successfully`;
        fileNameDiv.style.color = '#33d17a';
    } catch (error) {
        fileNameDiv.textContent = `✗ Error: ${error.message}`;
        fileNameDiv.style.color = '#ff6b6b';
        alert(`Error extracting text from file: ${error.message}`);
    }
}

async function handleJobUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileNameDiv = document.getElementById('job-file-name');
    const jobTextarea = document.getElementById('job-description');
    
    // Show loading
    fileNameDiv.textContent = `Uploading ${file.name}...`;
    fileNameDiv.style.color = '#66e3c4';
    
    try {
        const result = await chatbotAPI.extractText(file);
        jobTextarea.value = result.text;
        fileNameDiv.textContent = `✓ ${file.name} - Text extracted successfully`;
        fileNameDiv.style.color = '#33d17a';
    } catch (error) {
        fileNameDiv.textContent = `✗ Error: ${error.message}`;
        fileNameDiv.style.color = '#ff6b6b';
        alert(`Error extracting text from file: ${error.message}`);
    }
}

async function startInterview() {
    const resumeTextEl = document.getElementById('resume-text');
    const jobDescriptionEl = document.getElementById('job-description');
    
    if (!resumeTextEl || !jobDescriptionEl) {
        alert('Interview form elements not found');
        return;
    }
    
    const resumeText = resumeTextEl.value;
    const jobDescription = jobDescriptionEl.value;
    
    if (!resumeText || !jobDescription) {
        alert('Please provide both resume and job description');
        return;
    }
    
    try {
        // Show loading state
        const interviewSetup = document.getElementById('interview-setup');
        const interviewChat = document.getElementById('interview-chat');
        if (interviewSetup) {
            interviewSetup.style.display = 'none';
        }
        if (interviewChat) {
            interviewChat.style.display = 'block';
            // Show loading message
            const chatDiv = document.getElementById('chat-messages');
            if (chatDiv) {
                chatDiv.innerHTML = '<div class="chat-message question">Requesting camera and microphone access...</div>';
            }
        }
        
        // Request camera and microphone access
        await requestCameraAndMicrophone();
        
        // Start interview session
        const data = await chatbotAPI.startInterview(resumeText, jobDescription, 'technical', 'fresher', 5);
        currentSessionId = data.session_id;
        
        // Display first question with phase indicator
        const chatDiv = document.getElementById('chat-messages');
        if (chatDiv) {
            const phaseLabel = getPhaseLabel(data.phase || 'introduction');
            chatDiv.innerHTML = `
                <div class="interview-progress">
                    <div class="progress-info">
                        <span class="phase-badge phase-${data.phase || 'introduction'}">${phaseLabel}</span>
                    </div>
                </div>
                <div class="chat-message question">
                    <strong>Interviewer:</strong> ${data.question}
                </div>
            `;
        }
        
        // Initialize speech recognition
        initializeSpeechRecognition();
    } catch (error) {
        alert(`Error: ${error.message}`);
        
        // Show error in chat
        const chatDiv = document.getElementById('chat-messages');
        if (chatDiv) {
            chatDiv.innerHTML = `
                <div class="chat-message feedback">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        }
        
        // Stop stream if there was an error
        if (interviewStream) {
            interviewStream.getTracks().forEach(track => track.stop());
            interviewStream = null;
        }
        
        // Show setup again on error
        const interviewSetup = document.getElementById('interview-setup');
        const interviewChat = document.getElementById('interview-chat');
        if (interviewSetup) interviewSetup.style.display = 'block';
        if (interviewChat) interviewChat.style.display = 'none';
    }
}

async function requestCameraAndMicrophone() {
    try {
        // Check if mediaDevices is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera and microphone access is not supported in this browser. Please use a modern browser like Chrome, Firefox, or Edge.');
        }
        
        // Request both video (front camera) and audio
        interviewStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'user', // Front camera
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true
            }
        });
        
        const videoElement = document.getElementById('interview-video');
        if (videoElement) {
            videoElement.srcObject = interviewStream;
            videoElement.muted = false; // Unmute to hear audio if needed
            videoElement.playsInline = true;
            
            // Wait for video to be ready
            await new Promise((resolve, reject) => {
                videoElement.onloadedmetadata = () => {
                    videoElement.play()
                        .then(() => {
                            console.log('Video started successfully');
                            resolve();
                        })
                        .catch(reject);
                };
                videoElement.onerror = reject;
                
                // Timeout after 5 seconds
                setTimeout(() => reject(new Error('Video loading timeout')), 5000);
            });
        } else {
            throw new Error('Video element not found');
        }
    } catch (error) {
        // Clean up on error
        if (interviewStream) {
            interviewStream.getTracks().forEach(track => track.stop());
            interviewStream = null;
        }
        throw new Error(`Failed to access camera/microphone: ${error.message}. Please allow camera and microphone access.`);
    }
}

function initializeSpeechRecognition() {
    // Check if browser supports Web Speech API
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Speech recognition not supported in this browser');
        // Fallback: show text input
        const voiceInputContainer = document.querySelector('.voice-input-container');
        if (voiceInputContainer) {
            voiceInputContainer.innerHTML = `
                <textarea id="chat-answer" placeholder="Type your answer... (Speech recognition not available)"></textarea>
            `;
        }
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
        isRecording = true;
        const indicator = document.getElementById('recording-indicator');
        if (indicator) indicator.style.display = 'flex';
    };
    
    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }
        
        currentTranscript = finalTranscript + interimTranscript;
        const transcriptDiv = document.getElementById('voice-transcript');
        if (transcriptDiv) {
            transcriptDiv.innerHTML = `
                <div class="transcript-text">${finalTranscript}<span class="interim">${interimTranscript}</span></div>
            `;
        }
        
        // Show submit button when there's text
        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn && currentTranscript.trim()) {
            submitBtn.style.display = 'block';
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
            // User stopped speaking, keep recording
            return;
        }
        stopVoiceRecording();
        alert(`Speech recognition error: ${event.error}`);
    };
    
    recognition.onend = () => {
        if (isRecording) {
            // Restart recognition if still recording
            try {
                recognition.start();
            } catch (e) {
                console.error('Failed to restart recognition:', e);
            }
        }
    };
}

function startVoiceRecording() {
    if (!recognition) {
        alert('Speech recognition not initialized. Please refresh and try again.');
        return;
    }
    
    try {
        recognition.start();
        const startBtn = document.getElementById('start-recording-btn');
        const stopBtn = document.getElementById('stop-recording-btn');
        if (startBtn) startBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'block';
    } catch (error) {
        console.error('Error starting recognition:', error);
        alert('Failed to start recording. Please try again.');
    }
}

function stopVoiceRecording() {
    isRecording = false;
    if (recognition) {
        recognition.stop();
    }
    
    const startBtn = document.getElementById('start-recording-btn');
    const stopBtn = document.getElementById('stop-recording-btn');
    const indicator = document.getElementById('recording-indicator');
    
    if (startBtn) startBtn.style.display = 'block';
    if (stopBtn) stopBtn.style.display = 'none';
    if (indicator) indicator.style.display = 'none';
}

function getPhaseLabel(phase) {
    const phaseLabels = {
        'introduction': 'Introduction',
        'resume': 'Resume-Based',
        'jd': 'Job Description',
        'general': 'General'
    };
    return phaseLabels[phase] || 'General';
}

async function submitAnswer() {
    if (!currentSessionId) return;
    
    // Stop recording before submitting
    stopVoiceRecording();
    
    // Get answer from transcript or textarea
    let answer = currentTranscript.trim();
    const chatAnswerEl = document.getElementById('chat-answer');
    if (!answer && chatAnswerEl) {
        answer = chatAnswerEl.value.trim();
    }
    
    if (!answer) {
        alert('Please provide an answer');
        return;
    }
    
    try {
        const data = await chatbotAPI.submitAnswer(currentSessionId, answer);
        const chatDiv = document.getElementById('chat-messages');
        
        if (chatDiv) {
            // Check if interview is completed
            if (data.interview_completed) {
                chatDiv.innerHTML += `
                    <div class="chat-message answer">
                        <strong>You:</strong> ${answer}
                    </div>
                    <div class="chat-message feedback">
                        <strong>Feedback:</strong> ${data.feedback}
                        ${data.scores ? `
                            <div class="score-display">
                                <div class="score-item">
                                    <span>Correctness:</span>
                                    <span class="score-value">${data.scores.correctness}/10</span>
                                </div>
                                <div class="score-item">
                                    <span>Clarity:</span>
                                    <span class="score-value">${data.scores.clarity}/10</span>
                                </div>
                                <div class="score-item">
                                    <span>Confidence:</span>
                                    <span class="score-value">${data.scores.confidence}/10</span>
                                </div>
                                <div class="score-item overall">
                                    <span>Overall Score:</span>
                                    <span class="score-value">${data.scores.overall}/10</span>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="interview-complete">
                        <div class="interview-complete-header">
                            <h2>🎉 Interview Completed!</h2>
                            <p style="color: rgba(242, 244, 255, 0.8); margin-top: 10px;">Great job completing the interview. Here's your performance summary:</p>
                        </div>
                        
                        <div class="interview-performance-cards">
                            <div class="performance-card-main">
                                <div class="performance-card-icon">📊</div>
                                <div class="performance-card-content">
                                    <p class="performance-card-label">Average Score</p>
                                    <h3 class="performance-card-value">${data.average_score || 0}/10</h3>
                                    <div class="performance-bar">
                                        <div class="performance-bar-fill" style="width: ${((data.average_score || 0) / 10) * 100}%"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="performance-card-secondary">
                                <div class="performance-card-content">
                                    <p class="performance-card-label">Total Questions</p>
                                    <h3 class="performance-card-value">${data.total_questions || 0}</h3>
                                </div>
                            </div>
                        </div>
                        
                        <div class="interview-summary">
                            <h4>📝 Performance Summary</h4>
                            <div class="summary-content">
                                <p>${data.summary || 'Interview completed successfully. Review your answers and continue practicing to improve your interview skills.'}</p>
                            </div>
                        </div>
                        
                        <div class="interview-actions">
                            <button onclick="location.reload()" class="btn btn-primary">Start New Interview</button>
                        </div>
                    </div>
                `;
            } else {
                // Continue interview
                const phaseLabel = getPhaseLabel(data.phase || 'general');
                chatDiv.innerHTML += `
                    <div class="chat-message answer">
                        <strong>You:</strong> ${answer}
                    </div>
                    <div class="chat-message feedback">
                        <strong>Feedback:</strong> ${data.feedback}
                        ${data.scores ? `
                            <div class="score-display">
                                <div class="score-item">
                                    <span>Correctness:</span>
                                    <span class="score-value">${data.scores.correctness}/10</span>
                                </div>
                                <div class="score-item">
                                    <span>Clarity:</span>
                                    <span class="score-value">${data.scores.clarity}/10</span>
                                </div>
                                <div class="score-item">
                                    <span>Confidence:</span>
                                    <span class="score-value">${data.scores.confidence}/10</span>
                                </div>
                                <div class="score-item overall">
                                    <span>Overall:</span>
                                    <span class="score-value">${data.scores.overall}/10</span>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="interview-progress">
                        <div class="progress-info">
                            <span class="phase-badge phase-${data.phase || 'general'}">${phaseLabel}</span>
                        </div>
                    </div>
                    <div class="chat-message question">
                        <strong>Interviewer:</strong> ${data.next_question}
                    </div>
                `;
            }
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }
        
        // Clear transcript and hide submit button
        currentTranscript = '';
        const transcriptDiv = document.getElementById('voice-transcript');
        if (transcriptDiv) transcriptDiv.innerHTML = '';
        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn) submitBtn.style.display = 'none';
        
        if (chatAnswerEl) chatAnswerEl.value = '';
        
        // Restart recording for next question
        setTimeout(() => {
            startVoiceRecording();
        }, 1000);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Notifications
let notificationDropdownOpen = false;

// Load notification badge count
async function loadNotificationBadge() {
    try {
        // Check if user is logged in
        if (!authToken || !currentUser) {
            return;
        }
        
        const data = await notificationsAPI.getUnreadCount();
        const badge = document.getElementById('notification-badge');
        if (!badge) return;
        
        const count = data.count || 0;
        
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        // Silently fail - don't show errors if notifications can't be loaded
        console.error('Error loading notification badge:', error);
        const badge = document.getElementById('notification-badge');
        if (badge) {
            badge.style.display = 'none';
        }
    }
}

// Load notifications into dropdown
async function loadNotifications() {
    try {
        // Check if user is logged in
        if (!authToken || !currentUser) {
            const notificationList = document.getElementById('notification-list');
            if (notificationList) {
                notificationList.innerHTML = '<div class="notification-empty">Please log in to view notifications</div>';
            }
            return;
        }
        
        const data = await notificationsAPI.getNotifications();
        const notificationList = document.getElementById('notification-list');
        if (!notificationList) return;
        
        if (!data.notifications || data.notifications.length === 0) {
            notificationList.innerHTML = '<div class="notification-empty">No notifications</div>';
            return;
        }
        
        notificationList.innerHTML = data.notifications.map(n => {
            const date = n.created_at ? new Date(n.created_at).toLocaleString() : '';
            const unreadClass = !n.is_read ? 'unread' : '';
            const linkAttr = n.link ? `onclick="window.location.href='${n.link}'; markNotificationRead(${n.id});"` : '';
            
            return `
                <div class="notification-item ${unreadClass}" ${linkAttr || `onclick="markNotificationRead(${n.id})"`}>
                    <div class="notification-content">
                        <div class="notification-title">${n.title}</div>
                        <div class="notification-message">${n.message}</div>
                        <div class="notification-time">${date}</div>
                    </div>
                    ${!n.is_read ? '<div class="notification-dot"></div>' : ''}
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading notifications:', error);
        const notificationList = document.getElementById('notification-list');
        if (notificationList) {
            // Show user-friendly error message
            const errorMsg = error.message && error.message.includes('connect') 
                ? 'Unable to connect to server' 
                : 'Error loading notifications';
            notificationList.innerHTML = `<div class="notification-empty">${errorMsg}</div>`;
        }
    }
}

// Toggle notification dropdown
function toggleNotificationDropdown() {
    const dropdown = document.getElementById('notification-dropdown');
    notificationDropdownOpen = !notificationDropdownOpen;
    
    if (notificationDropdownOpen) {
        dropdown.style.display = 'block';
        loadNotifications();
    } else {
        dropdown.style.display = 'none';
    }
}

// Mark notification as read
async function markNotificationRead(notificationId) {
    try {
        if (!authToken || !currentUser) {
            console.warn('User not authenticated');
            return;
        }
        await notificationsAPI.markAsRead(notificationId);
        // Reload notifications and badge
        await loadNotifications();
        await loadNotificationBadge();
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Mark all notifications as read
async function markAllNotificationsRead() {
    try {
        if (!authToken || !currentUser) {
            console.warn('User not authenticated');
            return;
        }
        
        // Show loading state
        const markAllBtn = document.querySelector('.mark-all-read-btn');
        const originalText = markAllBtn ? markAllBtn.textContent : 'Mark all as read';
        if (markAllBtn) {
            markAllBtn.textContent = 'Marking...';
            markAllBtn.disabled = true;
        }
        
        // Call API
        await notificationsAPI.markAllAsRead();
        
        // Reload notifications and badge to reflect changes
        await loadNotifications();
        await loadNotificationBadge();
        
        // Restore button state
        if (markAllBtn) {
            markAllBtn.textContent = originalText;
            markAllBtn.disabled = false;
        }
        
        // Show success feedback (optional - can be removed if not needed)
        console.log('All notifications marked as read');
    } catch (error) {
        console.error('Error marking all notifications as read:', error);
        
        // Restore button state on error
        const markAllBtn = document.querySelector('.mark-all-read-btn');
        if (markAllBtn) {
            markAllBtn.textContent = 'Mark all as read';
            markAllBtn.disabled = false;
        }
        
        // Show error message to user
        alert('Failed to mark all notifications as read. Please try again.');
    }
}

// Mobile Menu Toggle
function toggleMobileMenu() {
    const navCenter = document.getElementById('nav-center');
    if (navCenter) {
        navCenter.classList.toggle('active');
    }
}

// Close mobile menu when clicking outside
document.addEventListener('click', (e) => {
    const navCenter = document.getElementById('nav-center');
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    
    if (navCenter && mobileToggle && !navCenter.contains(e.target) && !mobileToggle.contains(e.target)) {
        navCenter.classList.remove('active');
    }
});

// Close notification dropdown when clicking outside
document.addEventListener('click', (e) => {
    const bellBtn = document.getElementById('notification-bell-btn');
    const dropdown = document.getElementById('notification-dropdown');
    
    if (notificationDropdownOpen && 
        !bellBtn.contains(e.target) && 
        !dropdown.contains(e.target)) {
        toggleNotificationDropdown();
    }
});

