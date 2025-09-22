from typing import List, Optional
from bson import ObjectId
from fastapi import UploadFile
from pdfminer.high_level import extract_text as pdf_text
from backend.utils.scoring import final_score, embed
from backend.utils.faiss_store import FaissStore
from backend.utils.db import get_db

class ResumeAgent:
    def __init__(self, db=None):
        #self.db = db or get_db()
        self.db = db if db is not None else get_db()

        self.faiss = FaissStore(path="/data/faiss.index", dim=256)

    def to_oid(self, id_str: str) -> ObjectId:
        return ObjectId(id_str)

    async def process_one(self, job, file: UploadFile):
        content = await file.read()
        text = ""
        if file.filename.lower().endswith(".pdf"):
            # write temp
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp.flush()
                text = pdf_text(tmp.name)
        else:
            text = content.decode("utf-8", errors="ignore")

        # naive extraction of name/email
        import re
        email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        name = file.filename.rsplit(".",1)[0]

        score = final_score(job.get("description",""), job.get("required_skills",[]), text)
        cand = {
            "job_id": str(job["_id"]),
            "name": name,
            "email": email.group(0) if email else "",
            "raw_text": text[:100000],  # cap
            "score": score,
            "experience_years": 0,
            "status": "new"
        }
        res = self.db.candidates.insert_one(cand)
        cand_id = str(res.inserted_id)

        # add to vector store
        vec = embed(text)  # (1, dim)
        self.faiss.add(vec, [cand_id])
        return cand_id, score

    def fetch_candidates(self, q):
        query = {"job_id": q.job_id, "score": {"$gte": q.min_score, "$lte": q.max_score}}
        if q.status:
            query["status"] = q.status
        out = []
        for c in self.db.candidates.find(query).sort("score",-1):
            c["id"] = str(c.pop("_id"))
            out.append({
                "id": c["id"],
                "job_id": c["job_id"],
                "name": c.get("name",""),
                "email": c.get("email",""),
                "score": c.get("score",0.0),
                "experience_years": c.get("experience_years",0.0),
                "status": c.get("status","new"),
            })
        return out
