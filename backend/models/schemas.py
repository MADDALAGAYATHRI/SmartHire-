from pydantic import BaseModel, Field
from typing import List, Optional

class JobIn(BaseModel):
    title: str
    department: str
    required_skills: List[str] = []
    description: str

class JobOut(JobIn):
    id: str

class CandidateOut(BaseModel):
    id: str
    job_id: str
    name: str
    email: str
    score: float
    experience_years: float = 0
    status: str = "new"

class EmailIn(BaseModel):
    job_id: str
    candidate_id: str
    template: str
    subject: str
    sender: str = "hr@smarthire.local"

class Config(BaseModel):
    weights: dict = Field(default_factory=lambda: {"skills":0.4,"experience":0.4,"education":0.2})

class CandidateQuery(BaseModel):
    job_id: str
    min_score: float = 0
    max_score: float = 100
    status: Optional[str] = None
