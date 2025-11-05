from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import tempfile
import os
from pydantic import BaseModel
from github import Github

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str

@app.post("/run")
async def run_code(request: CodeRequest):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
            tmp.write(request.code.encode())
            tmp.flush()
            result = subprocess.run(
                ["python3", tmp.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True
            )
        os.unlink(tmp.name)
        return {"output": result.stdout + result.stderr}
    except subprocess.TimeoutExpired:
        return {"output": "Error: Code took too long to run (timeout)."}
    except Exception as e:
        return {"output": f"Error: {e}"}

# === Optional: Store shared code to GitHub ===
@app.post("/share")
async def share_code(request: CodeRequest):
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_NAME = "no-body-0/BackEnd-Repo"  # change this to your own repo
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    file_path = f"shared/{hash(request.code)}.py"
    repo.create_file(file_path, "Add shared code", request.code)
    raw_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{file_path}"
    return {"url": raw_url}
