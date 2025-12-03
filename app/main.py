# app/main.py — FINAL PRODUCTION VERSION: API + INSTANT GORGEOUS FRONTEND
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import numpy as np
import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# === IMPORT FRONTEND HTML ===
from app.frontend import get_frontend_html

app = FastAPI(
    title="WorkGallery AI — Job Recommender",
    description="Two-tower neural retrieval + LightGBM ranking | Live & Scalable",
    version="3.0"
)

# === LOAD MODEL & DATA ONCE ===
print("Loading production model & data...")
MODEL = joblib.load("models/lightgbm_ranker.pkl")
CAND_EMB = np.load("models/candidate_embeddings.npy")
JOB_EMB = np.load("models/job_embeddings.npy")
CAND_DF = pd.read_parquet("models/candidates.parquet")
JOB_DF = pd.read_parquet("models/jobs.parquet")

# Normalize column names
CAND_DF.columns = CAND_DF.columns.str.upper()
JOB_DF.columns = JOB_DF.columns.str.upper()

# Fast lookup
CAND_LOOKUP = CAND_DF.set_index("CANDIDATE_ID")


@app.get("/")
async def root():
    return {
        "message": "WorkGallery AI is LIVE & PRODUCTION READY",
        "candidates": len(CAND_DF),
        "jobs": len(JOB_DF),
        "endpoints": {
            "api": "/recommend?candidate_id=97",
            "beautiful_ui": "/frontend",
            "docs": "/docs"
        }
    }


@app.get("/recommend")
async def recommend(candidate_id: int, top_k: int = 10):
    if candidate_id not in CAND_LOOKUP.index:
        raise HTTPException(404, "Candidate not found. Try: 97, 12, 45, 88")

    cand = CAND_LOOKUP.loc[candidate_id]
    cand_vec = CAND_EMB[cand.name]

    # Vectorized scoring
    sims = cosine_similarity([cand_vec], JOB_EMB)[0]
    loc_match = (JOB_DF["LOCATION"] == cand["LOCATION"]).astype(int).values

    # Safe experience gap
    job_exp = JOB_DF["EXPERIENCE_YEARS"].fillna(5) if "EXPERIENCE_YEARS" in JOB_DF.columns else pd.Series(5, index=JOB_DF.index)
    exp_gap = np.abs(job_exp - cand["EXPERIENCE_YEARS"]).values

    X = np.column_stack([sims, loc_match, exp_gap])
    scores = MODEL.predict(X)
    top_idx = np.argsort(scores)[-top_k:][::-1]

    results = []
    for idx in top_idx:
        job = JOB_DF.iloc[idx]
        results.append({
            "job_id": int(job["JOB_ID"]),
            "title": job.get("JOB_TITLE", "Software Engineer"),
            "company": job.get("COMPANY", "Tech Corp"),
            "required_skills": job.get("REQUIRED_SKILL_LIST", "N/A")[:300],
            "location": job["LOCATION"],
            "score": round(float(scores[idx]), 4),
            "skill_similarity": round(float(sims[idx]), 4),
            "location_match": bool(loc_match[idx])
        })

    return {
        "candidate_id": candidate_id,
        "candidate": {
            "skills": cand["SKILL_LIST"][:500],
            "experience_years": int(cand["EXPERIENCE_YEARS"]),
            "location": cand["LOCATION"]
        },
        "recommendations": results,
        "total_jobs_scored": len(JOB_DF)
    }


# === INSTANT, BEAUTIFUL, NO-COLD-START FRONTEND ===
@app.get("/frontend", response_class=HTMLResponse)
async def frontend():
    return get_frontend_html()