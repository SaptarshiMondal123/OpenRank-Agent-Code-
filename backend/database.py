import os
from typing import Dict, Any, List
from supabase import create_client # type: ignore

_supabase_client = None

def load_dotenv_if_needed(dotenv_path: str = ".env") -> None:
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
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

def get_supabase_client():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    load_dotenv_if_needed()
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY is not set.")
    _supabase_client = create_client(url, key)
    return _supabase_client

def get_dashboard_stats():
    client = get_supabase_client()
    # Fetch last 50 submissions to calculate "Recent Trends"
    response = client.table("submissions").select("*").order("created_at", desc=True).limit(50).execute()
    data = response.data

    if not data:
        return {
            "total": 0, 
            "pass_rate": 0, 
            "patterns": [], 
            "recent": []
        }

    # 1. Calculate Pass Rate
    passed = sum(1 for d in data if d.get("status") == "PASS")
    total = len(data)
    pass_rate = round((passed / total) * 100, 1)

    # 2. Aggregate Patterns for Pie Chart
    patterns = {}
    for d in data:
        p = d.get("pattern_detected", "Unknown")
        # Clean up the string slightly
        if p == "Analysis Failed" or p is None: 
            p = "Unknown"
        patterns[p] = patterns.get(p, 0) + 1
    
    # Format for Recharts: [{name: "Recursion", value: 10}, ...]
    pattern_chart = [{"name": k, "value": v} for k, v in patterns.items()]

    # 3. Format Recent Activity Table
    recent = []
    for d in data[:7]: # Top 7 most recent
        recent.append({
            "id": d.get("id"),
            "problem": d.get("problem_name", "Unknown Problem"),
            "status": d.get("status", "FAIL"),
            "date": d.get("created_at", "").split("T")[0], # Extract YYYY-MM-DD
            "complexity": d.get("time_complexity", "N/A"),
            "space": d.get("space_complexity", "N/A")
        })

    return {
        "total": total,
        "pass_rate": pass_rate,
        "patterns": pattern_chart,
        "recent": recent
    }
