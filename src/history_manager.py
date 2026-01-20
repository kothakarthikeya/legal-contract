import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

# Calculate path relative to this file
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(_BASE_DIR, "document_registry.json")

class HistoryManager:
    """Manages document upload history and versioning"""
    
    def __init__(self, registry_path: str = REGISTRY_PATH):
        self.registry_path = registry_path
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load the document registry from disk"""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, "r") as f:
                return json.load(f)
        return {"documents": {}, "last_updated": None}

    def _save_registry(self):
        """Save the document registry to disk"""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_path, "w") as f:
            json.dump(self.registry, f, indent=4)

    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def register_upload(self, file_path: str, doc_id: str) -> Dict[str, Any]:
        """Register a new document upload"""
        filename = os.path.basename(file_path)
        # Strip the UUID prefix if present
        original_name = filename.split('_', 1)[1] if '_' in filename else filename
        file_hash = self._calculate_hash(file_path)
        
        entry = {
            "doc_id": doc_id,
            "filename": filename,
            "original_name": original_name,
            "hash": file_hash,
            "timestamp": datetime.now().isoformat(),
            "size": os.path.getsize(file_path)
        }

        # Check for history of this original name
        if original_name not in self.registry["documents"]:
            self.registry["documents"][original_name] = {
                "versions": [],
                "tags": []
            }
        
        # Check if this exact hash already exists
        is_duplicate = any(v["hash"] == file_hash for v in self.registry["documents"][original_name]["versions"])
        
        if not is_duplicate:
            version_num = len(self.registry["documents"][original_name]["versions"]) + 1
            entry["version"] = version_num
            self.registry["documents"][original_name]["versions"].append(entry)
            result = {"status": "new_version", "version": version_num, "is_duplicate": False}
        else:
            prev_version = next(v for v in self.registry["documents"][original_name]["versions"] if v["hash"] == file_hash)
            result = {"status": "duplicate", "version": prev_version["version"], "is_duplicate": True}

        self._save_registry()
        return result

    def get_document_context(self, original_name: str) -> List[Dict[str, Any]]:
        """Get all versions of a document"""
        return self.registry["documents"].get(original_name, {}).get("versions", [])

    def add_feedback(self, doc_id: str, rating: int, comments: str) -> bool:
        """Add user feedback to a specific document version"""
        for doc_name, data in self.registry["documents"].items():
            for version in data["versions"]:
                if version["doc_id"] == doc_id:
                    version["feedback"] = {
                        "rating": rating,
                        "comments": comments,
                        "timestamp": datetime.now().isoformat()
                    }
                    self._save_registry()
                    return True
        return False

    def detect_relationship(self, file_path: str) -> Dict[str, Any]:
        """Detect if uploaded file is related to existing documents"""
        filename = os.path.basename(file_path)
        original_name = filename.split('_', 1)[1] if '_' in filename else filename
        
        history = self.get_document_context(original_name)
        if not history:
            return {"relationship": "new_document"}
        
        return {
            "relationship": "extension",
            "previous_versions_count": len(history),
            "last_version_id": history[-1]["doc_id"]
        }
