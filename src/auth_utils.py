import hashlib
import os
import sqlite3
from typing import Optional


# Use absolute path to ensure consistency regardless of CWD
# src/auth_utils.py is in src/, so we go up one level for the root
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_SRC_DIR)
DB_PATH = os.path.join(_ROOT_DIR, "users.db")



def init_db():
    """Initialize the user database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, email: str, password: str) -> bool:
    """Create a new user account"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        pw_hash = hash_password(password)
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                  (username, email, pw_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username: str, password: str) -> bool:
    """Verify user credentials"""
    print(f"DEBUG: Attempting login for user='{username}' using DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pw_hash = hash_password(password)
    c.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, pw_hash))
    user = c.fetchone()
    conn.close()
    
    if user:
        print(f"DEBUG: Login successful for '{username}'")
    else:
        print(f"DEBUG: Login failed for '{username}'. (Hash mismatch or user not found)")
        # Debug: Check if user exists at all
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        exists = c.fetchone()
        conn.close()
        if exists:
            print(f"DEBUG: User '{username}' exists, but password hash did not match.")
        else:
            print(f"DEBUG: User '{username}' does not exist.")
            
    return user is not None

# Initialize database on import
init_db()
