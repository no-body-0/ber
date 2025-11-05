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
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    stdin_data = data.get("stdin", "")

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
            temp_file.write(code)
            temp_path = temp_file.name

        result = subprocess.run(
            ["python3", temp_path],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10
        )

        os.remove(temp_path)
        output = result.stdout or result.stderr
        return {"output": output.strip() or "No output."}

    except subprocess.TimeoutExpired:
        return {"output": "Error: Execution timed out."}
    except Exception as e:
        return {"output": f"Error: {str(e)}"}


# === Optional: Store shared code to GitHub ===
@app.post("/share")
async def share_code(request: CodeRequest):
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_NAME = "no-body-0/ber"  # change this to your own repo
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    file_path = f"shared/{hash(request.code)}.py"
    repo.create_file(file_path, "Add shared code", request.code)
    raw_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{file_path}"
    return {"url": raw_url}
