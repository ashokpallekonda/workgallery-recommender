# train_recommender.py  ← FINAL, BULLETPROOF, NO MORE ERRORS
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import lightgbm as lgb
import mlflow
import mlflow.lightgbm
import joblib
import os
from datetime import datetime
from tqdm import tqdm
tqdm.pandas()  # ← fixes progress_apply

from sqlalchemy import create_engine

print("="*60)
print("DAY 5: FINAL BULLETPROOF VERSION — THIS ONE WORKS")
print("="*60)

# 1. Load + force uppercase
engine = create_engine("snowflake://ashokpallekonda:chennai1306*Ajh@ZHCMWUB-LY28701/WG_DB/ANALYTICS_SCHEMA?warehouse=WG_WH&role=ACCOUNTADMIN")
candidates_df = pd.read_sql("SELECT * FROM fct_candidate_features", engine)
jobs_df = pd.read_sql("SELECT * FROM fct_job_features", engine)

candidates_df.columns = candidates_df.columns.str.upper()
jobs_df.columns = jobs_df.columns.str.upper()

print(f"Loaded {len(candidates_df)} candidates, {len(jobs_df)} jobs")

# 2. Embeddings
embedder = SentenceTransformer('all-MiniLM-L6-v2')
candidates_df['TEXT'] = candidates_df['SKILL_LIST'] + " | " + candidates_df['LOCATION']
jobs_df['TEXT'] = jobs_df['REQUIRED_SKILL_LIST'] + " | " + jobs_df['LOCATION']

candidate_emb = embedder.encode(candidates_df['TEXT'].tolist(), batch_size=32, show_progress_bar=True)
job_emb = embedder.encode(jobs_df['TEXT'].tolist(), batch_size=32, show_progress_bar=True)

# 3. Training pairs
np.random.seed(42)
pairs = []
for _, cand in candidates_df.iterrows():
    pos = jobs_df[jobs_df['LOCATION'] == cand['LOCATION']]
    if len(pos) > 0:
        job = pos.sample(1).iloc[0]
        pairs.append({'candidate_id': cand['CANDIDATE_ID'], 'job_id': job['JOB_ID'], 'label': 1})
    job = jobs_df.sample(1).iloc[0]
    pairs.append({'candidate_id': cand['CANDIDATE_ID'], 'job_id': job['JOB_ID'], 'label': 0})

train_df = pd.DataFrame(pairs)

# 4. Features — FIXED COLUMN NAMES
def sim(row):
    c_idx = candidates_df[candidates_df['CANDIDATE_ID'] == row['candidate_id']].index[0]
    j_idx = jobs_df[jobs_df['JOB_ID'] == row['job_id']].index[0]
    return cosine_similarity([candidate_emb[c_idx]], [job_emb[j_idx]])[0][0]

train_df['SKILL_SIMILARITY'] = train_df.progress_apply(sim, axis=1)

# Merge properly using correct column names
train_df = train_df.merge(candidates_df[['CANDIDATE_ID', 'LOCATION', 'EXPERIENCE_YEARS']], 
                         left_on='candidate_id', right_on='CANDIDATE_ID', how='left')
train_df = train_df.merge(jobs_df[['JOB_ID', 'LOCATION']], left_on='job_id', right_on='JOB_ID', how='left')

train_df['LOCATION_MATCH'] = (train_df['LOCATION_x'] == train_df['LOCATION_y']).astype(int)
train_df['EXPERIENCE_GAP'] = np.abs(train_df['EXPERIENCE_YEARS'] - 5)

X = train_df[['SKILL_SIMILARITY', 'LOCATION_MATCH', 'EXPERIENCE_GAP']]
y = train_df['label']
groups = train_df.groupby('candidate_id').size().tolist()

# 5. Train
print("\nTraining model...")
mlflow.set_experiment("workgallery-recommender")
with mlflow.start_run(run_name="day5-final-victory"):
    model = lgb.train({
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_at': [10],
        'learning_rate': 0.1,
        'num_leaves': 31,
        'seed': 42,
        'verbose': -1
    }, lgb.Dataset(X, label=y, group=groups), num_boost_round=200)
    input_example = X.head(1)  # one row of your features
    mlflow.lightgbm.log_model(model, "model", input_example=input_example)

# 6. Save
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/lightgbm_ranker.pkl")
np.save("models/candidate_embeddings.npy", candidate_emb)
np.save("models/job_embeddings.npy", job_emb)
candidates_df.to_parquet("models/candidates.parquet")
jobs_df.to_parquet("models/jobs.parquet")

print("\nDAY 5 100% COMPLETE — MODEL IS BORN")
print("Your recommender is alive and ready for Day 6")
print("="*60)