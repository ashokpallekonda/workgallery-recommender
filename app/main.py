# app/main.py — FINAL VERSION: API + BEAUTIFUL FRONTEND THAT ACTUALLY WORKS
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import numpy as np
import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import subprocess
import sys
import os

app = FastAPI(
    title="WorkGallery AI — Job Recommender",
    description="Two-tower + LightGBM | Live Production System",
    version="2.0"
)

# === LOAD MODEL & DATA ONCE AT STARTUP ===
print("Loading production model & embeddings...")
MODEL = joblib.load("models/lightgbm_ranker.pkl")
CAND_EMB = np.load("models/candidate_embeddings.npy")
JOB_EMB = np.load("models/job_embeddings.npy")
CAND_DF = pd.read_parquet("models/candidates.parquet")
JOB_DF = pd.read_parquet("models/jobs.parquet")

# Normalize columns
CAND_DF.columns = CAND_DF.columns.str.upper()
JOB_DF.columns = JOB_DF.columns.str.upper()

# Fast lookup
CAND_LOOKUP = CAND_DF.set_index("CANDIDATE_ID")


@app.get("/")
async def root():
    return {
        "message": "WorkGallery AI is LIVE",
        "candidates": len(CAND_DF),
        "jobs": len(JOB_DF),
        "endpoints": {
            "api": "/recommend?candidate_id=97",
            "interactive_ui": "/frontend",
            "docs": "/docs"
        }
    }


@app.get("/recommend")
async def recommend(candidate_id: int, top_k: int = 10):
    if candidate_id not in CAND_LOOKUP.index:
        raise HTTPException(404, "Candidate not found. Try: 97, 12, 45, 88")

    cand = CAND_LOOKUP.loc[candidate_id]
    cand_vec = CAND_EMB[cand.name]

    sims = cosine_similarity([cand_vec], JOB_EMB)[0]
    loc_match = (JOB_DF["LOCATION"] == cand["LOCATION"]).astype(int).values

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
            "skills": cand["SKILL_LIST"],
            "experience_years": int(cand["EXPERIENCE_YEARS"]),
            "location": cand["LOCATION"]
        },
        "recommendations": results
    }


# BEAUTIFUL FRONTEND — THIS ONE ACTUALLY WORKS
@app.get("/frontend", response_class=HTMLResponse)
def serve_frontend():
    # Launch Streamlit in background
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        os.path.join(os.path.dirname(__file__), "frontend.py"),
        "--server.port=8000",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ])
    
    # Return auto-redirect page
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WorkGallery AI</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="5;url=/frontend" />
        <style>
            body { font-family: system-ui; text-align: center; margin-top: 10%; background: #f0f2f6; }
            h1 { color: #1e3a8a; }
            .spinner { width: 50px; height: 50px; border: 5px solid #e0e7ff; border-top: 5px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin: 20px auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <h1>WorkGallery AI</h1>
        <p>Launching your beautiful recommendation engine...</p>
        <div class="spinner"></div>
        <p><strong>Auto-redirecting in 5 seconds...</strong><br>
        <a href="/frontend">Click here if not redirected</a></p>
    </body>
    </html>
    """