from pydantic import BaseModel, Field  # type: ignore
from typing import List

# --- EXISTING ---
class CodeSubmission(BaseModel):
    code: str
    problem_description: str
    language: str = "python"

class ComplexityAnalysis(BaseModel):
    time_complexity: str = Field(..., description="Estimated Big O Time Complexity")
    space_complexity: str = Field(..., description="Estimated Big O Space Complexity")
    is_optimal: bool = Field(..., description="True if this meets constraints")

class FeedbackResponse(BaseModel):
    complexity: ComplexityAnalysis
    bugs: List[str]
    suggestions: List[str]

# --- NEW: ADD THIS ---
class CoachingTip(BaseModel):
    detected_pattern: str = Field(..., description="The pattern the user used (e.g., Brute Force)")
    optimal_pattern: str = Field(..., description="The best pattern (e.g., Sliding Window)")
    explanation: str = Field(..., description="Why the optimal pattern is better")
    similar_problems: List[str] = Field(..., description="3 similar LeetCode problem names")