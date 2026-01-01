/**
 * Enhanced AI Virtual Interview Flow Management
 * Supports TR (Technical) and HR interview types with structured flow
 */

// Interview state - Made globally accessible to avoid conflicts with app.js
let currentInterviewType = null;  // 'TR' or 'HR'
let currentSessionId = null;
let interviewResumeData = null;
let interviewJDData = null;
let interviewResumeText = '';
let interviewJDText = '';
let interviewStartTime = null;
let currentQuestionStartTime = null;
let interviewStream = null;
let recognition = null;
let isRecording = false;
let currentTranscript = '';

// Make variables globally accessible for backward compatibility with old code
if (typeof window !== 'undefined') {
    window.currentSessionId = currentSessionId;
    window.interviewStream = interviewStream;
    window.recognition = recognition;
    window.isRecording = isRecording;
    window.currentTranscript = currentTranscript;
}

// STEP 1: Select Interview Type
function selectInterviewType(type, element) {
    try {
        console.log('Selecting interview type:', type);
        currentInterviewType = type;
        
        // Update UI - highlight selected card
        document.querySelectorAll('.interview-type-card').forEach(card => {
            card.classList.remove('selected');
        });
        if (element) {
            element.classList.add('selected');
        }
        
        // Show upload section and hide type selection
        const typeSelection = document.getElementById('interview-type-selection');
        const uploadSection = document.getElementById('interview-upload');
        
        if (!typeSelection) {
            console.error('interview-type-selection element not found');
            alert('Error: Interview type selection section not found. Please refresh the page.');
            return;
        }
        
        if (!uploadSection) {
            console.error('interview-upload element not found');
            alert('Error: Interview upload section not found. Please refresh the page.');
            return;
        }
        
        typeSelection.style.display = 'none';
        uploadSection.style.display = 'block';
        
        // Store interview type
        localStorage.setItem('selectedInterviewType', type);
        
        console.log('Interview type selected successfully:', type);
    } catch (error) {
        console.error('Error in selectInterviewType:', error);
        alert('Error selecting interview type: ' + error.message);
    }
}

function goBackToTypeSelection() {
    document.getElementById('interview-upload').style.display = 'none';
    document.getElementById('interview-type-selection').style.display = 'block';
    currentInterviewType = null;
    localStorage.removeItem('selectedInterviewType');
}

// STEP 2: Handle Resume Upload
async function handleResumeUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileNameDiv = document.getElementById('resume-file-name');
    const resumeTextarea = document.getElementById('resume-text');
    
    fileNameDiv.innerHTML = `<div class="upload-status">Uploading ${file.name}...</div>`;
    
    try {
        const result = await interviewAPI.uploadResume(file);
        interviewResumeText = result.resume_text || '';
        interviewResumeData = result.resume_data || null;
        
        if (resumeTextarea) {
            resumeTextarea.value = result.resume_text || '';
            resumeTextarea.style.display = 'block';
        }
        
        fileNameDiv.innerHTML = `
            <div class="upload-status success">
                ✓ ${result.filename} - Processed successfully
                ${result.resume_data ? `<br><small>Extracted: ${result.resume_data.skills?.length || 0} skills, ${result.resume_data.programming_languages?.length || 0} languages</small>` : ''}
            </div>
        `;
    } catch (error) {
        fileNameDiv.innerHTML = `<div class="upload-status error">✗ Error: ${error.message}</div>`;
        alert(`Error uploading resume: ${error.message}`);
    }
}

// STEP 2: Handle JD Upload
async function handleJDUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileNameDiv = document.getElementById('jd-file-name');
    const jdTextarea = document.getElementById('job-description');
    
    fileNameDiv.innerHTML = `<div class="upload-status">Uploading ${file.name}...</div>`;
    
    try {
        // Get resume skills for mapping
        const resumeSkills = interviewResumeData?.skills || [];
        const formData = new FormData();
        formData.append('file', file);
        if (resumeSkills.length > 0) {
            formData.append('resume_skills', JSON.stringify(resumeSkills));
        }
        
        const result = await interviewAPI.uploadJD(file, resumeSkills);
        interviewJDText = result.jd_text || '';
        interviewJDData = result.jd_data || null;
        
        if (jdTextarea) {
            jdTextarea.value = result.jd_text || '';
            jdTextarea.style.display = 'block';
        }
        
        fileNameDiv.innerHTML = `
            <div class="upload-status success">
                ✓ ${result.filename} - Processed successfully
                ${result.jd_data ? `<br><small>Required: ${result.jd_data.required_skills?.length || 0} skills, Missing: ${result.jd_data.missing_skills?.length || 0} skills</small>` : ''}
            </div>
        `;
    } catch (error) {
        fileNameDiv.innerHTML = `<div class="upload-status error">✗ Error: ${error.message}</div>`;
        alert(`Error uploading job description: ${error.message}`);
    }
}

// STEP 3: Process Uploads and Start Interview
async function processUploadsAndStart() {
    // Get interview type
    if (!currentInterviewType) {
        currentInterviewType = localStorage.getItem('selectedInterviewType');
        if (!currentInterviewType) {
            alert('Please select an interview type first');
            goBackToTypeSelection();
            return;
        }
    }
    
    // Get resume text (from upload or textarea)
    const resumeTextarea = document.getElementById('resume-text');
    if (resumeTextarea && resumeTextarea.value) {
        interviewResumeText = resumeTextarea.value;
    }
    
    // Get JD text (from upload or textarea)
    const jdTextarea = document.getElementById('job-description');
    if (jdTextarea && jdTextarea.value) {
        interviewJDText = jdTextarea.value;
    }
    
    if (!interviewResumeText) {
        alert('Please upload or enter your resume');
        return;
    }
    
    try {
        // Show loading
        const uploadSection = document.getElementById('interview-upload');
        const chatSection = document.getElementById('interview-chat');
        uploadSection.style.display = 'none';
        chatSection.style.display = 'block';
        
        // Request camera access
        await requestCameraAndMicrophone();
        
        // Start interview
        const startData = {
            interview_type: currentInterviewType,
            resume_text: interviewResumeText,
            job_description: interviewJDText,
            resume_data: interviewResumeData,
            jd_data: interviewJDData
        };
        
        const result = await interviewAPI.startInterview(startData);
        currentSessionId = result.session_id;
        // Update global reference for backward compatibility
        if (typeof window !== 'undefined') {
            window.currentSessionId = currentSessionId;
        }
        interviewStartTime = Date.now();
        currentQuestionStartTime = Date.now();
        
        // Display first question
        displayQuestion(result.question, result.question_number, result.total_questions, 'introduction');
        
        // Initialize speech recognition
        initializeSpeechRecognition();
        
        // Update question counter
        updateQuestionCounter(result.question_number, result.total_questions);
        
        // Update interview type badge
        const badge = document.getElementById('current-interview-type-badge');
        if (badge) {
            badge.textContent = currentInterviewType === 'TR' ? 'Technical Interview' : 'HR Interview';
            badge.className = `interview-type-badge ${currentInterviewType.toLowerCase()}`;
        }
    } catch (error) {
        console.error('Error starting interview:', error);
        // Show detailed error message for debugging
        let errorMessage = 'Failed to start interview.\n\n';
        
        // Check for specific error types
        if (error.message) {
            if (error.message.includes('resume_file_path') || error.message.includes('Unknown column')) {
                errorMessage += 'Database Error: Missing columns in interview_sessions table.\n';
                errorMessage += 'Please run: python backend/migrate_interview_columns.py\n\n';
                errorMessage += 'Full error: ' + error.message;
            } else if (error.message.includes('Cannot connect to server')) {
                errorMessage += 'Connection Error: Cannot connect to backend server.\n';
                errorMessage += 'Please check if the Railway backend is running.\n\n';
                errorMessage += 'Full error: ' + error.message;
            } else {
                errorMessage += 'Error: ' + error.message;
            }
        } else {
            errorMessage += 'Unknown error occurred. Please check the console for details.';
        }
        
        alert(errorMessage);
        // Show upload section again
        document.getElementById('interview-upload').style.display = 'block';
        document.getElementById('interview-chat').style.display = 'none';
    }
}

// Display question in chat
function displayQuestion(question, questionNumber, totalQuestions, phase) {
    const chatDiv = document.getElementById('chat-messages');
    if (!chatDiv) return;
    
    const phaseLabel = getPhaseLabel(currentInterviewType, phase);
    
    chatDiv.innerHTML += `
        <div class="chat-message question">
            <div class="phase-badge phase-${phase}">${phaseLabel}</div>
            <div class="question-content">
                <strong>Interviewer:</strong> ${question}
            </div>
        </div>
    `;
    
    chatDiv.scrollTop = chatDiv.scrollHeight;
    
    // Reset answer input
    const answerText = document.getElementById('answer-text');
    if (answerText) answerText.value = '';
    currentTranscript = '';
    
    // Show submit button
    const submitBtn = document.getElementById('submit-answer-btn');
    if (submitBtn) submitBtn.style.display = 'block';
}

function getPhaseLabel(interviewType, phase) {
    if (interviewType === 'TR') {
        const labels = {
            'introduction': 'Introduction',
            'resume': 'Resume-Based Technical',
            'programming': 'Programming Languages',
            'jd_skills': 'JD Required Skills',
            'scenario': 'Scenario-Based'
        };
        return labels[phase] || 'General';
    } else {
        const labels = {
            'introduction': 'Introduction',
            'communication': 'Communication Skills',
            'behavioral': 'Behavioral',
            'situational': 'Situational',
            'career': 'Career Goals'
        };
        return labels[phase] || 'General';
    }
}

function updateQuestionCounter(current, total) {
    const currentEl = document.getElementById('current-question-number');
    if (currentEl) currentEl.textContent = current;
    // Total questions removed - only showing current question number
}

// STEP 6: Submit Answer
async function submitAnswer() {
    if (!currentSessionId) {
        alert('No active interview session');
        return;
    }
    
    // Stop recording
    stopVoiceRecording();
    
    // Get answer
    const answerTextEl = document.getElementById('answer-text');
    let answer = currentTranscript.trim() || (answerTextEl ? answerTextEl.value.trim() : '');
    
    if (!answer) {
        alert('Please provide an answer');
        return;
    }
    
    // Calculate time taken
    const timeTaken = currentQuestionStartTime ? Math.floor((Date.now() - currentQuestionStartTime) / 1000) : 0;
    currentQuestionStartTime = Date.now();
    
    try {
        // Disable submit button
        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn) submitBtn.disabled = true;
        
        // Display user answer
        const chatDiv = document.getElementById('chat-messages');
        if (chatDiv) {
            chatDiv.innerHTML += `
                <div class="chat-message answer">
                    <strong>You:</strong> ${answer}
                </div>
            `;
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }
        
        // Submit answer
        const result = await interviewAPI.submitAnswer(currentSessionId, answer, timeTaken);
        
        // Display feedback with enhanced formatting for structured guidance
        if (chatDiv && result.feedback) {
            // Format feedback to highlight structured methods (STAR, numbered lists, etc.)
            let formattedFeedback = result.feedback;
            
            // Detect and format STAR method mentions
            const starPattern = /(STAR method|Situation.*?Task.*?Action.*?Result)/gi;
            if (starPattern.test(formattedFeedback)) {
                formattedFeedback = formattedFeedback.replace(
                    /(Situation|Task|Action|Result):\s*([^\n-]+)/gi,
                    '<strong>$1:</strong> $2'
                );
            }
            
            // Format numbered lists and bullet points
            formattedFeedback = formattedFeedback.replace(
                /(\d+\.\s+[^\n]+)/g,
                '<div class="feedback-list-item">$1</div>'
            );
            formattedFeedback = formattedFeedback.replace(
                /(-|\*)\s+([^\n]+)/g,
                '<div class="feedback-list-item">• $2</div>'
            );
            
            // Format code blocks or structured examples
            formattedFeedback = formattedFeedback.replace(
                /For example[^:]*:\s*([^\n]+)/gi,
                '<div class="feedback-example"><strong>Example:</strong> $1</div>'
            );
            
            // Preserve line breaks
            formattedFeedback = formattedFeedback.replace(/\n/g, '<br>');
            
            chatDiv.innerHTML += `
                <div class="chat-message feedback feedback-enhanced">
                    <div class="feedback-header">
                        <strong>💡 Feedback & Guidance:</strong>
                    </div>
                    <div class="feedback-content">
                        ${formattedFeedback}
                    </div>
                    ${result.scores ? `
                        <div class="score-display-mini">
                            <span>Correctness: ${result.scores.correctness}/10</span>
                            <span>Clarity: ${result.scores.clarity}/10</span>
                            <span>Confidence: ${result.scores.confidence}/10</span>
                            <span>Overall: ${result.scores.overall}/10</span>
                        </div>
                    ` : ''}
                </div>
            `;
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }
        
        // Check if interview is completed
        if (result.interview_completed) {
            showInterviewResults(result);
        } else if (result.next_question) {
            // Display next question
            displayQuestion(result.next_question, result.question_number, result.total_questions, result.phase);
            updateQuestionCounter(result.question_number, result.total_questions);
        }
        
        // Re-enable submit button
        if (submitBtn) submitBtn.disabled = false;
        
    } catch (error) {
        alert(`Error submitting answer: ${error.message}`);
        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn) submitBtn.disabled = false;
    }
}

// STEP 8: Show Interview Results
async function showInterviewResults(result) {
    // Hide interview chat
    document.getElementById('interview-chat').style.display = 'none';
    
    // Show results section
    const resultsSection = document.getElementById('interview-results');
    resultsSection.style.display = 'block';
    
    // Stop camera
    if (interviewStream) {
        interviewStream.getTracks().forEach(track => track.stop());
        interviewStream = null;
    }
    
    // Display final score
    const finalScoreEl = document.getElementById('final-score');
    if (finalScoreEl) {
        finalScoreEl.textContent = result.final_score || 0;
    }
    
    // Display interview type
    const typeEl = document.getElementById('interview-type-result');
    if (typeEl) {
        typeEl.textContent = currentInterviewType === 'TR' ? 'Technical Interview' : 'HR Interview';
    }
    
    // Display score breakdown
    const breakdownEl = document.getElementById('score-breakdown');
    if (breakdownEl && resultData.score_breakdown) {
        const breakdown = typeof resultData.score_breakdown === 'string' ? 
            JSON.parse(resultData.score_breakdown) : resultData.score_breakdown;
        let html = '<div class="breakdown-grid">';
        
        const interviewType = resultData.interview_type || currentInterviewType || 'TR';
        if (interviewType === 'TR') {
            html += `
                <div class="breakdown-item"><span>Introduction:</span> <strong>${breakdown.introduction_score || 0}/10</strong></div>
                <div class="breakdown-item"><span>Projects & Resume:</span> <strong>${breakdown.projects_resume_score || 0}/10</strong></div>
                <div class="breakdown-item"><span>Programming:</span> <strong>${breakdown.programming_score || 0}/10</strong></div>
                <div class="breakdown-item"><span>JD Gap Skills:</span> <strong>${breakdown.jd_gap_skills_score || 0}/10</strong></div>
                <div class="breakdown-item"><span>Communication:</span> <strong>${breakdown.communication_score || 0}/10</strong></div>
            `;
        } else {
            html += `
                <div class="breakdown-item"><span>Introduction:</span> <strong>${breakdown.hr_introduction_score || 0}/10</strong></div>
                <div class="breakdown-item"><span>Communication:</span> <strong>${breakdown.hr_communication_score || 0}/10</strong></div>
                <div class="breakdown-item"><span>Confidence:</span> <strong>${breakdown.hr_confidence_score || 0}/10</strong></div>
                <div class="breakdown-item"><span>Behavioral:</span> <strong>${breakdown.hr_behavioral_score || 0}/10</strong></div>
            `;
        }
        
        html += '</div>';
        breakdownEl.innerHTML = html;
    }
    
    // Display strengths
    const strengthsList = document.getElementById('strengths-list');
    if (strengthsList && resultData.strengths) {
        const strengths = Array.isArray(resultData.strengths) ? resultData.strengths : 
                         (typeof resultData.strengths === 'string' ? JSON.parse(resultData.strengths) : []);
        strengthsList.innerHTML = strengths.map(s => `<li>${s}</li>`).join('');
    }
    
    // Display weaknesses
    const weaknessesList = document.getElementById('weaknesses-list');
    if (weaknessesList && resultData.weaknesses) {
        const weaknesses = Array.isArray(resultData.weaknesses) ? resultData.weaknesses : 
                          (typeof resultData.weaknesses === 'string' ? JSON.parse(resultData.weaknesses) : []);
        weaknessesList.innerHTML = weaknesses.map(w => `<li>${w}</li>`).join('');
    }
    
    // Display improvements
    const improvementsList = document.getElementById('improvements-list');
    if (improvementsList && resultData.improvements) {
        const improvements = Array.isArray(resultData.improvements) ? resultData.improvements : 
                           (typeof resultData.improvements === 'string' ? JSON.parse(resultData.improvements) : []);
        improvementsList.innerHTML = improvements.map(i => `<li>${i}</li>`).join('');
    }
    
    // Display resources
    const resourcesList = document.getElementById('resources-list-interview');
    if (resourcesList && resultData.suggested_resources) {
        const resources = Array.isArray(resultData.suggested_resources) ? resultData.suggested_resources : 
                         (typeof resultData.suggested_resources === 'string' ? JSON.parse(resultData.suggested_resources) : []);
        resourcesList.innerHTML = resources.map(r => `<li>${r}</li>`).join('');
    }
    
    // Display summary
    const summaryEl = document.getElementById('summary-text');
    if (summaryEl) {
        if (resultData.summary) {
            summaryEl.textContent = typeof resultData.summary === 'string' ? resultData.summary : 
                                   (resultData.summary.get ? resultData.summary.get('summary', '') : '');
        }
    }
    
    // Display practice recommendations
    const weakSkills = resultData.weak_skills || [];
    const practiceMaterials = resultData.practice_materials || {};
    if (weakSkills.length > 0 || Object.keys(practiceMaterials).length > 0) {
        displayPracticeRecommendations(weakSkills, practiceMaterials);
    } else if (currentSessionId) {
        // Try to fetch practice recommendations
        loadPracticeRecommendations(currentSessionId);
    }
    
    // Refresh Placement Readiness Score after interview completion
    if (typeof loadPlacementReadinessScore === 'function') {
        loadPlacementReadinessScore();
    }
}

// Display Practice Recommendations
function displayPracticeRecommendations(weak_skills, practice_materials) {
    const practiceSection = document.getElementById('practice-recommendations');
    if (!practiceSection) {
        // Create practice recommendations section if it doesn't exist
        const resultsSection = document.getElementById('interview-results');
        if (resultsSection) {
            const practiceDiv = document.createElement('div');
            practiceDiv.id = 'practice-recommendations';
            practiceDiv.className = 'practice-recommendations-section';
            resultsSection.appendChild(practiceDiv);
        } else {
            return;
        }
    }
    
    if (!weak_skills || weak_skills.length === 0) {
        practiceSection.innerHTML = '<p style="text-align: center; color: rgba(232,236,243,0.6);">No weak skills detected. Great job!</p>';
        return;
    }
    
    let html = '<h3>🎯 Recommended Practice Based on Weak Areas</h3>';
    
    for (const skill of weak_skills) {
        const practice = practice_materials[skill] || {
            mcq_count: 5,
            coding_count: 1,
            interview_questions_count: 1,
            practice_description: `Practice ${skill}`,
            difficulty_level: 'intermediate'
        };
        
        html += `
            <div class="practice-skill-card">
                <div class="practice-skill-header">
                    <h4>${skill}</h4>
                    <span class="difficulty-badge ${practice.difficulty_level}">${practice.difficulty_level}</span>
                </div>
                <p class="practice-description">${practice.practice_description}</p>
                <div class="practice-recommendations">
                    ${practice.mcq_count > 0 ? `<div class="practice-item"><span class="practice-icon">📝</span> <strong>${practice.mcq_count}</strong> MCQ Questions</div>` : ''}
                    ${practice.coding_count > 0 ? `<div class="practice-item"><span class="practice-icon">💻</span> <strong>${practice.coding_count}</strong> Coding Problems</div>` : ''}
                    ${practice.interview_questions_count > 0 ? `<div class="practice-item"><span class="practice-icon">🎤</span> <strong>${practice.interview_questions_count}</strong> Interview Questions</div>` : ''}
                </div>
            </div>
        `;
    }
    
    practiceSection.innerHTML = html;
    practiceSection.style.display = 'block';
}

// Load Practice Recommendations
async function loadPracticeRecommendations(sessionId) {
    try {
        const data = await interviewAPI.getPracticeRecommendations(sessionId);
        displayPracticeRecommendations(data.weak_skills || [], data.practice_materials || {});
    } catch (error) {
        console.error('Error loading practice recommendations:', error);
    }
}

// End Interview Early
async function endInterviewEarly() {
    if (!currentSessionId) return;
    
    if (!confirm('Are you sure you want to end the interview? You will receive results based on your answers so far.')) {
        return;
    }
    
    try {
        const result = await interviewAPI.endInterview(currentSessionId);
        showInterviewResults(result);
    } catch (error) {
        alert(`Error ending interview: ${error.message}`);
    }
}

// Cleanup function to stop camera, mic, and speech recognition
function cleanupInterviewMedia() {
    // Stop speech recognition
    if (recognition) {
        try {
            recognition.stop();
        } catch (e) {
            console.log('Speech recognition already stopped');
        }
        recognition = null;
        isRecording = false;
    }
    
    // Stop camera and microphone
    if (interviewStream) {
        interviewStream.getTracks().forEach(track => {
            track.stop();
            console.log('Stopped media track:', track.kind);
        });
        interviewStream = null;
    }
    
    // Clear video element
    const videoElement = document.getElementById('interview-video');
    if (videoElement) {
        videoElement.srcObject = null;
    }
    
    // Hide recording indicator
    const indicator = document.getElementById('recording-indicator');
    if (indicator) indicator.style.display = 'none';
    
    // Update global references
    if (typeof window !== 'undefined') {
        window.interviewStream = null;
        window.recognition = null;
        window.isRecording = false;
    }
    
    console.log('Interview media cleanup completed');
}

// Start New Interview
function startNewInterview() {
    // Cleanup any existing media first
    cleanupInterviewMedia();
    
    // Reset state
    currentSessionId = null;
    currentInterviewType = null;
    interviewResumeData = null;
    interviewJDData = null;
    interviewResumeText = '';
    interviewJDText = '';
    
    // Update global references
    if (typeof window !== 'undefined') {
        window.currentSessionId = null;
        window.currentTranscript = '';
    }
    
    // Hide results, show type selection
    document.getElementById('interview-results').style.display = 'none';
    document.getElementById('interview-type-selection').style.display = 'block';
    
    // Clear file inputs
    document.getElementById('resume-file').value = '';
    document.getElementById('jd-file').value = '';
    document.getElementById('resume-text').value = '';
    document.getElementById('job-description').value = '';
    document.getElementById('resume-file-name').innerHTML = '';
    document.getElementById('jd-file-name').innerHTML = '';
}

function goToDashboard() {
    startNewInterview();
    showDashboard();
}

// Camera and Microphone
async function requestCameraAndMicrophone() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera and microphone access not supported');
        }
        
        interviewStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'user',
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
            videoElement.playsInline = true;
            await videoElement.play();
        }
    } catch (error) {
        console.warn('Camera access failed:', error);
        // Continue without camera - it's optional
    }
}

// Speech Recognition
function initializeSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Speech recognition not supported');
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
        
        // Update global reference
        if (typeof window !== 'undefined') {
            window.currentTranscript = currentTranscript;
        }
        
        // Update textarea
        const answerText = document.getElementById('answer-text');
        if (answerText) {
            answerText.value = currentTranscript;
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech') {
            stopVoiceRecording();
        }
    };
    
    recognition.onend = () => {
        if (isRecording) {
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
        alert('Speech recognition not available');
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

// Cleanup on page unload (browser close/refresh)
window.addEventListener('beforeunload', () => {
    cleanupInterviewMedia();
});

// Cleanup when page becomes hidden (tab switch, minimize)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Optional: cleanup when tab is hidden
        // Uncomment if you want to stop media when tab is switched
        // cleanupInterviewMedia();
    }
});

