"""
AI Chatbot utilities for virtual interviews with structured flow
"""
import requests
import json
import re
from config import Config

def get_system_prompt(interview_type='technical', experience_level='fresher', resume_text='', job_description=''):
    """
    Generate system prompt to "train" the AI interviewer
    This locks AI behavior for the entire interview
    """
    # Extract programming languages from resume
    languages = extract_programming_languages(resume_text)
    languages_str = ', '.join(languages) if languages else 'General programming'
    
    # Extract key skills from JD
    jd_skills = extract_skills_from_jd(job_description)
    jd_skills_str = ', '.join(jd_skills[:5]) if jd_skills else 'General skills'
    
    system_prompt = f"""You are a professional interview panelist conducting a mock interview.

RULES (STRICTLY FOLLOW):
1. Ask ONE question at a time
2. Do NOT explain answers or provide hints
3. Adjust difficulty based on candidate responses
4. Evaluate answers for correctness, clarity, and confidence
5. Be concise and realistic - conduct a real interview, not a tutorial
6. Do NOT repeat questions already asked

INTERVIEW CONTEXT:
- Interview Type: {interview_type}
- Experience Level: {experience_level}
- Candidate Skills (from resume): {languages_str}
- Job Requirements: {jd_skills_str}

INTERVIEW FLOW:
1. Start with introduction question
2. Then ask resume-based questions (focus on mentioned skills/languages)
3. Then ask job description related questions
4. End with general technical/behavioral questions

Be professional, realistic, and assess the candidate's actual knowledge."""
    
    return system_prompt

def extract_programming_languages(resume_text):
    """Extract programming languages mentioned in resume"""
    if not resume_text:
        return []
    
    languages = ['Python', 'Java', 'JavaScript', 'C++', 'C', 'C#', 'PHP', 'Ruby', 'Go', 'Rust', 
                 'Swift', 'Kotlin', 'TypeScript', 'SQL', 'HTML', 'CSS', 'React', 'Angular', 
                 'Vue', 'Node.js', 'Django', 'Flask', 'Spring', '.NET', 'ASP.NET']
    
    found_languages = []
    resume_lower = resume_text.lower()
    
    for lang in languages:
        if lang.lower() in resume_lower or lang in resume_text:
            found_languages.append(lang)
    
    return found_languages[:5]  # Return top 5

def extract_skills_from_jd(job_description):
    """Extract key skills/technologies from job description"""
    if not job_description:
        return []
    
    # Common tech keywords
    keywords = ['Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes', 
                'React', 'Angular', 'Node.js', 'Machine Learning', 'AI', 'Data Science',
                'DevOps', 'Cloud', 'API', 'REST', 'GraphQL', 'MongoDB', 'PostgreSQL',
                'Git', 'Agile', 'Scrum', 'Microservices', 'Spring', 'Django', 'Flask']
    
    found_skills = []
    jd_lower = job_description.lower()
    
    for keyword in keywords:
        if keyword.lower() in jd_lower or keyword in job_description:
            found_skills.append(keyword)
    
    return found_skills[:10]  # Return top 10

def generate_interview_question(resume_text, job_description, phase='introduction', 
                                question_number=0, conversation_history=[], 
                                interview_type='technical', experience_level='fresher',
                                previous_answer_score=None):
    """
    Generate interview question based on structured flow:
    - phase: 'introduction', 'resume', 'jd', 'general'
    - Adaptive difficulty based on previous_answer_score
    """
    # FIRST QUESTION: Always "Tell me about yourself"
    if question_number == 0:
        if interview_type == 'technical':
            return "Tell me about yourself and your technical background."
        else:
            return "Tell me about yourself."
    
    if Config.AI_API_KEY:
        try:
            # Build conversation context
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
                    difficulty_hint = "Ask a more challenging question (the candidate answered well)."
                elif previous_answer_score >= 4:
                    difficulty_hint = "Ask a medium difficulty question."
                else:
                    difficulty_hint = "Ask a simpler or clarification question (the candidate struggled)."
            
            # Phase-specific prompts
            if phase == 'resume':
                languages = extract_programming_languages(resume_text)
                languages_str = ', '.join(languages) if languages else 'programming'
                prompt = f"""Generate a {interview_type} interview question based on the candidate's resume.

Candidate Resume Summary:
{resume_text[:1000]}

Programming Languages/Skills Mentioned: {languages_str}
{difficulty_hint}

Generate ONE specific question about:
- A programming language mentioned in the resume (e.g., Python, Java, JavaScript)
- A project or technology mentioned
- A skill or framework listed

Question should be:
- Specific to their resume content
- Appropriate for {experience_level} level
- {difficulty_hint}
- Not generic or too broad

Return ONLY the question, no additional text."""
            
            elif phase == 'jd':
                jd_skills = extract_skills_from_jd(job_description)
                jd_skills_str = ', '.join(jd_skills[:5]) if jd_skills else 'general requirements'
                prompt = f"""Generate a {interview_type} interview question based on the job description.

Job Description Summary:
{job_description[:1000]}

Key Requirements: {jd_skills_str}
{difficulty_hint}

Generate ONE specific question about:
- A technology or skill required in the job description
- A responsibility or requirement mentioned
- How the candidate's experience relates to the role

Question should be:
- Directly related to job requirements
- Appropriate for {experience_level} level
- {difficulty_hint}
- Assesses fit for the role

Return ONLY the question, no additional text."""
            
            else:  # general phase
                prompt = f"""Generate a {interview_type} interview question.

Resume Summary: {resume_text[:500] if resume_text else 'Not provided'}
Job Description: {job_description[:500] if job_description else 'Not provided'}
{difficulty_hint}

Generate ONE general {interview_type} question that:
- Tests fundamental knowledge
- Is appropriate for {experience_level} level
- {difficulty_hint}
- Is relevant to the role

Return ONLY the question, no additional text."""
            
            headers = {
                'Authorization': f'Bearer {Config.AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': get_system_prompt(interview_type, experience_level, resume_text, job_description)},
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
                question = question.replace('"', '').replace("'", "")
                if question.startswith('Question:'):
                    question = question.replace('Question:', '').strip()
                if question.startswith('Q:'):
                    question = question.replace('Q:', '').strip()
                return question
        except requests.exceptions.RequestException as e:
            print(f"AI API request error: {e}")
        except Exception as e:
            print(f"AI API error: {e}")
    
    # Fallback questions based on phase
    return get_fallback_question(phase, interview_type, resume_text, job_description)

def get_fallback_question(phase, interview_type, resume_text, job_description):
    """Fallback questions when AI is not available"""
    languages = extract_programming_languages(resume_text)
    
    if phase == 'resume' and languages:
        lang = languages[0]
        questions = [
            f"You mentioned {lang} in your resume. Can you explain the difference between list and tuple in {lang}?",
            f"Tell me about a project where you used {lang}.",
            f"What are the key features of {lang} that you find most useful?",
            f"Describe your experience with {lang} data structures."
        ]
        import random
        return random.choice(questions)
    
    elif phase == 'jd' and job_description:
        questions = [
            "How does your experience align with the requirements mentioned in the job description?",
            "What skills from the job description do you possess?",
            "Can you explain how you would handle the responsibilities mentioned in this role?",
            "What challenges do you anticipate in this position?"
        ]
        import random
        return random.choice(questions)
    
    else:
        questions = {
            'technical': [
                "Explain a challenging technical problem you solved recently.",
                "Describe your experience with data structures and algorithms.",
                "How do you approach debugging a complex issue?",
                "What is your preferred programming language and why?"
            ],
            'hr': [
                "Why do you want to work at this company?",
                "What are your strengths and weaknesses?",
                "Where do you see yourself in 5 years?",
                "How do you handle stress and tight deadlines?"
            ],
            'behavioral': [
                "Describe a time you worked in a team.",
                "Tell me about a project you're proud of.",
                "How do you handle conflicts in the workplace?",
                "Describe a situation where you had to learn something new quickly."
            ]
        }
        import random
        question_list = questions.get(interview_type, questions['technical'])
        return random.choice(question_list)

def evaluate_answer(question, answer, question_type='technical', resume_text='', job_description=''):
    """
    Evaluate student's answer with scoring
    Returns: {
        'feedback': str,
        'correctness': int (0-10),
        'clarity': int (0-10),
        'confidence': int (0-10),
        'overall_score': float (0-10)
    }
    """
    if Config.AI_API_KEY:
        try:
            prompt = f"""Evaluate this interview answer and provide scores.

Question: {question}
Candidate's Answer: {answer}
Question Type: {question_type}
Resume Context: {resume_text[:300] if resume_text else 'Not provided'}

Evaluate and provide:
1. Correctness (0-10): How accurate and technically correct is the answer?
2. Clarity (0-10): How clear and well-structured is the answer?
3. Confidence (0-10): How confident and articulate does the candidate sound?

Then provide brief constructive feedback (2-3 sentences) that:
- Acknowledges what was done well
- Suggests specific improvements
- Is encouraging and professional

Return your response in this EXACT JSON format:
{{
    "correctness": <number 0-10>,
    "clarity": <number 0-10>,
    "confidence": <number 0-10>,
    "feedback": "<your feedback text>"
}}"""
            
            headers = {
                'Authorization': f'Bearer {Config.AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are an experienced interview evaluator. Provide accurate scores and constructive feedback in JSON format.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 300,
                'temperature': 0.5
            }
            
            response = requests.post(Config.AI_API_URL, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content'].strip()
                
                # Try to parse JSON from response
                try:
                    # Extract JSON from response (might have markdown code blocks)
                    json_match = re.search(r'\{[^{}]*"correctness"[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        eval_data = json.loads(json_match.group())
                    else:
                        # Try parsing entire content
                        eval_data = json.loads(content)
                    
                    correctness = int(eval_data.get('correctness', 5))
                    clarity = int(eval_data.get('clarity', 5))
                    confidence = int(eval_data.get('confidence', 5))
                    feedback = eval_data.get('feedback', 'Thank you for your answer.')
                    
                    # Calculate overall score (weighted average)
                    overall_score = (correctness * 0.5 + clarity * 0.3 + confidence * 0.2)
                    
                    return {
                        'feedback': feedback,
                        'correctness': correctness,
                        'clarity': clarity,
                        'confidence': confidence,
                        'overall_score': round(overall_score, 1)
                    }
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f"Error parsing AI evaluation: {e}")
                    # Fall through to default evaluation
        except requests.exceptions.RequestException as e:
            print(f"AI API request error: {e}")
        except Exception as e:
            print(f"AI API error: {e}")
    
    # Fallback evaluation
    return {
        'feedback': get_fallback_feedback(question_type),
        'correctness': 6,
        'clarity': 6,
        'confidence': 6,
        'overall_score': 6.0
    }

def get_fallback_feedback(question_type):
    """Fallback feedback when AI is not available"""
    feedback_templates = {
        'technical': "Your answer demonstrates understanding. Consider providing more specific examples and technical details.",
        'hr': "Good response. Try to connect your answer more directly to the company's values and your career goals.",
        'behavioral': "You've provided a relevant example. Remember to use the STAR method (Situation, Task, Action, Result) for behavioral questions."
    }
    return feedback_templates.get(question_type, "Thank you for your answer. Consider providing more specific details and examples.")

def generate_interview_summary(conversation_history, resume_text, job_description):
    """
    Generate final interview summary with strengths, weaknesses, and suggestions
    """
    if not Config.AI_API_KEY:
        return "Interview completed. Review your answers and continue practicing."
    
    try:
        # Build conversation summary
        qa_pairs = []
        scores = []
        for i, msg in enumerate(conversation_history):
            if msg.get('type') == 'question':
                qa_pairs.append(f"Q{i//2 + 1}: {msg['content']}")
            elif msg.get('type') == 'answer':
                qa_pairs.append(f"A{i//2 + 1}: {msg['content'][:200]}")
                if 'score' in msg:
                    scores.append(msg['score'])
        
        conversation_summary = '\n'.join(qa_pairs[-10:])  # Last 10 Q&A
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        prompt = f"""Provide a comprehensive interview summary.

Candidate Resume: {resume_text[:500] if resume_text else 'Not provided'}
Job Description: {job_description[:500] if job_description else 'Not provided'}
Average Score: {avg_score:.1f}/10

Interview Conversation:
{conversation_summary}

Provide a summary (3-4 paragraphs) covering:
1. Overall performance assessment
2. Key strengths demonstrated
3. Areas for improvement
4. Specific suggestions for better interview performance
5. Skill gaps identified

Be constructive, professional, and actionable."""
        
        headers = {
            'Authorization': f'Bearer {Config.AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are an interview coach providing comprehensive, constructive feedback.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.7
        }
        
        response = requests.post(Config.AI_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
    
    return "Interview completed. Continue practicing to improve your interview skills."
