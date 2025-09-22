from typing import List
from backend.utils.db import get_db
from backend.agents.resume_agent import ResumeAgent

class MasterNode:
    def __init__(self, db=None, resume_agent: ResumeAgent=None, email_agent=None):
        #self.db = db or get_db()
        self.db = db if db is not None else get_db()
        

        self.resume_agent = resume_agent or ResumeAgent(self.db)
        self.email_agent = email_agent

    async def process_resumes(self, job_id: str, files: List):
        job = self.db.jobs.find_one({"_id": self.resume_agent.to_oid(job_id)})
        processed = []
        for f in files:
            cid, score = await self.resume_agent.process_one(job, f)
            processed.append({"candidate_id": cid, "score": score})
        return processed
