import pandas as pd
import os
import hashlib
import secrets
import json
from datetime import datetime, timedelta

# User database file
USER_DB_FILE = "user_database.json"

def get_users():
    """Load user database from file or create empty one if not exists"""
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"users": {}, "sessions": {}}
    else:
        return {"users": {}, "sessions": {}}

def save_users(data):
    """Save user database to file"""
    with open(USER_DB_FILE, 'w') as f:
        json.dump(data, f)

def hash_password(password, salt=None):
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Create a hash with password and salt
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    return password_hash, salt

def register_user(username, password, full_name, role="user"):
    """Register a new user"""
    # Load existing users
    data = get_users()
    
    # Check if username already exists
    if username in data["users"]:
        return False, "Foydalanuvchi nomi allaqachon mavjud"
    
    # Hash password
    password_hash, salt = hash_password(password)
    
    # Create user object
    data["users"][username] = {
        "password_hash": password_hash,
        "salt": salt,
        "full_name": full_name,
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    
    # Save updated user database
    save_users(data)
    
    return True, "Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi"

def verify_user(username, password):
    """Verify user credentials"""
    # Load existing users
    data = get_users()
    
    # Check if username exists
    if username not in data["users"]:
        return False, "Foydalanuvchi nomi yoki parol noto'g'ri"
    
    # Get user data
    user = data["users"][username]
    
    # Hash provided password with stored salt
    password_hash, _ = hash_password(password, user["salt"])
    
    # Check if password matches
    if password_hash != user["password_hash"]:
        return False, "Foydalanuvchi nomi yoki parol noto'g'ri"
    
    # Create a session token
    session_token = secrets.token_hex(32)
    expiry = (datetime.now() + timedelta(days=1)).isoformat()
    
    # Store session
    data["sessions"][session_token] = {
        "username": username,
        "expiry": expiry
    }
    
    # Save updated session data
    save_users(data)
    
    return True, session_token

def validate_session(session_token):
    """Validate a session token"""
    if not session_token:
        return False, None
    
    # Load session data
    data = get_users()
    
    # Check if session exists
    if session_token not in data["sessions"]:
        return False, None
    
    # Get session data
    session = data["sessions"][session_token]
    
    # Check if session is expired
    if datetime.now() > datetime.fromisoformat(session["expiry"]):
        # Remove expired session
        del data["sessions"][session_token]
        save_users(data)
        return False, None
    
    # Get user data
    username = session["username"]
    
    if username not in data["users"]:
        return False, None
    
    return True, data["users"][username]

def logout_user(session_token):
    """Log out a user by removing their session"""
    if not session_token:
        return
    
    # Load session data
    data = get_users()
    
    # Remove session if it exists
    if session_token in data["sessions"]:
        del data["sessions"][session_token]
        save_users(data)

# Initialize with admin user if no users exist
def init_admin():
    data = get_users()
    if not data["users"]:
        register_user("admin", "admin123", "Administrator", "admin")