"""
Enhanced AI Interview utilities for TR (Technical) and HR interview types
Supports structured question flow and scoring (out of 100)
"""
import requests
import json
import re
from config import Config
from utils.resume_processor import (
    extract_programming_languages, 
    extract_skills,
    extract_projects,
    extract_certificates
)

def calculate_total_questions(interview_type, resume_data=None, jd_data=None, experience_level='fresher'):
    """
    Calculate dynamic number of questions based on:
    - Interview type (TR vs HR)
    - Resume complexity (skills, projects, languages)
    - JD requirements (required skills, missing skills)
    - Experience level
    
    Returns: int (minimum 6, maximum 12)
    """
    base_questions = 6  # Minimum questions
    
    if interview_type == 'HR':
        # HR interviews are typically shorter
        # Base: 6 questions, add 1-2 for experience level
        if experience_level == 'experienced':
            return 8
        elif experience_level == 'intermediate':
            return 7
        else:  # fresher
            return 6
    
    # Technical Interview (TR) - more dynamic
    question_count = base_questions
    
    # Add questions based on resume complexity
    if resume_data:
        # Skills: 1 question per 3-4 skills (max +2)
        skills_count = len(resume_data.get('skills', []))
        if skills_count > 0:
            question_count += min(2, (skills_count // 3))
        
        # Programming languages: 1 question per 2 languages (max +2)
        languages_count = len(resume_data.get('programming_languages', []))
        if languages_count > 0:
            question_count += min(2, (languages_count // 2))
        
        # Projects: 1 question if has projects (max +1)
        projects_count = len(resume_data.get('projects', []))
        if projects_count > 0:
            question_count += 1
        
        # Experience years: more experience = more questions
        experience_years = resume_data.get('experience_years', 0)
        if experience_years >= 3:
            question_count += 1
        elif experience_years >= 1:
            question_count += 0.5  # Will round up
    
    # Add questions based on JD requirements
    if jd_data:
        # Required skills: 1 question per 4-5 skills (max +2)
        required_skills_count = len(jd_data.get('required_skills', []))
        if required_skills_count > 0:
            question_count += min(2, (required_skills_count // 4))
        
        # Missing skills (gaps): Critical - 1 question per 2 missing skills (max +2)
        missing_skills_count = len(jd_data.get('missing_skills', []))
        if missing_skills_count > 0:
            question_count += min(2, (missing_skills_count // 2))
    
    # Round to nearest integer and ensure within bounds
    question_count = int(round(question_count))
    
    # Ensure minimum and maximum bounds
    question_count = max(6, min(12, question_count))
    
    return question_count

def get_system_prompt(interview_type='TR', experience_level='fresher', resume_text='', job_description='', resume_data=None, jd_data=None):
    """
    Generate system prompt for AI interviewer based on interview type (TR or HR)
    """
    if interview_type == 'TR':
        # Technical Interview system prompt
        languages = resume_data.get('programming_languages', []) if resume_data else extract_programming_languages(resume_text)
        languages_str = ', '.join(languages[:5]) if languages else 'General programming'
        
        jd_skills = jd_data.get('required_skills', [])[:5] if jd_data else []
        jd_skills_str = ', '.join(jd_skills) if jd_skills else 'General skills'
        
        return f"""You are a professional technical interviewer conducting a mock interview.

RULES (STRICTLY FOLLOW):
1. Ask ONE question at a time
2. Do NOT explain answers or provide hints
3. Adjust difficulty based on candidate responses
4. Evaluate answers for technical correctness, clarity, and confidence
5. Be concise and realistic - conduct a real interview, not a tutorial
6. Do NOT repeat questions already asked

INTERVIEW CONTEXT:
- Interview Type: TECHNICAL INTERVIEW (TR)
- Experience Level: {experience_level}
- Candidate Skills (from resume): {languages_str}
- Job Requirements: {jd_skills_str}

INTERVIEW FLOW (STRICT ORDER):
1. Introduction question (always first)
2. Resume-based technical questions (projects, technologies, certificates)
3. Programming languages questions (core concepts, practical questions)
4. JD-required technical skills (especially missing/weak skills)
5. Scenario-based problem-solving questions

Be professional, realistic, and assess the candidate's actual technical knowledge."""
    
    else:  # HR Interview
        return f"""You are a professional HR interviewer conducting a mock interview.

RULES (STRICTLY FOLLOW):
1. Ask ONE question at a time
2. Do NOT explain answers or provide hints
3. Focus on communication skills, confidence, and behavioral aspects
4. Evaluate answers for clarity, structure, confidence, and appropriateness
5. Be friendly but professional
6. Do NOT ask deep technical questions (this is an HR interview)

INTERVIEW CONTEXT:
- Interview Type: HR INTERVIEW
- Experience Level: {experience_level}

INTERVIEW FOCUS:
1. Introduction question (always first)
2. Communication skills assessment
3. Behavioral questions (strengths, weaknesses, teamwork)
4. Situational/real-life scenarios
5. Career goals and motivation
6. Confidence and clarity evaluation

Focus on evaluating communication skills, confidence, clarity, and behavioral fit.
Do NOT ask technical questions."""

def determine_phase_tr(question_number: int, resume_data=None, jd_data=None) -> str:
    """
    Determine interview phase for Technical Interview (TR)
    Returns: 'introduction', 'resume', 'programming', 'jd_skills', 'scenario'
    """
    if question_number == 0:
        return 'introduction'
    elif question_number <= 2:
        return 'resume'  # Resume-based questions (projects, technologies, certificates)
    elif question_number <= 4:
        return 'programming'  # Programming languages questions
    elif question_number <= 6:
        return 'jd_skills'  # JD-required skills (especially missing/weak)
    else:
        return 'scenario'  # Scenario-based problem-solving

def determine_phase_hr(question_number: int) -> str:
    """
    Determine interview phase for HR Interview
    Returns: 'introduction', 'communication', 'behavioral', 'situational', 'career'
    """
    if question_number == 0:
        return 'introduction'
    elif question_number <= 2:
        return 'communication'  # Communication skills
    elif question_number <= 4:
        return 'behavioral'  # Behavioral questions
    elif question_number <= 6:
        return 'situational'  # Situational scenarios
    else:
        return 'career'  # Career goals and motivation

def generate_interview_question(interview_type='TR', resume_text='', job_description='',
                                phase='introduction', question_number=0, conversation_history=[],
                                experience_level='fresher', previous_answer_score=None,
                                resume_data=None, jd_data=None):
    """
    Generate interview question based on interview type (TR or HR) and phase
    FIRST QUESTION must always be "Introduce yourself"
    """
    # FIRST QUESTION: Always "Introduce yourself"
    if question_number == 0:
        if interview_type == 'TR':
            return "Introduce yourself."
        else:  # HR
            return "Introduce yourself."
    
    # Use AI to generate questions if API key available
    if Config.AI_API_KEY:
        try:
            history_context = ""
            if conversation_history:
                recent_qa = [msg for msg in conversation_history[-6:] if msg.get('type') in ['question', 'answer']]
                if recent_qa:
                    history_context = "\n\nPrevious Q&A:\n"
                    for msg in recent_qa:
                        if msg['type'] == 'question':
                            history_context += f"Q: {msg['content']}\n"
                        else:
                            history_context += f"A: {msg['content'][:150]}...\n"
            
            # Determine difficulty based on previous answer
            difficulty_hint = ""
            if previous_answer_score is not None:
                if previous_answer_score >= 7:
                    difficulty_hint = "Ask a more challenging question (candidate answered well)."
                elif previous_answer_score >= 4:
                    difficulty_hint = "Ask a medium difficulty question."
                else:
                    difficulty_hint = "Ask a simpler or clarification question (candidate struggled)."
            
            prompt = ""
            
            if interview_type == 'TR':
                # Technical Interview questions
                prompt = generate_tr_question_prompt(phase, resume_text, job_description, 
                                                    resume_data, jd_data, difficulty_hint, 
                                                    experience_level)
            else:
                # HR Interview questions
                prompt = generate_hr_question_prompt(phase, resume_text, difficulty_hint, experience_level)
            
            headers = {
                'Authorization': f'Bearer {Config.AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': get_system_prompt(interview_type, experience_level, resume_text, job_description, resume_data, jd_data)},
                    {'role': 'user', 'content': prompt + history_context}
                ],
                'max_tokens': 200,
                'temperature': 0.7
            }
            
            response = requests.post(Config.AI_API_URL, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                question = data['choices'][0]['message']['content'].strip()
                # Clean up formatting
                question = re.sub(r'^["\']|["\']$', '', question)
                question = re.sub(r'^(Question:|Q:)\s*', '', question, flags=re.IGNORECASE)
                return question.strip()
        except Exception as e:
            print(f"AI API error: {e}")
    
    # Fallback questions
    return get_fallback_question(interview_type, phase, resume_data, jd_data)

def generate_tr_question_prompt(phase, resume_text, job_description, resume_data, jd_data, difficulty_hint, experience_level):
    """Generate prompt for Technical Interview question"""
    if phase == 'resume':
        projects = resume_data.get('projects', [])[:3] if resume_data else []
        projects_str = ', '.join([p.get('name', '') for p in projects]) if projects else 'projects mentioned in resume'
        
        return f"""Generate a TECHNICAL interview question based on the candidate's resume.

Resume Summary: {resume_text[:800] if resume_text else 'Not provided'}
Projects: {projects_str}
{difficulty_hint}

Generate ONE specific technical question about:
- A project mentioned in the resume
- Technologies or frameworks listed
- Certificates (if any)
- Skills mentioned

Question should be:
- Specific to resume content
- Appropriate for {experience_level} level
- {difficulty_hint}
- Tests actual technical knowledge

Return ONLY the question, no additional text."""
    
    elif phase == 'programming':
        languages = resume_data.get('programming_languages', [])[:3] if resume_data else []
        languages_str = ', '.join(languages) if languages else 'programming'
        
        return f"""Generate a TECHNICAL interview question about programming languages.

Candidate's Programming Languages: {languages_str}
{difficulty_hint}

Generate ONE technical question about:
- Core concepts of a programming language mentioned
- Practical programming scenarios
- Data structures or algorithms
- Language-specific features

Question should:
- Test deep understanding
- Be appropriate for {experience_level} level
- {difficulty_hint}

Return ONLY the question, no additional text."""
    
    elif phase == 'jd_skills':
        missing_skills = jd_data.get('missing_skills', [])[:5] if jd_data else []
        missing_skills_str = ', '.join(missing_skills) if missing_skills else 'required skills'
        
        return f"""Generate a TECHNICAL interview question about job-required skills, especially missing/weak skills.

Job Description: {job_description[:800] if job_description else 'Not provided'}
Missing/Weak Skills (HIGH PRIORITY): {missing_skills_str}
{difficulty_hint}

Generate ONE technical question about:
- Skills required in the job description
- Especially focus on missing/weak skills (HIGH PRIORITY)
- How candidate would handle job responsibilities

Question should:
- Focus on skill gaps
- Test ability to learn/adapt
- Be appropriate for {experience_level} level
- {difficulty_hint}

Return ONLY the question, no additional text."""
    
    else:  # scenario
        return f"""Generate a TECHNICAL scenario-based problem-solving question.

Resume: {resume_text[:500] if resume_text else 'Not provided'}
Job Description: {job_description[:500] if job_description else 'Not provided'}
{difficulty_hint}

Generate ONE real-world problem-solving question that:
- Presents a technical scenario
- Requires problem-solving approach
- Tests practical application of knowledge
- Is appropriate for {experience_level} level
- {difficulty_hint}

Return ONLY the question, no additional text."""

def generate_hr_question_prompt(phase, resume_text, difficulty_hint, experience_level):
    """Generate prompt for HR Interview question"""
    if phase == 'communication':
        return f"""Generate an HR interview question to assess COMMUNICATION SKILLS.

Resume: {resume_text[:500] if resume_text else 'Not provided'}
{difficulty_hint}

Generate ONE question that tests:
- Communication clarity
- Articulation ability
- Professional expression

Question should be appropriate for {experience_level} level.
Return ONLY the question, no additional text."""
    
    elif phase == 'behavioral':
        return f"""Generate a BEHAVIORAL interview question.

Resume: {resume_text[:500] if resume_text else 'Not provided'}
{difficulty_hint}

Generate ONE behavioral question about:
- Strengths & weaknesses
- Teamwork experiences
- Conflict handling
- Past experiences

Use STAR method context (Situation, Task, Action, Result).
Return ONLY the question, no additional text."""
    
    elif phase == 'situational':
        return f"""Generate a SITUATIONAL/REAL-LIFE SCENARIO question.

{difficulty_hint}

Generate ONE situational question that:
- Presents a work scenario
- Tests problem-solving approach
- Evaluates decision-making
- Assesses professional judgment

Return ONLY the question, no additional text."""
    
    else:  # career
        return f"""Generate a CAREER GOALS AND MOTIVATION question.

Resume: {resume_text[:500] if resume_text else 'Not provided'}
{difficulty_hint}

Generate ONE question about:
- Career goals
- Motivation
- Future aspirations
- Why they want this role

Return ONLY the question, no additional text."""

def get_fallback_question(interview_type, phase, resume_data=None, jd_data=None):
    """Fallback questions when AI is not available"""
    if interview_type == 'TR':
        languages = resume_data.get('programming_languages', [])[:1] if resume_data else []
        lang = languages[0] if languages else 'Python'
        
        fallback_tr = {
            'resume': [
                f"Tell me about a project mentioned in your resume and the technologies you used.",
                f"Can you explain a technical challenge you faced in one of your projects?",
                "What certificates do you have and how have they helped you?"
            ],
            'programming': [
                f"Explain the difference between list and tuple in {lang}.",
                f"Describe your experience with {lang} data structures.",
                f"What are the key features of {lang} that you find most useful?"
            ],
            'jd_skills': [
                "How does your experience align with the technical requirements mentioned in the job description?",
                "What technical skills from the job description do you need to improve?",
                "How would you approach learning a new technology required for this role?"
            ],
            'scenario': [
                "How would you debug a performance issue in a production system?",
                "Describe how you would design a scalable system architecture.",
                "Explain your approach to handling a critical bug discovered just before a release."
            ]
        }
        import random
        return random.choice(fallback_tr.get(phase, fallback_tr['scenario']))
    
    else:  # HR
        fallback_hr = {
            'communication': [
                "How do you communicate technical concepts to non-technical stakeholders?",
                "Describe a time when you had to explain a complex idea clearly.",
                "How do you ensure effective communication in a team setting?"
            ],
            'behavioral': [
                "What are your strengths and weaknesses?",
                "Tell me about a time you worked effectively in a team.",
                "Describe a situation where you handled a conflict at work."
            ],
            'situational': [
                "How would you handle a situation where you disagree with your manager's decision?",
                "What would you do if you were assigned a project outside your expertise?",
                "How do you prioritize tasks when you have multiple urgent deadlines?"
            ],
            'career': [
                "Where do you see yourself in 5 years?",
                "Why do you want to work at this company?",
                "What motivates you in your career?"
            ]
        }
        import random
        return random.choice(fallback_hr.get(phase, fallback_hr['career']))

def evaluate_answer(question, answer, interview_type='TR', phase='introduction', 
                   resume_text='', job_description=''):
    """
    Evaluate answer with scoring (0-10 scale for each metric)
    For TR: Focus on correctness, clarity, confidence
    For HR: Focus on communication, clarity, confidence, structure
    Returns: {
        'feedback': str,
        'correctness': float (0-10),
        'clarity': float (0-10),
        'confidence': float (0-10),
        'overall_score': float (0-10) - weighted average
    }
    """
    if Config.AI_API_KEY:
        try:
            # Different evaluation criteria for TR vs HR
            if interview_type == 'TR':
                eval_criteria = """1. Correctness (0-10): Technical accuracy and correctness of the answer
2. Clarity (0-10): How clear, well-structured, and understandable is the answer
3. Confidence (0-10): How confident and articulate does the candidate sound"""
            else:  # HR
                eval_criteria = """1. Correctness (0-10): Appropriateness and relevance of the answer (not technical correctness)
2. Clarity (0-10): Communication clarity, structure, and articulation
3. Confidence (0-10): Confidence level, professional tone, and self-assurance"""
            
            # Determine if this is a behavioral/situational question that would benefit from STAR method
            is_behavioral = any(keyword in question.lower() for keyword in [
                'tell me about', 'describe a time', 'situation', 'challenge', 'conflict',
                'problem', 'example', 'experience', 'handled', 'dealt with', 'worked with',
                'team', 'difficult', 'stress', 'pressure', 'mistake', 'failure', 'success',
                'how did you', 'what did you', 'when did you', 'give an example'
            ])
            
            # Determine if answer lacks structure (analyze before scoring)
            answer_lower = answer.lower()
            answer_length = len(answer.split())
            has_structure_indicators = any(indicator in answer_lower for indicator in [
                'first', 'second', 'then', 'next', 'finally', 'initially', 'after that',
                'situation', 'task', 'action', 'result', 'because', 'therefore', 'however',
                'in addition', 'furthermore', 'specifically', 'for example', 'for instance'
            ])
            lacks_structure = not has_structure_indicators and (answer_length < 30 or len(answer.split('.')) < 2)
            is_too_short = answer_length < 20
            
            # Build structured feedback guidance based on question and answer analysis
            feedback_guidance = ""
            if is_behavioral and (lacks_structure or is_too_short):
                feedback_guidance = """
CRITICAL: The answer lacks structure. You MUST provide specific guidance on HOW to structure behavioral answers using the STAR method.

Your feedback MUST include:
1. Explain the STAR method clearly:
   - Situation: Set the context (when, where, who was involved)
   - Task: What was your responsibility or goal?
   - Action: What specific steps did YOU take? (Use 'I' not 'we')
   - Result: What was the outcome? Quantify if possible (numbers, percentages, impact)

2. Show how to apply STAR to THIS specific question with a brief example structure

3. Be specific and actionable - don't just say "use STAR", explain HOW

Example feedback format:
"Your answer lacks structure. Use the STAR method to organize your response:
- Situation: Set the context (when, where, who was involved)
- Task: What was your responsibility or goal?
- Action: What specific steps did YOU take? (Use 'I' not 'we')
- Result: What was the outcome? Quantify if possible.

For this question about [topic], structure it like: [brief example showing STAR structure]"
"""
            elif interview_type == 'TR' and (lacks_structure or is_too_short):
                feedback_guidance = """
CRITICAL: The answer lacks clarity or structure. You MUST provide specific guidance on HOW to improve technical communication.

Your feedback MUST include:
1. Explain what specific technical details are missing
2. Suggest a clear structure (e.g., "Start with concept, then explain how it works, then give an example")
3. Provide concrete examples of what to add

Example feedback format:
"Your answer needs more structure. Try this format:
1. Define the concept clearly (what is it?)
2. Explain how it works (with technical details, algorithms, or mechanisms)
3. Provide a real-world example or use case
4. Mention any relevant technologies, tools, or best practices

For example, if explaining [concept], you could add: [specific technical detail]"
"""
            elif interview_type == 'HR' and (lacks_structure or is_too_short):
                feedback_guidance = """
CRITICAL: The answer lacks clarity or structure. You MUST provide specific guidance on HOW to improve communication.

Your feedback MUST include:
1. Explain what specific information is missing
2. Suggest a clear structure (e.g., "Start with your point, then explain with examples, then conclude")
3. Provide concrete examples of what to add

Example feedback format:
"Your answer needs more structure. Try this format:
1. State your main point clearly (direct answer to the question)
2. Provide a specific example from your experience (be concrete, not vague)
3. Explain what you learned or the outcome (show impact)
4. Connect it back to the question (why this matters)

For example, instead of saying 'I worked on a project', say 'I led a team of 5 developers to build a mobile app that increased user engagement by 30%'"
"""
            
            prompt = f"""Evaluate this interview answer and provide scores.

Interview Type: {interview_type} Interview
Question: {question}
Candidate's Answer: {answer}
Phase: {phase}
Resume Context: {resume_text[:300] if resume_text else 'Not provided'}

Evaluate and provide:
{eval_criteria}

{feedback_guidance}

Then provide constructive feedback that:
- Acknowledges what was done well (if anything)
- Explains SPECIFICALLY HOW to improve (not just "improve communication")
- Provides structured guidance with examples
- Is encouraging and professional
- If structure is lacking, include specific frameworks (STAR method, etc.) with examples

Return your response in this EXACT JSON format:
{{
    "correctness": <number 0-10>,
    "clarity": <number 0-10>,
    "confidence": <number 0-10>,
    "feedback": "<your detailed feedback with specific HOW-TO guidance>"
}}"""
            
            headers = {
                'Authorization': f'Bearer {Config.AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': f'You are an experienced {interview_type} interview evaluator. Provide accurate scores and constructive feedback in JSON format.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 500,
                'temperature': 0.5
            }
            
            response = requests.post(Config.AI_API_URL, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content'].strip()
                
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\{[^{}]*"correctness"[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        eval_data = json.loads(json_match.group())
                    else:
                        eval_data = json.loads(content)
                    
                    correctness = float(eval_data.get('correctness', 5))
                    clarity = float(eval_data.get('clarity', 5))
                    confidence = float(eval_data.get('confidence', 5))
                    feedback = eval_data.get('feedback', 'Thank you for your answer.')
                    
                    # Calculate overall score (weighted average)
                    # For TR: correctness 50%, clarity 30%, confidence 20%
                    # For HR: correctness 30%, clarity 40%, confidence 30%
                    if interview_type == 'TR':
                        overall_score = (correctness * 0.5 + clarity * 0.3 + confidence * 0.2)
                    else:
                        overall_score = (correctness * 0.3 + clarity * 0.4 + confidence * 0.3)
                    
                    return {
                        'feedback': feedback,
                        'correctness': round(correctness, 1),
                        'clarity': round(clarity, 1),
                        'confidence': round(confidence, 1),
                        'overall_score': round(overall_score, 1)
                    }
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f"Error parsing AI evaluation: {e}")
        except Exception as e:
            print(f"AI API error: {e}")
    
    # Fallback evaluation
    return {
        'feedback': get_fallback_feedback(interview_type, phase),
        'correctness': 6.0,
        'clarity': 6.0,
        'confidence': 6.0,
        'overall_score': 6.0
    }

def get_fallback_feedback(interview_type, phase):
    """Fallback feedback when AI is not available"""
    if interview_type == 'TR':
        return "Your answer demonstrates understanding. Consider providing more specific technical examples and details."
    else:
        return "Good response. Try to be more specific with examples and connect your answer to your experiences."

def calculate_final_score_tr(answers: list) -> dict:
    """
    Calculate final score for Technical Interview (out of 100)
    Scoring breakdown:
    - Introduction: 10%
    - Projects & Resume Knowledge: 25%
    - Programming Skills: 35%
    - JD Gap Skills: 20%
    - Communication: 10%
    """
    if not answers:
        return {'total_score': 0.0, 'breakdown': {}}
    
    # Group answers by phase
    introduction_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'introduction']
    resume_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'resume']
    programming_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'programming']
    jd_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'jd_skills']
    scenario_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'scenario']
    
    # Calculate phase averages (out of 10)
    intro_avg = sum(introduction_scores) / len(introduction_scores) if introduction_scores else 0
    resume_avg = sum(resume_scores) / len(resume_scores) if resume_scores else 0
    programming_avg = sum(programming_scores) / len(programming_scores) if programming_scores else 0
    jd_avg = sum(jd_scores) / len(jd_scores) if jd_scores else 0
    
    # Communication score is average of all clarity scores
    communication_scores = [a.get('clarity_score', 0) for a in answers]
    communication_avg = sum(communication_scores) / len(communication_scores) if communication_scores else 0
    
    # Convert to percentage (out of 100) with weights
    introduction_pct = (intro_avg / 10) * 10  # 10% weight
    projects_resume_pct = (resume_avg / 10) * 25  # 25% weight
    programming_pct = (programming_avg / 10) * 35  # 35% weight
    jd_gap_pct = (jd_avg / 10) * 20  # 20% weight
    communication_pct = (communication_avg / 10) * 10  # 10% weight
    
    total_score = introduction_pct + projects_resume_pct + programming_pct + jd_gap_pct + communication_pct
    
    return {
        'total_score': round(total_score, 1),
        'breakdown': {
            'introduction_score': round(intro_avg, 1),
            'projects_resume_score': round(resume_avg, 1),
            'programming_score': round(programming_avg, 1),
            'jd_gap_skills_score': round(jd_avg, 1),
            'communication_score': round(communication_avg, 1)
        }
    }

def calculate_final_score_hr(answers: list) -> dict:
    """
    Calculate final score for HR Interview (out of 100)
    Scoring breakdown:
    - Introduction: 15%
    - Communication Skills: 35%
    - Confidence & Clarity: 25%
    - Behavioral & Situational Answers: 25%
    """
    if not answers:
        return {'total_score': 0.0, 'breakdown': {}}
    
    # Group answers by phase
    introduction_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'introduction']
    communication_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'communication']
    behavioral_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'behavioral']
    situational_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'situational']
    career_scores = [a.get('overall_score', 0) for a in answers if a.get('phase') == 'career']
    
    # Calculate phase averages
    intro_avg = sum(introduction_scores) / len(introduction_scores) if introduction_scores else 0
    communication_avg = sum(communication_scores) / len(communication_scores) if communication_scores else 0
    
    # Confidence is average of all confidence scores
    confidence_scores = [a.get('confidence_score', 0) for a in answers]
    confidence_avg = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    # Behavioral & Situational combined
    behavioral_combined = behavioral_scores + situational_scores + career_scores
    behavioral_avg = sum(behavioral_combined) / len(behavioral_combined) if behavioral_combined else 0
    
    # Convert to percentage (out of 100) with weights
    introduction_pct = (intro_avg / 10) * 15  # 15% weight
    communication_pct = (communication_avg / 10) * 35  # 35% weight
    confidence_pct = (confidence_avg / 10) * 25  # 25% weight
    behavioral_pct = (behavioral_avg / 10) * 25  # 25% weight
    
    total_score = introduction_pct + communication_pct + confidence_pct + behavioral_pct
    
    return {
        'total_score': round(total_score, 1),
        'breakdown': {
            'hr_introduction_score': round(intro_avg, 1),
            'hr_communication_score': round(communication_avg, 1),
            'hr_confidence_score': round(confidence_avg, 1),
            'hr_behavioral_score': round(behavioral_avg, 1)
        }
    }

def generate_interview_summary(conversation_history, interview_type='TR', final_score=0.0, 
                              resume_text='', job_description='', score_breakdown=None):
    """
    Generate final interview summary with strengths, weaknesses, and suggestions
    Returns dictionary with summary, strengths, weaknesses, improvements, suggested_resources
    """
    if not Config.AI_API_KEY:
        return {
            'summary': "Interview completed. Review your answers and continue practicing.",
            'strengths': [],
            'weaknesses': [],
            'improvements': [],
            'suggested_resources': []
        }
    
    try:
        # Build conversation summary
        qa_pairs = []
        for msg in conversation_history:
            if msg.get('type') == 'question':
                qa_pairs.append(f"Q: {msg['content']}")
            elif msg.get('type') == 'answer':
                qa_pairs.append(f"A: {msg['content'][:200]}")
        
        conversation_summary = '\n'.join(qa_pairs[-15:])  # Last 15 Q&A
        
        breakdown_str = json.dumps(score_breakdown) if score_breakdown else "Not available"
        
        prompt = f"""Provide a comprehensive {interview_type} interview summary and analysis.

Final Score: {final_score:.1f}/100
Score Breakdown: {breakdown_str}

Candidate Resume: {resume_text[:500] if resume_text else 'Not provided'}
Job Description: {job_description[:500] if job_description else 'Not provided'}

Interview Conversation:
{conversation_summary}

Provide a detailed analysis in JSON format with:
1. "summary": Comprehensive summary (3-4 paragraphs) covering overall performance, key strengths, areas for improvement, and specific suggestions
2. "strengths": Array of 3-5 key strengths demonstrated
3. "weaknesses": Array of 3-5 areas that need improvement
4. "weak_skills": Array of 3-5 SPECIFIC technical skills or topics that were weak (e.g., "SQL Joins", "Python Decorators", "System Design", "Data Structures - Trees", "Communication - STAR Method"). Be specific and actionable.
5. "improvements": Array of 3-5 specific actionable improvement suggestions with HOW-TO guidance

IMPORTANT for "improvements": Each improvement MUST explain HOW to improve, not just what to improve.
- For communication issues: Explain specific structures (STAR method, technical explanation format, etc.)
- For technical gaps: Provide specific learning paths or resources
- For confidence issues: Give concrete practice strategies

Example improvements:
- "Improve answer structure using STAR method: Situation (context), Task (your goal), Action (specific steps you took), Result (quantified outcome)"
- "Enhance technical explanations by following this format: 1) Define concept, 2) Explain mechanism, 3) Provide example, 4) Mention tools/technologies"
6. "suggested_resources": Array of 2-3 suggested learning resources/courses based on weak areas

Be constructive, professional, and actionable. Focus on helping the candidate improve.

Return ONLY valid JSON in this format:
{{
    "summary": "<comprehensive summary text>",
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...],
    "improvements": ["improvement1", "improvement2", ...],
    "suggested_resources": ["resource1", "resource2", ...]
}}"""
        
        headers = {
            'Authorization': f'Bearer {Config.AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': f'You are an interview coach providing comprehensive, constructive feedback for {interview_type} interviews. Return only valid JSON.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 800,
            'temperature': 0.7
        }
        
        response = requests.post(Config.AI_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content'].strip()
            
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*"summary".*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(content)
                
                return {
                    'summary': result.get('summary', 'Interview completed.'),
                    'strengths': result.get('strengths', []),
                    'weaknesses': result.get('weaknesses', []),
                    'weak_skills': result.get('weak_skills', []),
                    'improvements': result.get('improvements', []),
                    'suggested_resources': result.get('suggested_resources', [])
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"Error parsing AI summary: {e}")
    except Exception as e:
        print(f"Error generating summary: {e}")
    
    # Fallback
    return {
        'summary': f"Interview completed with a score of {final_score:.1f}/100. Continue practicing to improve your {interview_type} interview skills.",
        'strengths': ['Willingness to participate', 'Professional attitude'],
        'weaknesses': ['Need more practice', 'Technical depth'],
        'weak_skills': ['General Technical Concepts', 'Communication Skills'],
        'improvements': ['Practice more interview questions', 'Review technical concepts'],
        'suggested_resources': ['Interview preparation courses', 'Technical skill development']
    }

def generate_practice_materials(weak_skills, interview_type='TR'):
    """
    Generate practice materials (questions, quizzes, coding problems) based on weak skills detected from interview
    
    Args:
        weak_skills: List of specific weak skills/topics (e.g., ["SQL Joins", "Python Decorators"])
        interview_type: 'TR' or 'HR'
    
    Returns:
        Dictionary with practice recommendations for each weak skill
    """
    if not weak_skills or not Config.AI_API_KEY:
        return {}
    
    try:
        weak_skills_str = ', '.join(weak_skills[:5])  # Limit to top 5
        
        prompt = f"""Based on the following weak skills detected from an interview, generate specific practice recommendations.

Weak Skills Detected: {weak_skills_str}
Interview Type: {interview_type}

For EACH weak skill, provide practice recommendations in this EXACT JSON format:
{{
    "skill_name": "<exact skill name>",
    "mcq_count": <number of MCQ questions recommended (0-10)>,
    "coding_count": <number of coding problems recommended (0-5)>,
    "interview_questions_count": <number of interview-style questions (0-3)>,
    "practice_description": "<brief description of what to practice>",
    "difficulty_level": "<beginner/intermediate/advanced>"
}}

Guidelines:
- For technical skills (SQL, Python, Algorithms, etc.): Recommend MCQs and coding problems
- For communication/behavioral skills: Recommend interview questions and MCQs
- For conceptual topics: Recommend MCQs and interview questions
- Be specific: "SQL Joins" should get SQL-related practice, not general database questions

Return ONLY valid JSON array:
[
    {{"skill_name": "SQL Joins", "mcq_count": 5, "coding_count": 2, "interview_questions_count": 1, "practice_description": "Practice writing JOIN queries (INNER, LEFT, RIGHT, FULL)", "difficulty_level": "intermediate"}},
    ...
]"""
        
        headers = {
            'Authorization': f'Bearer {Config.AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are an educational content generator. Return only valid JSON arrays.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 800,
            'temperature': 0.7
        }
        
        response = requests.post(Config.AI_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content'].strip()
            
            try:
                # Extract JSON array from response
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    practice_data = json.loads(json_match.group())
                    
                    # Convert to dictionary keyed by skill name
                    result = {}
                    for item in practice_data:
                        skill_name = item.get('skill_name', '')
                        if skill_name:
                            result[skill_name] = {
                                'mcq_count': item.get('mcq_count', 0),
                                'coding_count': item.get('coding_count', 0),
                                'interview_questions_count': item.get('interview_questions_count', 0),
                                'practice_description': item.get('practice_description', ''),
                                'difficulty_level': item.get('difficulty_level', 'intermediate')
                            }
                    return result
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"Error parsing practice materials: {e}")
    except Exception as e:
        print(f"Error generating practice materials: {e}")
    
    # Fallback: Generate basic recommendations
    result = {}
    for skill in weak_skills[:5]:
        # Determine practice type based on skill name
        skill_lower = skill.lower()
        if any(keyword in skill_lower for keyword in ['sql', 'database', 'query']):
            result[skill] = {
                'mcq_count': 5,
                'coding_count': 2,
                'interview_questions_count': 1,
                'practice_description': f'Practice {skill} with MCQs and coding problems',
                'difficulty_level': 'intermediate'
            }
        elif any(keyword in skill_lower for keyword in ['algorithm', 'data structure', 'coding', 'programming']):
            result[skill] = {
                'mcq_count': 3,
                'coding_count': 3,
                'interview_questions_count': 1,
                'practice_description': f'Practice {skill} with coding problems and MCQs',
                'difficulty_level': 'intermediate'
            }
        elif any(keyword in skill_lower for keyword in ['communication', 'behavioral', 'star']):
            result[skill] = {
                'mcq_count': 5,
                'coding_count': 0,
                'interview_questions_count': 3,
                'practice_description': f'Practice {skill} with interview questions and MCQs',
                'difficulty_level': 'beginner'
            }
        else:
            result[skill] = {
                'mcq_count': 5,
                'coding_count': 1,
                'interview_questions_count': 2,
                'practice_description': f'Practice {skill} with various question types',
                'difficulty_level': 'intermediate'
            }
    
    return result

