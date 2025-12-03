# app/frontend.py — FINAL: INSTANT, BEAUTIFUL, UNBREAKABLE HTML/JS FRONTEND
from fastapi.responses import HTMLResponse

def get_frontend_html():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WorkGallery AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; font-family: 'Segoe UI', sans-serif; }
        .card { background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="text-gray-800">
    <div class="container mx-auto px-4 py-12 max-w-4xl">
        <h1 class="text-5xl font-bold text-white text-center mb-4">WorkGallery AI</h1>
        <p class="text-xl text-white text-center mb-12 opacity-90">Production Job Recommender • Two-tower + LightGBM</p>
        
        <div class="card p-8">
            <div class="mb-8">
                <label class="block text-lg font-semibold mb-3">Candidate ID</label>
                <input id="candidateId" type="text" value="97" class="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg" placeholder="Try 97, 12, 45, 88">
            </div>
            
            <button onclick="getRecommendations()" class="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold py-4 px-8 rounded-lg text-xl hover:from-purple-700 hover:to-blue-700 transition shadow-lg">
                Find My Perfect Jobs
            </button>
        </div>
        
        <div id="results" class="mt-8"></div>
    </div>

    <script>
        async function getRecommendations() {
            const id = document.getElementById('candidateId').value.trim() || "97";
            const results = document.getElementById('results');
            results.innerHTML = '<div class="card p-12 text-center"><div class="spinner"></div><p class="text-xl">Finding your dream jobs...</p></div>';
            
            try {
                // ABSOLUTE URL — WORKS EVERY TIME
                const res = await fetch(`https://workgallery.onrender.com/recommend?candidate_id=${id}&top_k=15`);
                const data = await res.json();
                
                if (res.status !== 200) throw new Error("Not found");
                
                let html = `<div class="card p-8 mb-6"><p class="text-2xl font-bold mb-2">Top Jobs for Candidate ${id}</p>
                           <p class="text-lg opacity-80">Experience: ${data.candidate.experience_years} years • Location: ${data.candidate.location}</p>
                           <p class="text-sm opacity-70 mt-2">Skills: ${data.candidate.skills.substring(0, 150)}...</p></div>`;
                
                data.recommendations.forEach(job => {
                    const match = job.location_match ? '<span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-bold">Location Match</span>' : '';
                    html += `
                    <div class="card p-6 mb-6 hover:shadow-xl transition">
                        <div class="flex justify-between items-start mb-4">
                            <div>
                                <h3 class="text-2xl font-bold">#${job.job_id} • ${job.title || 'Software Engineer'}</h3>
                                <p class="text-lg opacity-70">${job.company || 'Tech Corp'} • ${job.location}</p>
                            </div>
                            <div class="text-right">
                                <p class="text-3xl font-bold text-purple-600">${job.score.toFixed(3)}</p>
                                <p class="text-sm opacity-70">Score</p>
                                ${match}
                            </div>
                        </div>
                        <p class="text-gray-700 mb-3"><strong>Required Skills:</strong> ${job.required_skills.substring(0, 180)}...</p>
                        <div class="flex gap-4 text-sm">
                            <span class="bg-blue-100 text-blue-800 px-4 py-2 rounded-full">Skill Match: ${job.skill_similarity.toFixed(3)}</span>
                        </div>
                    </div>`;
                });
                
                results.innerHTML = html;
            } catch (e) {
                results.innerHTML = '<div class="card p-8 text-center text-red-600"><p class="text-xl">Invalid candidate ID. Try 97, 12, 45, or 88</p></div>';
            }
        }
        
        // Delay auto-load by 3 seconds to let model warm up
        window.onload = () => setTimeout(() => {
            document.getElementById('candidateId').value = "97";
            getRecommendations();
        }, 3000);
    </script>
</body>
</html>
    """)