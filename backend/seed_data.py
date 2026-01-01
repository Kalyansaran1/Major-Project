"""
Seed initial data for the platform
"""
from models import db, User, Company, Question
import json

def seed_initial_data():
    """Seed database with initial data"""
    
    # Check if data already exists
    if User.query.first():
        print("Database already seeded. Skipping...")
        return
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@interviewplatform.com',
        role='admin',
        full_name='System Administrator'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create faculty user
    faculty = User(
        username='faculty1',
        email='faculty@interviewplatform.com',
        role='faculty',
        full_name='Dr. John Smith'
    )
    faculty.set_password('faculty123')
    db.session.add(faculty)
    
    # Create sample student
    student = User(
        username='student1',
        email='student@interviewplatform.com',
        role='student',
        full_name='Alice Johnson'
    )
    student.set_password('student123')
    db.session.add(student)
    
    # Create companies
    companies_data = [
        {'name': 'Google', 'description': 'Tech giant specializing in search and cloud services'},
        {'name': 'Microsoft', 'description': 'Leading software and cloud computing company'},
        {'name': 'Amazon', 'description': 'E-commerce and cloud services leader'},
        {'name': 'Apple', 'description': 'Consumer electronics and software company'},
    ]
    
    companies = {}
    for comp_data in companies_data:
        company = Company(**comp_data)
        db.session.add(company)
        companies[comp_data['name']] = company
    
    db.session.flush()
    
    # Create sample coding questions
    coding_questions = [
        {
            'title': 'Two Sum',
            'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
            'type': 'coding',
            'difficulty': 'easy',
            'company_id': companies['Google'].id,
            'tags': 'array,hashmap',
            'created_by': faculty.id,
            'test_cases': json.dumps([
                {'input': '[2,7,11,15]\n9', 'output': '[0,1]'},
                {'input': '[3,2,4]\n6', 'output': '[1,2]'},
                {'input': '[3,3]\n6', 'output': '[0,1]'}
            ]),
            'starter_code': 'def twoSum(nums, target):\n    # Your code here\n    pass',
            'solution': 'def twoSum(nums, target):\n    hashmap = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in hashmap:\n            return [hashmap[complement], i]\n        hashmap[num] = i\n    return []'
        },
        {
            'title': 'Reverse Linked List',
            'description': 'Given the head of a singly linked list, reverse the list, and return the reversed list.',
            'type': 'coding',
            'difficulty': 'easy',
            'company_id': companies['Microsoft'].id,
            'tags': 'linked-list,recursion',
            'created_by': faculty.id,
            'test_cases': json.dumps([
                {'input': '[1,2,3,4,5]', 'output': '[5,4,3,2,1]'},
                {'input': '[1,2]', 'output': '[2,1]'},
                {'input': '[]', 'output': '[]'}
            ]),
            'starter_code': 'def reverseList(head):\n    # Your code here\n    pass',
            'solution': 'def reverseList(head):\n    prev = None\n    current = head\n    while current:\n        next_temp = current.next\n        current.next = prev\n        prev = current\n        current = next_temp\n    return prev'
        },
        {
            'title': 'Valid Parentheses',
            'description': 'Given a string s containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.',
            'type': 'coding',
            'difficulty': 'easy',
            'company_id': companies['Amazon'].id,
            'tags': 'stack,string',
            'created_by': faculty.id,
            'test_cases': json.dumps([
                {'input': '"()"', 'output': 'True'},
                {'input': '"()[]{}"', 'output': 'True'},
                {'input': '"(]"', 'output': 'False'}
            ]),
            'starter_code': 'def isValid(s):\n    # Your code here\n    pass',
            'solution': 'def isValid(s):\n    stack = []\n    mapping = {")": "(", "}": "{", "]": "["}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else "#"\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return not stack'
        },
        {
            'title': 'Merge Two Sorted Lists',
            'description': 'Merge two sorted linked lists and return it as a sorted list.',
            'type': 'coding',
            'difficulty': 'medium',
            'company_id': companies['Apple'].id,
            'tags': 'linked-list,merge',
            'created_by': faculty.id,
            'test_cases': json.dumps([
                {'input': '[1,2,4]\n[1,3,4]', 'output': '[1,1,2,3,4,4]'},
                {'input': '[]\n[]', 'output': '[]'},
                {'input': '[]\n[0]', 'output': '[0]'}
            ]),
            'starter_code': 'def mergeTwoLists(l1, l2):\n    # Your code here\n    pass',
            'solution': 'def mergeTwoLists(l1, l2):\n    dummy = ListNode(0)\n    current = dummy\n    while l1 and l2:\n        if l1.val < l2.val:\n            current.next = l1\n            l1 = l1.next\n        else:\n            current.next = l2\n            l2 = l2.next\n        current = current.next\n    current.next = l1 or l2\n    return dummy.next'
        },
        {
            'title': 'Longest Substring Without Repeating Characters',
            'description': 'Given a string s, find the length of the longest substring without repeating characters.',
            'type': 'coding',
            'difficulty': 'medium',
            'company_id': companies['Google'].id,
            'tags': 'string,sliding-window',
            'created_by': faculty.id,
            'test_cases': json.dumps([
                {'input': '"abcabcbb"', 'output': '3'},
                {'input': '"bbbbb"', 'output': '1'},
                {'input': '"pwwkew"', 'output': '3'}
            ]),
            'starter_code': 'def lengthOfLongestSubstring(s):\n    # Your code here\n    pass',
            'solution': 'def lengthOfLongestSubstring(s):\n    char_set = set()\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        while s[right] in char_set:\n            char_set.remove(s[left])\n            left += 1\n        char_set.add(s[right])\n        max_len = max(max_len, right - left + 1)\n    return max_len'
        }
    ]
    
    for q_data in coding_questions:
        question = Question(**q_data)
        db.session.add(question)
    
    # Create sample MCQ questions
    mcq_questions = [
        {
            'title': 'What is the time complexity of binary search?',
            'description': 'Select the correct time complexity for binary search algorithm.',
            'type': 'mcq',
            'difficulty': 'easy',
            'company_id': companies['Google'].id,
            'tags': 'algorithms,complexity',
            'created_by': faculty.id,
            'options': json.dumps(['O(n)', 'O(log n)', 'O(n log n)', 'O(1)']),
            'correct_answer': 'B'
        },
        {
            'title': 'Which data structure follows LIFO principle?',
            'description': 'Choose the data structure that follows Last In First Out principle.',
            'type': 'mcq',
            'difficulty': 'easy',
            'company_id': companies['Microsoft'].id,
            'tags': 'data-structures',
            'created_by': faculty.id,
            'options': json.dumps(['Queue', 'Stack', 'Array', 'Linked List']),
            'correct_answer': 'B'
        },
        {
            'title': 'What is the space complexity of merge sort?',
            'description': 'Select the correct space complexity for merge sort algorithm.',
            'type': 'mcq',
            'difficulty': 'medium',
            'company_id': companies['Amazon'].id,
            'tags': 'algorithms,sorting',
            'created_by': faculty.id,
            'options': json.dumps(['O(1)', 'O(n)', 'O(log n)', 'O(n log n)']),
            'correct_answer': 'B'
        }
    ]
    
    for q_data in mcq_questions:
        question = Question(**q_data)
        db.session.add(question)
    
    # Create fill-in-the-blank questions
    fill_blank_questions = [
        {
            'title': 'Python Data Types',
            'description': 'Fill in the blanks about Python data types.',
            'type': 'fill_blank',
            'difficulty': 'easy',
            'company_id': companies['Microsoft'].id,
            'tags': 'python,programming',
            'created_by': faculty.id,
            'blanks': json.dumps([
                {'id': 1, 'text': 'In Python, lists are', 'answer': 'mutable'},
                {'id': 2, 'text': 'Tuples are', 'answer': 'immutable'},
                {'id': 3, 'text': 'Dictionary keys must be', 'answer': 'hashable'}
            ])
        }
    ]
    
    for q_data in fill_blank_questions:
        question = Question(**q_data)
        db.session.add(question)
    
    db.session.commit()
    print("Database seeded successfully!")

