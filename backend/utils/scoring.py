from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

def clean(text:str)->str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def tfidf_score(jd:str, resume:str)->float:
    jd_c, res_c = clean(jd), clean(resume)
    vec = TfidfVectorizer(min_df=1)
    X = vec.fit_transform([jd_c, res_c])
    score = cosine_similarity(X[0], X[1])[0,0]
    return float(round(score*100, 2))

def keyword_boost(required_skills, resume):
    resume_l = resume.lower()
    hit = sum(1 for s in required_skills if s.lower() in resume_l)
    return min(20, hit * 4)  # up to +20

def final_score(jd, required_skills, resume):
    base = tfidf_score(jd, resume)
    return float(min(100.0, base + keyword_boost(required_skills, resume)))

def embed(text: str, dim:int=256):
    # Simple, deterministic pseudo-embedding using tf-idf projection
    v = TfidfVectorizer(min_df=1, max_features=dim)
    X = v.fit_transform([clean(text)])
    dense = X.toarray().astype('float32')
    # normalize for inner product
    norm = np.linalg.norm(dense, axis=1, keepdims=True) + 1e-10
    return (dense / norm).astype('float32')
