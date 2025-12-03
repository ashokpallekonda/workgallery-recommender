# app/frontend.py — BEAUTIFUL LIVE FRONTEND IN 5 MINUTES
import streamlit as st
import requests
import json

st.set_page_config(page_title="WorkGallery AI", page_icon="briefcase", layout="centered")

st.title("WorkGallery AI")
st.markdown("### Production-grade job recommendations — live in your browser")

candidate_id = st.text_input("Enter Candidate ID (try 97)", value="97")
top_k = st.slider("Number of jobs to show", 5, 20, 10)

if st.button("Get My Top Jobs", type="primary"):
    with st.spinner("Finding your perfect matches..."):
        try:
            url = f"https://workgallery.onrender.com/recommend?candidate_id={candidate_id}&top_k={top_k}"
            response = requests.get(url, timeout=10)
            data = response.json()

            st.success(f"Top {top_k} jobs for Candidate {candidate_id}")
            
            cand = data["candidate"]
            st.info(f"**Skills**: {cand['skills'][:200]}{'...' if len(cand['skills']) > 200 else ''}\n\n"
                    f"**Experience**: {cand['experience_years']} years | **Location**: {cand['location']}")

            for job in data["recommendations"]:
                score = job["score"]
                with st.expander(f"{job['job_id']} • {job.get('title', 'Software Engineer')} • Score: {score:.3f} {'Match' if job['location_match'] else ''}"):
                    st.write(f"**Company**: {job.get('company', 'Tech Corp')}")
                    st.write(f"**Location**: {job['location']}")
                    st.write(f"**Required Skills**: {job['required_skills'][:300]}")
                    st.write(f"**Skill Similarity**: {job['skill_similarity']:.3f}")
                    if job['location_match']:
                        st.success("Location Match!")
        except:
            st.error("Invalid candidate ID or service warming up. Try 97, 12, 45, 88")

st.markdown("---")
st.caption("Built by Ashok Pallekonda • Two-tower + LightGBM • Live on Render.com")
st.markdown("[GitHub](https://github.com/ashokpallekonda/workgallery-recommender) • [LinkedIn Post](https://linkedin.com)")