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
    language = data.get("language", "python")
    user_input = data.get("input", "")

    if language == "python":
        try:
            # Check if code expects input()
            if "input(" in code and not user_input:
                prompt_text = code.split("input(")[1].split(")")[0].strip("'\"") + ": "
                return {"prompt": prompt_text}
            
            # Execute Python code safely
            import subprocess, tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
                tmp.write(code.encode())
                tmp_path = tmp.name

            result = subprocess.run(
                ["python3", tmp_path],
                input=user_input,
                capture_output=True,
                text=True,
                timeout=5
            )

            os.remove(tmp_path)
            return {"output": result.stdout or result.stderr}

        except Exception as e:
            return {"output": f"Error: {str(e)}"}

    return {"output": "Unsupported language"}


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
