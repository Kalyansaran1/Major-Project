"""
LeetCode-style code judge that executes solution functions directly
"""
import re
import json
import ast
from utils.compiler import execute_code, run_test_cases

def parse_test_case_input(input_str):
    """
    Parse test case input string into Python objects
    Handles formats like: "[2,7,11,15]\n9" -> [[2,7,11,15], 9]
    """
    lines = input_str.strip().split('\n')
    parsed = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            # Try to parse as JSON/Python literal
            parsed.append(ast.literal_eval(line))
        except:
            # If that fails, try JSON
            try:
                parsed.append(json.loads(line))
            except:
                # Fallback: return as string
                parsed.append(line)
    return parsed if len(parsed) > 1 else (parsed[0] if parsed else None)

def format_output(value):
    """Format a Python value to match expected output format"""
    if isinstance(value, (list, tuple)):
        return json.dumps(value).replace(' ', '')
    elif isinstance(value, dict):
        return json.dumps(value, sort_keys=True).replace(' ', '')
    elif isinstance(value, (int, float, bool)):
        return str(value)
    else:
        return str(value)

def extract_solution_function_python(code):
    """
    Extract solution function from Python code, removing main() if present
    Returns: (solution_code, has_main)
    """
    # Try to find common solution function names
    solution_patterns = [
        r'def\s+(twoSum|solution|solve|answer)\s*\(',
        r'class\s+Solution:.*?def\s+(\w+)\s*\(',
    ]
    
    # Check if there's a main block
    has_main = bool(re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', code))
    
    # Try to extract Solution class with method
    solution_class_match = re.search(
        r'class\s+Solution\s*:.*?(?=def\s+\w+|class\s+\w+|if\s+__name__|$)',
        code,
        re.DOTALL
    )
    
    if solution_class_match:
        solution_code = solution_class_match.group(0)
        # Remove main block if present (handle indented blocks)
        if has_main:
            lines = solution_code.split('\n')
            result_lines = []
            in_main = False
            for line in lines:
                if re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', line):
                    in_main = True
                    continue
                if in_main:
                    # Check if we're back to base indentation (end of main block)
                    if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                        in_main = False
                        result_lines.append(line)
                    # Skip indented lines in main block
                    continue
                result_lines.append(line)
            solution_code = '\n'.join(result_lines)
        return solution_code.strip(), has_main
    
    # Try to find standalone function
    for pattern in solution_patterns:
        match = re.search(pattern, code, re.IGNORECASE)
        if match:
            # Extract function and everything until next def/class/main
            func_match = re.search(
                r'def\s+' + match.group(1) + r'\s*\([^)]*\)\s*:.*?(?=def\s+\w+|class\s+\w+|if\s+__name__|$)',
                code,
                re.DOTALL
            )
            if func_match:
                return func_match.group(0).strip(), has_main
    
    # If no specific pattern found, try to remove main and return rest
    if has_main:
        lines = code.split('\n')
        result_lines = []
        in_main = False
        for line in lines:
            if re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', line):
                in_main = True
                continue
            if in_main:
                # Check if we're back to base indentation (end of main block)
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    in_main = False
                    result_lines.append(line)
                # Skip indented lines in main block
                continue
            result_lines.append(line)
        code_without_main = '\n'.join(result_lines)
    else:
        code_without_main = code
    return code_without_main.strip(), has_main

def extract_solution_function_cpp(code):
    """
    Extract solution function from C++ code, removing main() if present
    Returns: (solution_code, has_main)
    """
    has_main = bool(re.search(r'int\s+main\s*\(', code))
    
    # Try to find Solution class
    solution_class_match = re.search(
        r'class\s+Solution\s*\{.*?\};',
        code,
        re.DOTALL
    )
    
    if solution_class_match:
        solution_code = solution_class_match.group(0)
        # Remove main function if present (handle multi-line with balanced braces)
        # First, try simple removal
        solution_code = re.sub(
            r'int\s+main\s*\([^)]*\)\s*\{[^}]*\}',
            '',
            solution_code,
            flags=re.DOTALL
        )
        # If that didn't work, try removing main with balanced braces
        if 'main' in solution_code:
            # Remove everything from "int main(" to matching closing brace
            lines = solution_code.split('\n')
            result_lines = []
            in_main = False
            brace_count = 0
            for line in lines:
                if re.search(r'int\s+main\s*\(', line):
                    in_main = True
                    brace_count = line.count('{') - line.count('}')
                    continue
                if in_main:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        in_main = False
                    continue
                result_lines.append(line)
            solution_code = '\n'.join(result_lines)
        return solution_code.strip(), has_main
    
    # Try to find standalone function (like twoSum)
    func_match = re.search(
        r'(?:class\s+\w+\s*\{[^}]*\})?\s*(?:public:|private:)?\s*.*?(\w+)\s*\([^)]*\)\s*\{[^}]*\}',
        code,
        re.DOTALL
    )
    
    if func_match and not has_main:
        return code.strip(), False
    
    # Remove main and return rest (handle multi-line with balanced braces)
    if has_main:
        lines = code.split('\n')
        result_lines = []
        in_main = False
        brace_count = 0
        for line in lines:
            if re.search(r'int\s+main\s*\(', line):
                in_main = True
                brace_count = line.count('{') - line.count('}')
                continue
            if in_main:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    in_main = False
                continue
            result_lines.append(line)
        code_without_main = '\n'.join(result_lines)
    else:
        code_without_main = code
    
    return code_without_main.strip(), has_main

def extract_solution_function_java(code):
    """
    Extract solution function from Java code, removing main() if present
    Returns: (solution_code, has_main)
    """
    has_main = bool(re.search(r'public\s+static\s+void\s+main\s*\(', code))
    
    # Try to find Solution class
    solution_class_match = re.search(
        r'class\s+Solution\s*\{.*?\}',
        code,
        re.DOTALL
    )
    
    if solution_class_match:
        solution_code = solution_class_match.group(0)
        # Remove main method (handle multi-line with balanced braces)
        if has_main:
            lines = solution_code.split('\n')
            result_lines = []
            in_main = False
            brace_count = 0
            for line in lines:
                if re.search(r'public\s+static\s+void\s+main\s*\(', line):
                    in_main = True
                    brace_count = line.count('{') - line.count('}')
                    continue
                if in_main:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        in_main = False
                    continue
                result_lines.append(line)
            solution_code = '\n'.join(result_lines)
        return solution_code.strip(), has_main
    
    # If no Solution class, still remove main if present
    if has_main:
        lines = code.split('\n')
        result_lines = []
        in_main = False
        brace_count = 0
        for line in lines:
            if re.search(r'public\s+static\s+void\s+main\s*\(', line):
                in_main = True
                brace_count = line.count('{') - line.count('}')
                continue
            if in_main:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    in_main = False
                continue
            result_lines.append(line)
        code = '\n'.join(result_lines)
    
    return code.strip(), has_main

def wrap_for_run_python(code, sample_input=None):
    """
    Wrap Python solution code with main() for Run mode testing
    """
    solution_code, has_main = extract_solution_function_python(code)
    
    # If it already has main, return as-is
    if has_main:
        return code
    
    # Try to detect function name
    func_match = re.search(r'def\s+(\w+)\s*\(', solution_code)
    if not func_match:
        # If no function found, try Solution class
        method_match = re.search(r'class\s+Solution.*?def\s+(\w+)\s*\(', solution_code, re.DOTALL)
        if method_match:
            func_name = method_match.group(1)
            # Create wrapper
            if sample_input:
                try:
                    inputs = parse_test_case_input(sample_input)
                    if isinstance(inputs, list) and len(inputs) >= 2:
                        nums, target = inputs[0], inputs[1]
                        wrapper = f"""
{solution_code}

if __name__ == "__main__":
    solution = Solution()
    result = solution.{func_name}({nums}, {target})
    print(result)
"""
                    else:
                        wrapper = f"""
{solution_code}

if __name__ == "__main__":
    solution = Solution()
    result = solution.{func_name}({inputs})
    print(result)
"""
                except:
                    wrapper = f"""
{solution_code}

if __name__ == "__main__":
    solution = Solution()
    # Add your test input here
    pass
"""
            else:
                wrapper = f"""
{solution_code}

if __name__ == "__main__":
    solution = Solution()
    # Add your test input here
    pass
"""
            return wrapper.strip()
        return code
    
    func_name = func_match.group(1)
    
    # Create wrapper
    if sample_input:
        try:
            inputs = parse_test_case_input(sample_input)
            if isinstance(inputs, (list, tuple)) and len(inputs) >= 1:
                wrapper = f"""
{solution_code}

if __name__ == "__main__":
    result = {func_name}({', '.join(repr(inp) for inp in inputs)})
    print(result)
"""
            else:
                wrapper = f"""
{solution_code}

if __name__ == "__main__":
    result = {func_name}({repr(inputs)})
    print(result)
"""
        except:
            wrapper = f"""
{solution_code}

if __name__ == "__main__":
    # Add your test input here
    pass
"""
    else:
        wrapper = f"""
{solution_code}

if __name__ == "__main__":
    # Add your test input here
    pass
"""
    
    return wrapper.strip()

def wrap_for_run_c_cpp(code, language, sample_input=None):
    """
    Wrap C/C++ solution code with main() for Run mode testing
    """
    # Check if main already exists
    if re.search(r'int\s+main\s*\(', code):
        return code
    
    # Try to find function name (twoSum, solution, etc.)
    func_match = re.search(r'(\w+)\s*\([^)]*\)\s*\{', code)
    if not func_match:
        return code
    
    func_name = func_match.group(1)
    
    # Parse sample input if provided
    if sample_input:
        try:
            inputs = parse_test_case_input(sample_input)
            if isinstance(inputs, (list, tuple)) and len(inputs) >= 2:
                nums, target = inputs[0], inputs[1]
                # Create wrapper
                if language == 'c':
                    # Check if stdio.h is included
                    has_stdio = '#include <stdio.h>' in code or '#include<stdio.h>' in code
                    has_stdlib = '#include <stdlib.h>' in code or '#include<stdlib.h>' in code
                    headers = ''
                    if not has_stdio:
                        headers += '#include <stdio.h>\n'
                    if not has_stdlib:
                        headers += '#include <stdlib.h>\n'
                    
                    wrapper = f"""
{headers}
{code}

int main() {{
    int nums[] = {{{', '.join(map(str, nums))}}};
    int numsSize = {len(nums)};
    int target = {target};
    int returnSize;
    int* result = {func_name}(nums, numsSize, target, &returnSize);
    if (result != NULL) {{
        printf("[");
        for (int i = 0; i < returnSize; i++) {{
            if (i > 0) printf(",");
            printf("%d", result[i]);
        }}
        printf("]\\n");
        free(result);
    }}
    return 0;
}}
"""
                else:  # cpp
                    wrapper = f"""
#include <iostream>
#include <vector>
using namespace std;

{code}

int main() {{
    vector<int> nums = {{{', '.join(map(str, nums))}}};
    int target = {target};
    Solution solution;
    vector<int> result = solution.{func_name}(nums, target);
    cout << "[";
    for (int i = 0; i < result.size(); i++) {{
        if (i > 0) cout << ",";
        cout << result[i];
    }}
    cout << "]\\n";
    return 0;
}}
"""
            else:
                wrapper = f"""
{code}

int main() {{
    // Add your test input here
    return 0;
}}
"""
        except:
            wrapper = f"""
{code}

int main() {{
    // Add your test input here
    return 0;
}}
"""
    else:
        # Check if stdio.h is included for C
        if language == 'c':
            has_stdio = '#include <stdio.h>' in code or '#include<stdio.h>' in code
            has_stdlib = '#include <stdlib.h>' in code or '#include<stdlib.h>' in code
            headers = ''
            if not has_stdio:
                headers += '#include <stdio.h>\n'
            if not has_stdlib:
                headers += '#include <stdlib.h>\n'
            wrapper = f"""
{headers}
{code}

int main() {{
    // Add your test input here
    return 0;
}}
"""
        else:  # cpp
            wrapper = f"""
#include <iostream>
#include <vector>
using namespace std;

{code}

int main() {{
    // Add your test input here
    return 0;
}}
"""
    
    return wrapper.strip()

def wrap_for_run_java(code, sample_input=None):
    """
    Wrap Java solution code with main() for Run mode testing
    """
    # Check if main already exists
    if re.search(r'public\s+static\s+void\s+main\s*\(', code):
        return code
    
    # Try to find method name
    method_match = re.search(r'public\s+\w+\s+(\w+)\s*\([^)]*\)', code)
    if not method_match:
        return code
    
    method_name = method_match.group(1)
    
    # Parse sample input if provided
    if sample_input:
        try:
            inputs = parse_test_case_input(sample_input)
            if isinstance(inputs, (list, tuple)) and len(inputs) >= 2:
                nums, target = inputs[0], inputs[1]
                wrapper = f"""
{code}

class Main {{
    public static void main(String[] args) {{
        Solution solution = new Solution();
        int[] nums = {{{', '.join(map(str, nums))}}};
        int target = {target};
        int[] result = solution.{method_name}(nums, target);
        System.out.print("[");
        for (int i = 0; i < result.length; i++) {{
            if (i > 0) System.out.print(",");
            System.out.print(result[i]);
        }}
        System.out.println("]");
    }}
}}
"""
            else:
                wrapper = f"""
{code}

class Main {{
    public static void main(String[] args) {{
        // Add your test input here
    }}
}}
"""
        except:
            wrapper = f"""
{code}

class Main {{
    public static void main(String[] args) {{
        // Add your test input here
    }}
}}
"""
    else:
        wrapper = f"""
{code}

class Main {{
    public static void main(String[] args) {{
        // Add your test input here
    }}
}}
"""
    
    return wrapper.strip()

def execute_solution_function_python(solution_code, inputs):
    """
    Execute Python solution function with given inputs and return the result
    """
    # Create execution environment
    namespace = {}
    
    try:
        # Execute solution code
        exec(solution_code, namespace)
        
        # Try to find Solution class with method
        if 'Solution' in namespace:
            solution = namespace['Solution']()
            # Find the method (usually first method that's not __init__)
            method_name = None
            for attr_name in dir(solution):
                if not attr_name.startswith('_') and callable(getattr(solution, attr_name)):
                    attr = getattr(solution, attr_name)
                    if attr.__name__ != '__init__':
                        method_name = attr_name
                        break
            
            if method_name:
                method = getattr(solution, method_name)
                # Call with inputs
                if isinstance(inputs, (list, tuple)):
                    result = method(*inputs)
                else:
                    result = method(inputs)
                return result, 'accepted'
        
        # Try to find function (twoSum, solution, etc.)
        # Common function names for LeetCode problems
        common_names = ['twoSum', 'solution', 'solve', 'answer', 'calculate']
        for name in common_names:
            if name in namespace and callable(namespace[name]):
                func = namespace[name]
                if isinstance(inputs, (list, tuple)):
                    result = func(*inputs)
                else:
                    result = func(inputs)
                return result, 'accepted'
        
        # Try any callable that's not a builtin
        for name, obj in namespace.items():
            if callable(obj) and not name.startswith('_') and name not in ['print', 'len', 'range', 'str', 'int', 'list', 'dict']:
                try:
                    if isinstance(inputs, (list, tuple)):
                        result = obj(*inputs)
                    else:
                        result = obj(inputs)
                    return result, 'accepted'
                except:
                    continue
        
        return None, 'error'
    except Exception as e:
        return str(e), 'runtime_error'

def execute_solution_function_cpp(solution_code, inputs):
    """
    Execute C++ solution function by wrapping it in a test harness
    """
    # Try to detect method name
    method_match = re.search(r'(\w+)\s*\([^)]*\)\s*\{', solution_code)
    method_name = method_match.group(1) if method_match else 'twoSum'
    
    # Parse inputs
    if isinstance(inputs, (list, tuple)) and len(inputs) >= 2:
        nums, target = inputs[0], inputs[1]
    else:
        nums, target = inputs if isinstance(inputs, (list, tuple)) else ([], inputs)
    
    # Create wrapper code that calls the solution and prints result
    wrapper_code = f"""
#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <unordered_map>
using namespace std;

{solution_code}

int main() {{
    Solution solution;
    vector<int> nums = {{{', '.join(map(str, nums))}}};
    int target = {target};
    vector<int> result = solution.{method_name}(nums, target);
    cout << "[";
    for (int i = 0; i < result.size(); i++) {{
        if (i > 0) cout << ",";
        cout << result[i];
    }}
    cout << "]";
    return 0;
}}
"""
    
    output, status, exec_time, memory = execute_code(wrapper_code, 'cpp', '')
    
    if status == 'accepted':
        # Parse output
        try:
            result_str = output.strip()
            # Extract array from output like "[0,1]"
            match = re.search(r'\[([^\]]+)\]', result_str)
            if match:
                result = json.loads('[' + match.group(1) + ']')
                return result, 'accepted'
            return output, 'accepted'
        except:
            return output, status
    else:
        return output, status

def execute_solution_function_java(solution_code, inputs):
    """
    Execute Java solution function by wrapping it in a test harness
    """
    # Try to detect method name
    method_match = re.search(r'public\s+\w+\s+(\w+)\s*\([^)]*\)', solution_code)
    method_name = method_match.group(1) if method_match else 'twoSum'
    
    # Parse inputs
    if isinstance(inputs, (list, tuple)) and len(inputs) >= 2:
        nums, target = inputs[0], inputs[1]
    else:
        nums, target = inputs if isinstance(inputs, (list, tuple)) else ([], inputs)
    
    # Create wrapper code
    wrapper_code = f"""
import java.util.*;

{solution_code}

class Main {{
    public static void main(String[] args) {{
        Solution solution = new Solution();
        int[] nums = {{{', '.join(map(str, nums))}}};
        int target = {target};
        int[] result = solution.{method_name}(nums, target);
        System.out.print("[");
        for (int i = 0; i < result.length; i++) {{
            if (i > 0) System.out.print(",");
            System.out.print(result[i]);
        }}
        System.out.print("]");
    }}
}}
"""
    
    output, status, exec_time, memory = execute_code(wrapper_code, 'java', '')
    
    if status == 'accepted':
        try:
            result_str = output.strip()
            match = re.search(r'\[([^\]]+)\]', result_str)
            if match:
                result = json.loads('[' + match.group(1) + ']')
                return result, 'accepted'
            return output, 'accepted'
        except:
            return output, status
    else:
        return output, status

def run_test_cases_function_based(code, language, test_cases):
    """
    Run test cases by calling solution functions directly (LeetCode style)
    Returns: (passed_count, total_count, results)
    """
    passed = 0
    total = len(test_cases)
    results = []
    
    # Extract solution code (remove main if present)
    if language == 'python':
        solution_code, _ = extract_solution_function_python(code)
        execute_func = execute_solution_function_python
    elif language == 'cpp':
        solution_code, _ = extract_solution_function_cpp(code)
        execute_func = execute_solution_function_cpp
    elif language == 'java':
        solution_code, _ = extract_solution_function_java(code)
        execute_func = execute_solution_function_java
    else:
        # Fallback to old method
        return run_test_cases(code, language, test_cases)
    
    for i, test_case in enumerate(test_cases):
        input_str = test_case.get('input', '')
        expected_output_str = test_case.get('output', '').strip()
        
        # Parse inputs
        try:
            inputs = parse_test_case_input(input_str)
        except Exception as e:
            results.append({
                'test_case': i + 1,
                'input': input_str,
                'expected_output': expected_output_str,
                'actual_output': f'Input parsing error: {str(e)}',
                'passed': False,
                'status': 'error',
                'execution_time': 0.0
            })
            continue
        
        # Execute solution function
        import time
        start_time = time.time()
        actual_result, status = execute_func(solution_code, inputs)
        execution_time = time.time() - start_time
        
        # Format outputs for comparison
        actual_output_str = format_output(actual_result) if actual_result is not None else ''
        expected_output_str = expected_output_str.replace(' ', '')
        actual_output_str = actual_output_str.replace(' ', '')
        
        # Compare (normalize both)
        is_passed = actual_output_str == expected_output_str and status == 'accepted'
        
        if is_passed:
            passed += 1
        
        results.append({
            'test_case': i + 1,
            'input': input_str,
            'expected_output': expected_output_str,
            'actual_output': actual_output_str if status == 'accepted' else str(actual_result),
            'passed': is_passed,
            'status': status,
            'execution_time': execution_time
        })
    
    return passed, total, results

