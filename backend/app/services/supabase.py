import os
import requests
from dotenv import load_dotenv
import json
from datetime import datetime
import uuid
import time
import traceback

load_dotenv()

SUPABASE_URL = os.getenv('supaurl')
SUPABASE_ANON_KEY = os.getenv('supakey')

# Setup local storage directory
LOCAL_STORAGE_DIR = os.path.join(os.getcwd(), "backend", "local_db")
SESSIONS_FILE = os.path.join(LOCAL_STORAGE_DIR, "chat_sessions.json")
MESSAGES_FILE = os.path.join(LOCAL_STORAGE_DIR, "chat_messages.json")

# Create local storage directory if it doesn't exist
if not os.path.exists(LOCAL_STORAGE_DIR):
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

# Initialize local storage files if they don't exist
if not os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump([], f)

if not os.path.exists(MESSAGES_FILE):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump([], f)

def _read_local_sessions():
    """Read sessions from local storage"""
    try:
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is corrupted or doesn't exist, initialize with empty array
        with open(SESSIONS_FILE, 'w') as f:
            json.dump([], f)
        return []

def _write_local_sessions(sessions):
    """Write sessions to local storage"""
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f)

def _read_local_messages():
    """Read messages from local storage"""
    try:
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is corrupted or doesn't exist, initialize with empty array
        with open(MESSAGES_FILE, 'w') as f:
            json.dump([], f)
        return []

def _write_local_messages(messages):
    """Write messages to local storage"""
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f)

def get_chat_session(uuid_val):
    if not uuid_val or uuid_val == "NULL":
        return create_new_session()  # Create a new session if none exists
    
    # Try Supabase first    
    try:
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            url = f"{SUPABASE_URL}/rest/v1/chat_sessions?id=eq.{uuid_val}"
            print(url)
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                # If no session found with the given ID, create a new one
                if not result:
                    return create_new_session()
                return result
    except Exception as error:
        print(f"Supabase error: {error}. Using local storage instead.")
        traceback.print_exc()
    
    # Use local storage as fallback
    sessions = _read_local_sessions()
    for session in sessions:
        if session.get('id') == uuid_val:
            return [session]  # Return as list to match Supabase format
    
    # If no session found, create a new one
    return create_new_session()


def get_latest_chat_session():
    # Try Supabase first
    try:
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            url = f"{SUPABASE_URL}/rest/v1/chat_sessions?order=time_created.desc&limit=1"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result:  # Sessions found
                    return result[0]
    except Exception as error:
        print(f"Supabase error: {error}. Using local storage instead.")
        traceback.print_exc()
    
    # Use local storage as fallback
    sessions = _read_local_sessions()
    if sessions:
        # Sort by time_created in descending order
        sessions.sort(key=lambda x: x.get('time_created', ''), reverse=True)
        return sessions[0]
    
    # If no sessions found, create a new one
    return create_new_session()

def get_all_chat_sessions():
    # Try Supabase first
    try:
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            url = f"{SUPABASE_URL}/rest/v1/chat_sessions?order=time_created.desc"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
    except Exception as error:
        print(f"Supabase error: {error}. Using local storage instead.")
        traceback.print_exc()
    
    # Use local storage as fallback
    sessions = _read_local_sessions()
    # Sort by time_created in descending order
    sessions.sort(key=lambda x: x.get('time_created', ''), reverse=True)
    return sessions


def get_chat_histories(session_id):
    if not session_id or session_id == "NULL":
        return []  # Return empty list if no session
    
    # Try Supabase first
    try:
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            url = f"{SUPABASE_URL}/rest/v1/chat_messages?chat_session_id=eq.{session_id}&order=time_created.asc"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
    except Exception as error:
        print(f"Supabase error: {error}. Using local storage instead.")
        traceback.print_exc()
    
    # Use local storage as fallback
    messages = _read_local_messages()
    session_messages = [msg for msg in messages if msg.get('chat_session_id') == session_id]
    # Sort by time_created in ascending order
    session_messages.sort(key=lambda x: x.get('time_created', ''))
    return session_messages


def post_chat_session(session_title):
    try:
        url = f"{SUPABASE_URL}/rest/v1/chat_sessions"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Prefer': 'return=representation',
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
        }
        data = {
            "id": str(uuid.uuid4()),
            "title": session_title,
            "time_created": datetime.now().isoformat(),
        }
        
        response = requests.post(url, headers=headers, json=data)
        print("Response Content:", response.text)

        if response.status_code == 201:
            # If the session is created successfully, extract and return the 'id'
            session_data = response.json()
            if isinstance(session_data, list) and session_data:
                return {"success": "Session created successfully!", "session_id": session_data[0]['id']}
            return {"success": "Session created successfully!", "session_data": session_data}
        else:
            # If there is an error, return the error message
            return {"error": response.text}

    except Exception as error:
        return {"error": str(error)}


def post_message(sender, message, chat_session_id, image_url=None, manim_code=None, image_summary=None, video_url=None):
    # If no session ID, create a new session
    if not chat_session_id or chat_session_id == "NULL":
        new_session = create_new_session()
        if isinstance(new_session, dict) and "error" in new_session:
            return new_session
        elif isinstance(new_session, list) and new_session:
            chat_session_id = new_session[0].get("id", None)
        else:
            chat_session_id = new_session.get("id", None)
    
    # Prepare message data
    message_data = {
        "id": str(uuid.uuid4()),
        "sender": sender,
        "message": message,
        "chat_session_id": chat_session_id,
        "image_url": image_url,
        "manim_code": manim_code,
        "image_summary": image_summary,
        "video_url": video_url,
        "time_created": datetime.now().isoformat()
    }
    
    # Try Supabase first
    try:
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            url = f"{SUPABASE_URL}/rest/v1/chat_messages"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Prefer': 'return=representation',
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
            }
            response = requests.post(url, headers=headers, json=message_data)
            if response.status_code == 201:
                return {"success": "Message sent successfully!", "data": response.json()}
    except Exception as error:
        print(f"Supabase error: {error}. Using local storage instead.")
        traceback.print_exc()
    
    # Use local storage as fallback
    messages = _read_local_messages()
    messages.append(message_data)
    _write_local_messages(messages)
    return {"success": "Message saved locally!", "data": message_data}

def create_new_session():
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "title": f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "time_created": datetime.now().isoformat()
    }
    
    # Try Supabase first
    try:
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            url = f"{SUPABASE_URL}/rest/v1/chat_sessions"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Prefer': 'return=representation',
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
            }
            response = requests.post(url, headers=headers, json=session_data)
            if response.status_code == 201:
                try:
                    result = response.json()
                    if isinstance(result, list) and result:
                        return result  # return the inserted session object as a list
                    return result
                except ValueError:
                    print("Session created in Supabase, but response is not valid JSON")
    except Exception as error:
        print(f"Supabase error: {error}. Using local storage instead.")
        traceback.print_exc()
    
    # Use local storage as fallback
    sessions = _read_local_sessions()
    sessions.append(session_data)
    _write_local_sessions(sessions)
    return [session_data]  # Return as list to match Supabase format

