import os
import sys
import uuid
import json
from typing import Optional

# -------------------------------------------------------------------
# Environment & logging safety (keep lightweight at startup)
# -------------------------------------------------------------------
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Monkey-patch langchain.debug if missing
try:
    import langchain
    if not hasattr(langchain, "debug"):
        langchain.debug = False
except ImportError:
    pass

# -------------------------------------------------------------------
# FastAPI imports
# -------------------------------------------------------------------
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from pydantic import BaseModel

# -------------------------------------------------------------------
# Path setup
# -------------------------------------------------------------------
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)
sys.path.append(_PROJECT_ROOT)

# -------------------------------------------------------------------
# Internal utilities
# -------------------------------------------------------------------
from src.history_manager import HistoryManager
from src.auth_utils import create_user, verify_user

# -------------------------------------------------------------------
# FastAPI app instance
# -------------------------------------------------------------------
app = FastAPI(title="Contract Intelligence System", version="1.0.0")
asgi_app = app  # ✅ This is what Gunicorn should point to

# -------------------------------------------------------------------
# Directories & files
# -------------------------------------------------------------------
UPLOAD_DIR = os.path.join(_PROJECT_ROOT, "uploads")
REPORT_DIR = os.path.join(_PROJECT_ROOT, "reports")
FEEDBACK_FILE = os.path.join(_PROJECT_ROOT, "feedback.json")
INDEX_PATH = os.path.join(_PROJECT_ROOT, "index.html")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# -------------------------------------------------------------------
# Lazy workflow (avoid OOM at startup)
# -------------------------------------------------------------------
workflow_app = None
def get_workflow_app():
    global workflow_app
    if workflow_app is None:
        from src.workflows.graph import app as _workflow_app
        workflow_app = _workflow_app
    return workflow_app

# -------------------------------------------------------------------
# Pydantic models
# -------------------------------------------------------------------
class Feedback(BaseModel):
    doc_id: str
    rating: int
    comments: str
    timestamp: str

class UserAuth(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def save_feedback(feedback: Feedback):
    feedbacks = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                feedbacks = json.load(f)
        except Exception:
            feedbacks = []

    feedbacks.append(feedback.dict())
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedbacks, f, indent=4)

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root():
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return f.read()
    src_index = os.path.join(_SRC_DIR, "index.html")
    if os.path.exists(src_index):
        with open(src_index, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(content="<h1>Error: index.html not found.</h1>", status_code=404)

@app.post("/register")
async def register(user: UserAuth):
    if not user.email:
        return JSONResponse(status_code=400, content={"message": "Email is required"})
    if create_user(user.username, user.email, user.password):
        return {"message": "User registered successfully"}
    return JSONResponse(status_code=400, content={"message": "Username or email already exists"})

@app.post("/login")
async def login(user: UserAuth):
    if verify_user(user.username, user.password):
        return {"message": "Login successful", "username": user.username}
    return JSONResponse(status_code=401, content={"message": "Invalid username or password"})

@app.post("/analyze_contract")
async def analyze_contract(file: Optional[UploadFile] = File(None), link_url: Optional[str] = Form(None)):
    if not file and not link_url:
        raise HTTPException(status_code=400, detail="Provide either a file or a link_url.")

    if link_url:
        return HTMLResponse(content=f"<div>Link received: {link_url}</div>")

    allowed_extensions = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        if os.path.getsize(file_path) == 0:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        initial_state = {"file_path": file_path, "doc_id": file_id}

        workflow = get_workflow_app()
        final_state = workflow.invoke(initial_state)
        report_html = final_state.get("final_report", "<div>Analysis failed.</div>")

        report_path = os.path.join(REPORT_DIR, f"{file_id}.html")
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write(report_html)

        return HTMLResponse(content=report_html)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"<pre>{str(e)}</pre>", status_code=500)

@app.get("/history")
async def get_history():
    hm = HistoryManager()
    return hm.registry

@app.post("/submit_feedback")
async def submit_feedback(feedback: Feedback):
    hm = HistoryManager()
    hm.add_feedback(feedback.doc_id, feedback.rating, feedback.comments)
    save_feedback(feedback)
    return {"status": "success"}

@app.get("/download_feedback")
async def download_feedback():
    if os.path.exists(FEEDBACK_FILE):
        return FileResponse(FEEDBACK_FILE, filename="feedback.json", media_type="application/json")
    return {"message": "No feedback available"}

@app.get("/download_report/{doc_id}")
async def download_report(doc_id: str):
    report_path = os.path.join(REPORT_DIR, f"{doc_id}.html")
    if os.path.exists(report_path):
        return FileResponse(report_path, filename=f"report_{doc_id}.html", media_type="text/html")
    raise HTTPException(status_code=404, detail="Report not found")

# -------------------------------------------------------------------
# Local run only
# -------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
