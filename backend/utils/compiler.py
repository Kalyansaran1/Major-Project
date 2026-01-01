"""
Code compiler integration utilities
"""
import requests
import json
import subprocess
import tempfile
import os
import time
import platform
from config import Config

def execute_code(code, language, stdin=''):
    """
    Execute code using online compiler API or local compilation
    Returns: (output, status, execution_time, memory)
    """
    language_map = {
        'c': 'c',
        'cpp': 'cpp17',
        'python': 'python3',
        'java': 'java'
    }
    
    # If compiler API is configured, use it
    if Config.COMPILER_CLIENT_ID:
        payload = {
            'clientId': Config.COMPILER_CLIENT_ID,
            'clientSecret': Config.COMPILER_CLIENT_SECRET,
            'script': code,
            'language': language_map.get(language, language),
            'stdin': stdin,
            'versionIndex': '0'
        }
        
        try:
            response = requests.post(Config.COMPILER_API_URL, json=payload, timeout=10)
            data = response.json()
            
            output = data.get('output', '')
            status = 'accepted' if data.get('statusCode') == 200 else 'runtime_error'
            execution_time = data.get('cpuTime', 0.0)
            memory = data.get('memory', 0.0)
            
            return output, status, execution_time, memory
        except Exception as e:
            return str(e), 'runtime_error', 0.0, 0.0
    
    # Fallback: Local execution
    try:
        if language == 'python':
            return _execute_python(code, stdin)
        elif language == 'cpp':
            return _execute_cpp(code, stdin)
        elif language == 'c':
            return _execute_c(code, stdin)
        elif language == 'java':
            return _execute_java(code, stdin)
        else:
            return f"Unsupported language: {language}", 'error', 0.0, 0.0
    except Exception as e:
        return str(e), 'runtime_error', 0.0, 0.0

def _execute_python(code, stdin=''):
    """Execute Python code locally"""
    import io
    import sys
    
    # Capture stdout
    old_stdout = sys.stdout
    old_stdin = sys.stdin
    sys.stdout = buffer = io.StringIO()
    sys.stdin = io.StringIO(stdin)
    
    try:
        start_time = time.time()
        exec(code)
        execution_time = time.time() - start_time
        
        # Get output
        output = buffer.getvalue()
        sys.stdout = old_stdout
        sys.stdin = old_stdin
        
        return output, 'accepted', execution_time, 10.0
    except Exception as e:
        sys.stdout = old_stdout
        sys.stdin = old_stdin
        return str(e), 'runtime_error', 0.0, 0.0

def _execute_cpp(code, stdin=''):
    """Execute C++ code locally using g++ or fallback to online API"""
    temp_dir = tempfile.mkdtemp()
    try:
        # Write code to file
        code_file = os.path.join(temp_dir, 'main.cpp')
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Determine executable name based on OS
        is_windows = platform.system() == 'Windows'
        exe_name = 'main.exe' if is_windows else 'main'
        exe_path = os.path.join(temp_dir, exe_name)
        
        # Compile - try g++ first, then cl on Windows
        compile_cmd = None
        if _check_command('g++'):
            compile_cmd = ['g++', '-o', exe_path, code_file, '-std=c++17']
        elif is_windows and _check_command('cl'):
            # Try cl.exe (MSVC) on Windows
            compile_cmd = ['cl', '/EHsc', f'/Fe:{exe_path}', code_file]
        
        if not compile_cmd:
            # Fallback to free online compiler API
            return _execute_cpp_online(code, stdin)
        
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_dir
        )
        
        if compile_result.returncode != 0:
            return compile_result.stderr, 'compilation_error', 0.0, 0.0
        
        # Execute
        start_time = time.time()
        run_result = subprocess.run(
            [exe_path] if not is_windows else [exe_path],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=temp_dir
        )
        execution_time = time.time() - start_time
        
        if run_result.returncode != 0:
            return run_result.stderr or "Runtime error", 'runtime_error', execution_time, 0.0
        
        return run_result.stdout, 'accepted', execution_time, 0.0
        
    except subprocess.TimeoutExpired:
        return "Execution timeout", 'timeout', 0.0, 0.0
    except Exception as e:
        return str(e), 'runtime_error', 0.0, 0.0
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

def _execute_c(code, stdin=''):
    """Execute C code locally using gcc"""
    temp_dir = tempfile.mkdtemp()
    try:
        # Write code to file
        code_file = os.path.join(temp_dir, 'main.c')
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Determine executable name based on OS
        is_windows = platform.system() == 'Windows'
        exe_name = 'main.exe' if is_windows else 'main'
        exe_path = os.path.join(temp_dir, exe_name)
        
        # Compile
        compile_cmd = ['gcc', '-o', exe_path, code_file]
        if not _check_command('gcc'):
            # Fallback to online compiler API
            return _execute_c_online(code, stdin)
        
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_dir
        )
        
        if compile_result.returncode != 0:
            return compile_result.stderr, 'compilation_error', 0.0, 0.0
        
        # Execute
        start_time = time.time()
        run_result = subprocess.run(
            [exe_path] if not is_windows else [exe_path],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=temp_dir
        )
        execution_time = time.time() - start_time
        
        if run_result.returncode != 0:
            return run_result.stderr or "Runtime error", 'runtime_error', execution_time, 0.0
        
        return run_result.stdout, 'accepted', execution_time, 0.0
        
    except subprocess.TimeoutExpired:
        return "Execution timeout", 'timeout', 0.0, 0.0
    except Exception as e:
        return str(e), 'runtime_error', 0.0, 0.0
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

def _execute_java(code, stdin=''):
    """Execute Java code locally"""
    temp_dir = tempfile.mkdtemp()
    try:
        # Extract class name from code (assume public class exists)
        class_name = 'Main'
        if 'public class' in code:
            class_name = code.split('public class')[1].split()[0].split('{')[0].strip()
        
        # Write code to file
        code_file = os.path.join(temp_dir, f'{class_name}.java')
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Compile
        if not _check_command('javac'):
            # Fallback to online compiler API
            return _execute_java_online(code, stdin)
        
        compile_result = subprocess.run(
            ['javac', code_file],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=temp_dir
        )
        
        if compile_result.returncode != 0:
            return compile_result.stderr, 'compilation_error', 0.0, 0.0
        
        # Execute
        if not _check_command('java'):
            return "Java runtime (java) not found. Please install JDK.", 'error', 0.0, 0.0
        
        start_time = time.time()
        run_result = subprocess.run(
            ['java', '-cp', temp_dir, class_name],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=temp_dir
        )
        execution_time = time.time() - start_time
        
        if run_result.returncode != 0:
            return run_result.stderr or "Runtime error", 'runtime_error', execution_time, 0.0
        
        return run_result.stdout, 'accepted', execution_time, 0.0
        
    except subprocess.TimeoutExpired:
        return "Execution timeout", 'timeout', 0.0, 0.0
    except Exception as e:
        return str(e), 'runtime_error', 0.0, 0.0
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

def _execute_online(code, language, stdin=''):
    """Execute code using free online compiler API (Piston API)"""
    try:
        # Use Piston API (free, no authentication required)
        piston_url = 'https://emkc.org/api/v2/piston/execute'
        
        # Map language names
        lang_map = {
            'cpp': 'cpp',
            'c': 'c',
            'java': 'java',
            'python': 'python3'
        }
        
        piston_lang = lang_map.get(language, language)
        
        payload = {
            'language': piston_lang,
            'version': '*',
            'files': [
                {
                    'content': code
                }
            ],
            'stdin': stdin
        }
        
        response = requests.post(piston_url, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'run' in data:
                run_data = data['run']
                output = run_data.get('stdout', '')
                stderr = run_data.get('stderr', '')
                
                if stderr:
                    # If there's stderr, it might be a compilation or runtime error
                    if 'compile' in data and data['compile'].get('stderr'):
                        return data['compile']['stderr'], 'compilation_error', 0.0, 0.0
                    return stderr, 'runtime_error', 0.0, 0.0
                
                # Calculate execution time if available
                execution_time = 0.0
                if 'time' in run_data:
                    try:
                        execution_time = float(run_data['time'])
                    except:
                        pass
                
                return output, 'accepted', execution_time, 0.0
            else:
                return "Unknown error from compiler API", 'error', 0.0, 0.0
        else:
            return f"Compiler API error: {response.status_code}", 'error', 0.0, 0.0
            
    except requests.exceptions.Timeout:
        return "Compiler API timeout. Please try again.", 'timeout', 0.0, 0.0
    except requests.exceptions.RequestException as e:
        return f"Compiler API error: {str(e)}", 'error', 0.0, 0.0
    except Exception as e:
        return f"Error: {str(e)}", 'error', 0.0, 0.0

def _execute_cpp_online(code, stdin=''):
    """Execute C++ code using free online compiler API"""
    return _execute_online(code, 'cpp', stdin)

def _execute_c_online(code, stdin=''):
    """Execute C code using free online compiler API"""
    return _execute_online(code, 'c', stdin)

def _execute_java_online(code, stdin=''):
    """Execute Java code using free online compiler API"""
    return _execute_online(code, 'java', stdin)

def _check_command(cmd):
    """Check if a command is available in the system"""
    try:
        subprocess.run(
            [cmd, '--version'] if cmd not in ['cl'] else [cmd],
            capture_output=True,
            timeout=2
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False

def run_test_cases(code, language, test_cases):
    """
    Run code against test cases
    Returns: (passed_count, total_count, results)
    """
    passed = 0
    total = len(test_cases)
    results = []
    
    for i, test_case in enumerate(test_cases):
        stdin = test_case.get('input', '')
        expected_output = test_case.get('output', '').strip()
        
        output, status, exec_time, memory = execute_code(code, language, stdin)
        actual_output = output.strip()
        
        is_passed = actual_output == expected_output and status == 'accepted'
        if is_passed:
            passed += 1
        
        results.append({
            'test_case': i + 1,
            'input': stdin,
            'expected_output': expected_output,
            'actual_output': actual_output,
            'passed': is_passed,
            'status': status,
            'execution_time': exec_time
        })
    
    return passed, total, results

