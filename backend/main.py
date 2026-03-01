from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel # type: ignore
from workflow import app_workflow
from agent_core import chat_with_coach
from database import get_dashboard_stats
from database import get_supabase_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (OPTIONS, GET, POST, etc.)
    allow_headers=["*"],
)

class RequestBody(BaseModel):
    code: str
    problem: str
    language: str = "python"
    run_ai: bool = False

class ChatRequest(BaseModel):
    code: str
    problem: str
    history: list # List of {role: str, content: str}

@app.post("/full-critique")
async def full_critique(body: RequestBody):
    initial_state = {
        "code": body.code, 
        "problem": body.problem, 
        "language": body.language
    }
    
    # Pass the run_ai flag into invoke()
    result_state = app_workflow.invoke(initial_state, run_ai=body.run_ai)
    
    return {
        "report": result_state.get("final_report", ""),
        "judge_results": result_state.get("judge_results", []) 
    }

@app.post("/chat")
async def chat(body: ChatRequest):
    response = chat_with_coach(body.history, body.code, body.problem)
    return {"reply": response}

@app.get("/stats")
async def stats():
    return get_dashboard_stats()

@app.get("/problems")
async def get_problems():
    """Fetches the list of problems for the dropdown"""
    try:
        supabase = get_supabase_client()
        # We only grab the id, title, and difficulty for the list
        res = supabase.table("problems").select("id, title, difficulty").execute()
        return {"problems": res.data}
    except Exception as e:
        return {"error": str(e), "problems": []}

@app.get("/problems/{problem_id}")
async def get_problem(problem_id: str):
    """Fetches the full description and starter code when a user clicks a problem"""
    try:
        supabase = get_supabase_client()
        res = supabase.table("problems").select("*").eq("id", problem_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return {"error": "Problem not found"}
    except Exception as e:
        return {"error": str(e)}