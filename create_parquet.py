import pandas as pd
import snowflake.connector
import pyarrow as pa
import pyarrow.parquet as pq

# Connect to Snowflake
conn = snowflake.connector.connect(
    user='ashokpallekonda',
    password='chennai1306*Ajh',
    account='ZHCMWUB-LY28701',
    warehouse='WG_WH',
    database='WG_DB',
    schema='ANALYTICS_SCHEMA'
)

# Load candidate features
df_candidates = pd.read_sql("SELECT CANDIDATE_ID, SKILL_LIST, EXPERIENCE_YEARS, LOCATION FROM FCT_CANDIDATE_FEATURES", conn)
df_candidates['event_timestamp'] = pd.Timestamp.now()  # Add timestamp
df_candidates.to_parquet('candidate_data.parquet', index=False)

# Load job features
df_jobs = pd.read_sql("SELECT JOB_ID, REQUIRED_SKILL_LIST, LOCATION FROM FCT_JOB_FEATURES", conn)
df_jobs['event_timestamp'] = pd.Timestamp.now()  # Add timestamp
df_jobs.to_parquet('job_data.parquet', index=False)

conn.close()
print("PARQUET FILES CREATED: candidate_data.parquet, job_data.parquet")