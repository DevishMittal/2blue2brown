import os
from dotenv import load_dotenv
import requests
import mimetypes
import shutil
import time
from flask import url_for

load_dotenv()

class SupabaseStorage:
    def __init__(self):
        self.supabase_url = os.getenv("supaurl")
        self.supabase_key = os.getenv("supakey")
        self.bucket_name = "images"
        # Create local storage directory if it doesn't exist
        self.local_storage_path = os.path.join(os.getcwd(), "local_storage")
        if not os.path.exists(self.local_storage_path):
            os.makedirs(self.local_storage_path)

    def upload_file(self, file_path, file_name=None):
        if file_name is None:
            file_name = os.path.basename(file_path)
        
        # Try to upload to Supabase first
        try:
            if self.supabase_url and self.supabase_key:
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type is None:
                    if file_path.lower().endswith(".mp4"):
                        mime_type = "video/mp4"
                    else:
                        mime_type = "application/octet-stream"
                upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{file_name}?upsert=true"
                with open(file_path, "rb") as file:
                    file_data = file.read()
                headers = {
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": mime_type,
                }
                response = requests.put(upload_url, headers=headers, data=file_data)
                if response.status_code == 200:
                    return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{file_name}"
        except Exception as e:
            print(f"Supabase upload failed: {str(e)}. Using local storage instead.")
        
        # Fall back to local storage
        return self._store_locally(file_path, file_name)
    
    def _store_locally(self, file_path, file_name):
        """Store file locally and return a relative URL for access"""
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{file_name}"
        local_path = os.path.join(self.local_storage_path, unique_filename)
        
        # Copy the file to local storage
        shutil.copy2(file_path, local_path)
        
        # Return a relative URL path that can be accessed by the frontend
        # This assumes you have set up a route to serve files from local_storage
        # Create a relative URL that the frontend can access
        relative_url = f"/api/media/{unique_filename}"
        return relative_url

    def retrieve_file(self, file_name, download_path=None):
        # First try to get from Supabase
        try:
            if self.supabase_url:
                url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{file_name}"
                response = requests.get(url)
                if response.status_code == 200:
                    if download_path:
                        with open(download_path, "wb") as f:
                            f.write(response.content)
                    return response.content
        except Exception as e:
            print(f"Supabase retrieval failed: {str(e)}. Trying local storage.")
        
        # Fall back to local storage
        local_path = os.path.join(self.local_storage_path, file_name)
        if os.path.exists(local_path):
            if download_path:
                shutil.copy2(local_path, download_path)
            with open(local_path, "rb") as f:
                return f.read()
        
        raise Exception(f"File not found: {file_name}")