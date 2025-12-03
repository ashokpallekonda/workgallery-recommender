# app/main.py — FINAL PRODUCTION VERSION WITH BEAUTIFUL FRONTEND
from fastapi import FastAPI, HTTPException
import numpy as np
import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import subprocess
import sys

app = FastAPI(
    title="WorkGallery AI — Job Recommender",
    description="Two-tower neural retrieval + LightGBM ranking | Live & Scalable",
    version="2.0"
)

print("Loading production model & data...")
MODEL = joblib.load("models/lightgbm_ranker.pkl")
CAND_EMB = np.load("models/candidate_embeddings.npy")
JOB_EMB = np.load("models/job_embeddings.npy")
CAND_DF = pd.read_parquet("models/candidates.parquet")
JOB_DF = pd.read_parquet("models/jobs.parquet")

# Normalize column names
CAND_DF = CAND_DF.copy()
JOB_DF = JOB_DF.copy()
CAND_DF.columns = CAND_DF.columns.str.upper()
JOB_DF.columns = JOB_DF.columns.str.upper()

# Fast lookup by candidate_id
CAND_LOOKUP = CAND_DF.set_index("CANDIDATE_ID")


@app.get("/")
async def root():
    return {
        "message": "WorkGallery AI is LIVE",
        "candidates": len(CAND_DF),
        "jobs": len(JOB_DF),
        "docs": "/docs",
        "frontend": "/frontend"
    }


@app.get("/recommend")
async def recommend(candidate_id: int, top_k: int = 10):
    if candidate_id not in CAND_LOOKUP.index:
        raise HTTPException(404, f"Candidate {candidate_id} not found. Try 97, 12, 45, 88")

    cand = CAND_LOOKUP.loc[candidate_id]
    cand_vec = CAND_EMB[cand.name]

    # Vectorized scoring
    sims = cosine_similarity([cand_vec], JOB_EMB)[0]
    loc_match = (JOB_DF["LOCATION"] == cand["LOCATION"]).astype(int).values

    # Safe experience handling
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
            "required_skills": job.get("REQUIRED_SKILL_LIST", "N/A"),
            "location": job["LOCATION"],
            "score": round(float(scores[idx]), 4),
            "skill_similarity": round(float(sims[idx]), 4),
            "location_match": bool(loc_match[idx])
        })

    return {
        "candidate_id": candidate_id,
        "candidate": {
            "skills": cand["SKILL_LIST"],
            "experience_years": int(cand["EXPERIENCE_YEARS"]),
            "location": cand["LOCATION"]
        },
        "recommendations": results,
        "total_jobs_scored": len(JOB_DF)
    }


# BEAUTIFUL FRONTEND ROUTE
@app.get("/frontend")
def frontend():
    """Launch stunning Streamlit UI"""
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "app/frontend.py",
        "--server.port", "8000",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]
    subprocess.run(cmd)
    return {"status": "frontend launched"}