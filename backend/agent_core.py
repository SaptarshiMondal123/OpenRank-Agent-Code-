import json
import os
import re
import subprocess
import tempfile
import sys
from typing import Optional, Any
from langchain_groq import ChatGroq # type: ignore
from schemas import FeedbackResponse, CoachingTip, ComplexityAnalysis
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage # type: ignore

def _load_dotenv_if_needed(dotenv_path: str = ".env") -> None:
    if os.getenv("GROQ_API_KEY"):
        return
    if not os.path.exists(dotenv_path):
        return

    with open(dotenv_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

_load_dotenv_if_needed()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is not set in the environment or .env file.")

# Initialize Groq (Only one strict model needed now)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# --- CHAIN 1: Analyst ---

def analyze_submission(code: str, problem: str):
    # SAFEST: Replace { with {{ and } with }} in the user input before f-string
    safe_problem = problem.replace("{", "{{").replace("}", "}}")
    safe_code = code.replace("{", "{{").replace("}", "}}")
    
    prompt = f"""
    You are a Competitive Programming Coach. Analyze the following solution.
    Problem: {safe_problem}
    User Code:
    {safe_code}
    
    CRITICAL GRADING RULES:
    1. Analyze Time and Space Complexity accurately.
    2. STRICT OPTIMALITY CHECK:
       - If the code uses Recursion ($O(N)$ space) but could be done Iteratively ($O(1)$ space), set "is_optimal": False.
       - If the code fails on edge cases (like negative numbers), set "is_optimal": False.
       - Factorial/Fibonacci recursion is NEVER optimal due to Stack Overflow risk.
       
    Return ONLY valid JSON matching this structure. Do NOT return markdown or explanation text outside the JSON.
    {{
        "complexity": {{
            "time_complexity": "O(...)", 
            "space_complexity": "O(...)", 
            "is_optimal": true/false
        }},
        "bugs": ["list of potential bugs..."],
        "suggestions": ["list of suggestions..."]
    }}
    """
    
    response = llm.invoke(prompt)
    raw_content = getattr(response, "content", "") or str(response)
    
    try:
        json_str = extract_json_str(raw_content)
        data = json.loads(json_str)
        return FeedbackResponse(**data)
    except Exception as e:
        print(f"Analysis Error: {e}")
        from schemas import ComplexityAnalysis
        return FeedbackResponse(
            complexity=ComplexityAnalysis(
                time_complexity="Unknown",
                space_complexity="Unknown",
                is_optimal=False
            ),
            bugs=["Could not parse AI response due to error."],
            suggestions=["Please try again."]
        )

# --- HELPER FUNCTIONS ---

def extract_json_str(text: str) -> str:
    """Finds the first valid JSON object in a string."""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```", "", text)
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        return match.group(1)
    return text.strip()

def normalize_coaching_data(data: dict) -> dict:
    detected = str(data.get("detected_pattern") or data.get("algorithmic_pattern") or "Unknown")
    optimal = str(data.get("optimal_pattern") or data.get("optimal_approach") or "Manual Review")
    
    raw_explanation = data.get("explanation") or data.get("difference") or "No explanation provided."
    clean_explanation = ""
    if isinstance(raw_explanation, dict):
        clean_explanation = (
            raw_explanation.get("difference") or 
            raw_explanation.get("explanation") or 
            raw_explanation.get("text") or 
            str(raw_explanation) 
        )
    else:
        clean_explanation = str(raw_explanation)

    raw_similar = data.get("similar_problems") or data.get("recommendations") or []
    clean_similar = []
    if isinstance(raw_similar, list):
        for item in raw_similar:
            if item and isinstance(item, str):
                clean_similar.append(item)
            elif item and isinstance(item, dict):
                clean_similar.append(str(list(item.values())[0]))
    elif isinstance(raw_similar, str):
        clean_similar = [raw_similar]
        
    return {
        "detected_pattern": detected,
        "optimal_pattern": optimal,
        "explanation": clean_explanation,
        "similar_problems": clean_similar
    }

# --- CHAIN 2: The Strategist ---

def get_strategic_coaching(code: str, problem: str):
    return get_strategic_coaching_with_context(code, problem, None)

def get_strategic_coaching_with_context(code: str, problem: str, extra_context: Optional[str]):
    extra = f"\nAdditional context: {extra_context}\n" if extra_context else ""
    
    prompt = f"""
    You are a generic coding pattern recognizer.
    
    Problem: {problem}
    User Code: {code}
    {extra}
    
    1. Identify the algorithmic pattern used (e.g., Two Pointers, Greedy, Brute Force).
    2. Determine the OPTIMAL pattern for this specific problem.
    3. Explain the difference clearly.
    4. Recommend 2-3 similar LeetCode problems.
    
    IMPORTANT: Return strict JSON. Do not write introductory text.
    Use these exact keys: "detected_pattern", "optimal_pattern", "explanation", "similar_problems".
    """
    
    response = llm.invoke(prompt)
    raw_content = getattr(response, "content", "") or str(response)
    
    try:
        json_str = extract_json_str(raw_content)
        data_dict = json.loads(json_str)
        clean_data = normalize_coaching_data(data_dict)
        return CoachingTip(**clean_data)
        
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return CoachingTip(
            detected_pattern="Unknown",
            optimal_pattern="Analysis Failed",
            explanation=f"AI Error: {str(e)[:100]}",
            similar_problems=[]
        )

# --- EXECUTION ENGINE (LOCAL SANDBOX) ---

def run_code_in_sandbox(code: str, language: str, inputs: list, function_name: Optional[str] = None):
    target_function = function_name or "solution"
    test_cases_json = json.dumps(inputs)
    
    # Basic security block
    dangerous_keywords = ["import os", "import sys", "import subprocess", "eval(", "exec("]
    if any(keyword in code for keyword in dangerous_keywords):
         return [{"input": "Security Check", "expected": "Pass", "actual": "⚠️ Security Error: OS/Sys imports and eval() are blocked.", "passed": False, "runtime": 0, "memory": 0}]

    # --- UPGRADED WRAPPER WITH TRACEMALLOC & TIMING ---
    wrapped_code = f"""
import json
import inspect
import time
import tracemalloc

# --- USER CODE ---
{code}

# --- BATCH EXECUTION ---
try:
    func = {target_function}
    sig = inspect.signature(func)
    num_params = len(sig.parameters)
    
    test_cases = json.loads({repr(test_cases_json)})
    results = []
    
    for case in test_cases:
        raw_input = case.get('input')
        
        # 1. Start memory tracker and timer
        tracemalloc.start()
        start_time = time.perf_counter()
        
        try:
            if isinstance(raw_input, dict):
                result = func(**raw_input)
            elif isinstance(raw_input, list) and num_params > 1 and len(raw_input) == num_params:
                result = func(*raw_input)
            else:
                result = func(raw_input)
                
            # 2. Stop timer and grab peak memory
            end_time = time.perf_counter()
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Calculate metrics
            runtime_ms = round((end_time - start_time) * 1000, 2)
            memory_mb = round(peak_mem / (1024 * 1024), 2)
            
            # Ensure minimums so it doesn't just say "0"
            if runtime_ms < 1: runtime_ms = 1.0
            if memory_mb < 0.1: memory_mb = 0.1
                
            results.append({{
                "status": "success", 
                "output": result,
                "runtime": runtime_ms,
                "memory": memory_mb
            }})
        except Exception as e:
            tracemalloc.stop()
            results.append({{"status": "error", "output": type(e).__name__ + ": " + str(e), "runtime": 0, "memory": 0}})
            
    print("---PISTON_JSON_START---")
    print(json.dumps(results))
    print("---PISTON_JSON_END---")
    
except Exception as e:
    print(f"FATAL_SANDBOX_ERROR: {{type(e).__name__}}: {{e}}")
"""
    
    results = []
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(wrapped_code)
            temp_filepath = temp_file.name

        try:
            process = subprocess.run([sys.executable, temp_filepath], capture_output=True, text=True, timeout=3)
            output = process.stdout + "\n" + process.stderr
        except subprocess.TimeoutExpired:
            output = "FATAL_SANDBOX_ERROR: TimeoutError: Code execution exceeded 3 seconds."
        finally:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

        if "---PISTON_JSON_START---" in output and "---PISTON_JSON_END---" in output:
            json_str = output.split("---PISTON_JSON_START---")[1].split("---PISTON_JSON_END---")[0].strip()
            execution_results = json.loads(json_str)
            
            for idx, tc in enumerate(inputs):
                expected_str = str(tc.get("expected_output")).strip()
                if expected_str == "True": expected_str = "true"
                if expected_str == "False": expected_str = "false"
                
                runtime = 0
                memory = 0
                
                if idx < len(execution_results):
                    exec_res = execution_results[idx]
                    if exec_res["status"] == "success":
                        runtime = exec_res.get("runtime", 0)
                        memory = exec_res.get("memory", 0)
                        if isinstance(exec_res["output"], bool):
                            actual_str = str(exec_res["output"]).lower()
                        else:
                            actual_str = json.dumps(exec_res["output"])
                    else:
                        actual_str = "⚠️ " + exec_res["output"]
                        if "RecursionError" in actual_str: actual_str = "⚠️ Stack Overflow"
                else:
                    actual_str = "Missing output"
                
                expected_clean = expected_str.replace(" ", "").replace("'", '"')
                actual_clean = actual_str.replace(" ", "").replace("'", '"')
                passed = (actual_clean == expected_clean)
                
                results.append({
                    "input": str(tc.get("input")),
                    "expected": expected_str,
                    "actual": actual_str,
                    "passed": passed,
                    "runtime": runtime,    # <--- EXTRACTED!
                    "memory": memory       # <--- EXTRACTED!
                })
        else:
            clean_output = output.replace("FATAL_SANDBOX_ERROR: ", "⚠️ ").strip()
            if not clean_output: clean_output = "⚠️ Syntax Error"
            for tc in inputs:
                results.append({"input": str(tc.get("input")), "expected": str(tc.get("expected_output")), "actual": clean_output, "passed": False, "runtime": 0, "memory": 0})
                
    except Exception as e:
        for tc in inputs:
            results.append({"input": str(tc.get("input")), "expected": str(tc.get("expected_output")), "actual": f"Local Error: {e}", "passed": False, "runtime": 0, "memory": 0})
            
    return results

# --- CHAIN 3: The Coach (Chat) ---

def chat_with_coach(chat_history: list, code: str, problem: str):
    system_prompt = f"""
    You are a friendly and encouraging Competitive Programming Coach.
    
    The user is working on this problem:
    "{problem}"
    
    Here is their current code solution:
    ```python
    {code}
    ```
    
    Your goal is to answer their questions about the code, the algorithm, or Time Complexity.
    - Be concise.
    - If they ask for "Simpler explanation", use analogies (e.g., stacking plates for stacks).
    - If they provide new code in the chat, analyze it briefly.
    """
    
    messages = [SystemMessage(content=system_prompt)]
    
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
            
    response = llm.invoke(messages)
    return response.content