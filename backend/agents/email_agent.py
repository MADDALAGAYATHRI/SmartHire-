from backend.utils.db import get_db
from datetime import datetime

def simple_sentiment(text: str)->str:
    t = (text or "").lower()
    pos = any(k in t for k in ["yes","accept","interested","thank you","great"])
    neg = any(k in t for k in ["no","reject","not interested","sorry"])
    if pos and not neg: return "positive"
    if neg and not pos: return "negative"
    return "neutral"

class EmailAgent:
    def __init__(self, db=None):
        #self.db = db or get_db()
        self.db = db if db is not None else get_db()


    def send_email(self, payload):
        # Stub: log email, mark as sent, add sentiment tag as neutral
        log = {
            "job_id": payload.job_id,
            "candidate_id": payload.candidate_id,
            "subject": payload.subject,
            "template": payload.template,
            "sender": payload.sender,
            "sent_at": datetime.utcnow(),
            "status": "sent",
            "reply_text": None,
            "reply_sentiment": "neutral"
        }
        res = self.db.emails.insert_one(log)
        log["id"] = str(res.inserted_id)
        return log
