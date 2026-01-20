import os
# Suppress TensorFlow logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_USE_LEGACY_KERAS"] = "1"

# Monkey-patch langchain.debug if missing (for newer versions)
try:
    import langchain
    if not hasattr(langchain, "debug"):
        langchain.debug = False
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from typing import Optional
from pydantic import BaseModel
import uuid
import json
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows.graph import app as workflow_app
from src.history_manager import HistoryManager
from src.auth_utils import create_user, verify_user

app = FastAPI(title="Contract Intelligence System", version="1.0.0")

# Use absolute paths
# Use absolute paths - verify structure for Render
# src/main.py is in src/, so project root is one level up
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)

# Define paths relative to Project Root (not src)
UPLOAD_DIR = os.path.join(_PROJECT_ROOT, "uploads")
REPORT_DIR = os.path.join(_PROJECT_ROOT, "reports")
FEEDBACK_FILE = os.path.join(_PROJECT_ROOT, "feedback.json")
INDEX_PATH = os.path.join(_PROJECT_ROOT, "index.html")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Pydantic models
class Feedback(BaseModel):
    doc_id: str
    rating: int
    comments: str
    timestamp: str

class UserAuth(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

def save_feedback(feedback: Feedback):
    """Save feedback to JSON file"""
    feedbacks = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                feedbacks = json.load(f)
        except:
            feedbacks = []
    
    feedbacks.append(feedback.dict())
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedbacks, f, indent=4)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML interface"""
    # Check Project Root first (standard deployment)
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return f.read()
            
    # Fallback to src/index.html (old structure)
    src_index = os.path.join(_SRC_DIR, "index.html")
    if os.path.exists(src_index):
        with open(src_index, "r", encoding="utf-8") as f:
            return f.read()
            
    return HTMLResponse(content="<h1>Error: index.html not found. Please ensure it is in the project root.</h1>", status_code=404)

@app.post("/register")
async def register(user: UserAuth):
    """Register a new user"""
    if not user.email:
        return JSONResponse(status_code=400, content={"message": "Email is required for registration"})
    success = create_user(user.username, user.email, user.password)
    if success:
        return {"message": "User registered successfully"}
    return JSONResponse(status_code=400, content={"message": "Username or email already exists"})

@app.post("/login")
async def login(user: UserAuth):
    """Login user"""
    success = verify_user(user.username, user.password)
    if success:
        return {"message": "Login successful", "username": user.username}
    return JSONResponse(status_code=401, content={"message": "Invalid username or password"})

@app.post("/analyze_contract")
async def analyze_contract(
    file: Optional[UploadFile] = File(None),
    link_url: Optional[str] = Form(None)
):
    """
    Analyze a contract document
    """
    if not file and not link_url:
        raise HTTPException(status_code=400, detail="Please provide either a file or a link_url.")
    
    # Handle Link (placeholder)
    if link_url:
        return HTMLResponse(content=f"<div class='alert'>Link received: {link_url}<br>(Link processing not fully implemented)</div>")

    # Handle File
    allowed_extensions = {".pdf", ".docx", ".doc", ".ppt", ".pptx", ".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        print(f"File saved: {file_path}")
        
        # Invoke LangGraph Workflow
        initial_state = {
            "file_path": file_path,
            "doc_id": file_id,
        }
        
        print("Starting workflow...")
        final_state = workflow_app.invoke(initial_state)
        
        # Get HTML report
        report_html = final_state.get("final_report", "<div class='error'>Analysis Failed or Returned No Output.</div>")
        
        # Save report for download
        report_path = os.path.join(REPORT_DIR, f"{file_id}.html")
        try:
            with open(report_path, "w", encoding="utf-8") as rf:
                rf.write(report_html)
            print(f"Report saved: {report_path}")
        except Exception as fe:
            print(f"Failed to save report: {fe}")
            
        return HTMLResponse(content=report_html)
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)
        return HTMLResponse(content=f"<div class='error'>Error during analysis:<br><pre>{str(e)}</pre></div>", status_code=500)

@app.get("/history")
async def get_history():
    """Get document upload history"""
    hm = HistoryManager()
    return hm.registry

@app.post("/submit_feedback")
async def submit_feedback(feedback: Feedback):
    """Submit user feedback for a document"""
    try:
        hm = HistoryManager()
        success = hm.add_feedback(feedback.doc_id, feedback.rating, feedback.comments)
        
        # Also save to standalone feedback file
        save_feedback(feedback)
        
        if not success:
            return {"status": "partial_success", "message": "Feedback saved, but document ID not found in history."}
            
        return {"status": "success", "message": "Feedback submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

@app.get("/download_feedback")
async def download_feedback():
    """Download all feedback as JSON"""
    if os.path.exists(FEEDBACK_FILE):
        return FileResponse(path=FEEDBACK_FILE, filename="contract_analysis_feedback.json", media_type="application/json")
    return {"message": "No feedback available yet."}

@app.get("/download_report/{doc_id}")
async def download_report(doc_id: str):
    """Download a specific report"""
    report_path = os.path.join(REPORT_DIR, f"{doc_id}.html")
    if os.path.exists(report_path):
        return FileResponse(path=report_path, filename=f"report_{doc_id}.html", media_type="text/html")
    raise HTTPException(status_code=404, detail="Report not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Contract Intelligence System at http://0.0.0.0:{port}")
    print("Loading AI models... (this may take a minute)")
    uvicorn.run(app, host="0.0.0.0", port=port)
