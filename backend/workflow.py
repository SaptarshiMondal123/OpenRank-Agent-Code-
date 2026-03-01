import json
from typing import Any, Dict, List
import queue
import threading
from agent_core import (
    analyze_submission,
    get_strategic_coaching_with_context,
    run_code_in_sandbox, # The Engine is back!
)
from static_analyzer import strict_complexity_check
from database import get_supabase_client

# --- LOGGING WORKER SETUP ---
_log_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
_log_worker_started = False

def _build_final_report(state: Dict[str, Any]) -> str:
    complexity = state.get("complexity", {})
    strategy = state.get("strategy", {})
    static_complexity = state.get("static_complexity", {})
    judge_results = state.get("judge_results", [])
    judge_error = state.get("judge_error")

    lines = ["### Execution & Analysis Summary"]

    if judge_results:
        lines.append("\n#### 🧪 Test Results")
        passed_count = sum(1 for c in judge_results if c.get("passed"))
        lines.append(f"**Passed {passed_count} / {len(judge_results)} cases**\n")
        
        for idx, case in enumerate(judge_results):
            icon = "✅ Pass" if case.get("passed") else "❌ Fail"
            lines.append(f"- **Test {idx + 1}:** {icon}")
            lines.append(f"  - Input: `{case.get('input')}`")
            lines.append(f"  - Expected: `{case.get('expected')}` | Actual: `{case.get('actual')}`")
    elif judge_error:
        lines.append(f"\n#### ⚠️ Execution Error\n{judge_error}")

    if complexity:
        lines.append("\n#### ⏱️ Complexity")
        lines.append(f"- **Time:** {complexity.get('time_complexity', 'N/A')}")
        lines.append(f"- **Space:** {complexity.get('space_complexity', 'N/A')}")
        lines.append(f"- **Optimal:** {'✅ Yes' if complexity.get('is_optimal') else '❌ No'}")

    if strategy:
        lines.append("\n#### 💡 AI Coach Insight")
        lines.append(f"- **Detected Approach:** {strategy.get('detected_pattern', 'Unknown')}")
        lines.append(f"- **Feedback:** {strategy.get('explanation', 'N/A')}")

    return "\n".join(lines)

def _build_log_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    problem = state.get("problem", "")
    complexity = state.get("complexity", {})
    strategy = state.get("strategy", {})
    judge_results = state.get("judge_results", [])
    
    if judge_results and any(not r.get("passed") for r in judge_results):
        status = "FAIL"
    elif judge_results:
        status = "PASS"
    else:
        status = "ERROR"

    return {
        "problem_name": problem[:50],
        "code_snippet": state.get("code", "")[:5000],
        "status": status,
        "time_complexity": complexity.get("time_complexity", "Unknown"),
        "space_complexity": complexity.get("space_complexity", "Unknown"),
        "pattern_detected": strategy.get("detected_pattern", "Unknown"),
    }

def _log_to_db_sync(payload: Dict[str, Any]) -> None:
    try:
        supabase = get_supabase_client()
        supabase.table("submissions").insert(payload).execute()
    except Exception as e:
        print(f"❌ DB Log Error: {e}")

def _log_worker() -> None:
    while True:
        payload = _log_queue.get()
        if payload is None:
            break
        _log_to_db_sync(payload)
        _log_queue.task_done()

def log_to_db(state: Dict[str, Any]) -> None:
    global _log_worker_started
    if not _log_worker_started:
        thread = threading.Thread(target=_log_worker, name="db-log-worker", daemon=True)
        thread.start()
        _log_worker_started = True
    try:
        _log_queue.put_nowait(_build_log_payload(state))
    except Exception as e:
        print(f"DB Queue Error: {e}")

def _model_to_dict(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"): return model.model_dump()
    if hasattr(model, "dict"): return model.dict()
    return dict(model)

# --- DATABASE TEST CASE LOADER ---
def get_problem_test_cases(problem_text: str):
    """Fetches exact test cases from Supabase by checking Title and Description."""
    try:
        supabase = get_supabase_client()
        
        # 1. Try exact match on Title
        res_title = supabase.table("problems").select("test_cases").eq("title", problem_text).execute()
        if res_title.data and len(res_title.data) > 0:
            return res_title.data[0]["test_cases"]
            
        # 2. Try exact match on Description
        res_desc = supabase.table("problems").select("test_cases").eq("description", problem_text).execute()
        if res_desc.data and len(res_desc.data) > 0:
            return res_desc.data[0]["test_cases"]
            
        # 3. Fuzzy match fallback
        short_text = problem_text[:30]
        res_fuzzy = supabase.table("problems").select("test_cases").ilike("description", f"%{short_text}%").execute()
        if res_fuzzy.data and len(res_fuzzy.data) > 0:
            return res_fuzzy.data[0]["test_cases"]
            
    except Exception as e:
        print(f"DB Fetch Error: {e}")
    
    return []

def _normalize_test_cases(raw_cases: Any) -> list:
    # Safely parse Supabase JSON strings into Python lists
    if isinstance(raw_cases, str):
        try:
            raw_cases = json.loads(raw_cases)
        except Exception:
            return []

    if not raw_cases or not isinstance(raw_cases, list):
        return []
    
    normalized = []
    for case in raw_cases:
        if not isinstance(case, dict): continue
        inp = case.get("input") or case.get("inputs")
        exp = case.get("expected_output") or case.get("expected") or case.get("output")
        if inp is not None and exp is not None:
            normalized.append({"input": inp, "expected_output": exp})
            
    return normalized

# --- MAIN IDE WORKFLOW ---

# Inside workflow.py

class AppWorkflow:
    def invoke(self, state: Dict[str, Any], run_ai: bool = True) -> Dict[str, Any]:
        code = state.get("code", "")
        problem = state.get("problem", "")
        language = state.get("language", "python")

        # 1. Static Analysis
        static_complexity = strict_complexity_check(code)
        state["static_complexity"] = static_complexity

        # 2. Safety Check
        if static_complexity.get("risk_factor") == "HIGH":
            state["final_report"] = _build_final_report(state) + "\n\n🚨 **Code Rejected:** Nested loops are too deep."
            log_to_db(state)
            return state

        # 3. Load Database Test Cases & Execute Sandbox
        raw_tests = get_problem_test_cases(problem)
        test_cases = _normalize_test_cases(raw_tests)
        
        if not test_cases:
            state["judge_results"] = []
            state["judge_error"] = f"No test cases found in database for problem: '{problem}'"
        else:
            judge_results = run_code_in_sandbox(
                code,
                language,
                test_cases,
                static_complexity.get("function_name") 
            )
            state["judge_results"] = judge_results

        # 4. Check for test failures
        failed_cases = [c for c in state.get("judge_results", []) if not c.get("passed")]
        state["failed_cases"] = failed_cases
        failure_context = None
        if failed_cases:
            f = failed_cases[0]
            failure_context = f"Failed input: {f['input']}. Expected: {f['expected']}. Got: {f['actual']}."

        # 5. AI Analysis (ONLY IF REQUESTED)
        if run_ai:
            try:
                feedback = analyze_submission(code, problem)
                state["complexity"] = _model_to_dict(feedback.complexity)
                state["bugs"] = list(feedback.bugs)
                state["suggestions"] = list(feedback.suggestions)
                
                coaching = get_strategic_coaching_with_context(code, problem, failure_context)
                state["strategy"] = _model_to_dict(coaching)
            except Exception as e:
                print(f"AI Error: {e}")
                state["strategy"] = {"detected_pattern": "Error", "explanation": "AI Service Unavailable"}
        else:
            # If AI is skipped, leave these blank
            state["complexity"] = {}
            state["strategy"] = {}

        # 6. Finalize Report
        state["final_report"] = _build_final_report(state)
        log_to_db(state)

        return state

app_workflow = AppWorkflow()