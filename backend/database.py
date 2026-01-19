
"""
Database connection management.
Handles MongoDB and Google Sheets connections based on environment variables.
"""

import os
import json
from typing import Optional, Any

# Optional imports to avoid crashing if dependencies are missing during local dev
try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    HAS_SHEETS = True
except ImportError:
    HAS_SHEETS = False


class DatabaseManager:
    """Singleton manager for database connections."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_connections()
        return cls._instance
    
    def _init_connections(self):
        """Initialize connections based on environment variables."""
        self.mongo_collection: Optional[Any] = None
        self.sheet: Optional[Any] = None
        
        # 1. MongoDB Setup
        mongo_uri = os.getenv("MONGODB_URI")
        if mongo_uri and HAS_MONGO:
            try:
                client = MongoClient(mongo_uri)
                # Parse database name from URI or default to 'simulation_db'
                db = client.get_database("simulation_db")
                self.mongo_collection = db.get_collection("sessions")
                print("✅ MongoDB connected.")
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
        elif mongo_uri and not HAS_MONGO:
            print("⚠️ MONGODB_URI found but pymongo not installed.")
            
        # 2. Google Sheets Setup
        sheets_creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        if sheets_creds_json and sheet_id and HAS_SHEETS:
            try:
                scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                
                # Handle if env var is stringified JSON
                if isinstance(sheets_creds_json, str):
                    try:
                        creds_dict = json.loads(sheets_creds_json)
                        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                    except json.JSONDecodeError:
                        print("❌ GOOGLE_SHEETS_CREDENTIALS invalid JSON.")
                        creds = None
                
                if creds:
                    client = gspread.authorize(creds)
                    self.sheet = client.open_by_key(sheet_id).sheet1
                    print("✅ Google Sheets connected.")
            except Exception as e:
                print(f"❌ Google Sheets connection failed: {e}")

    def save_session(self, session_data: dict):
        """Save session data to all configured persistence layers."""
        
        # MongoDB: Upsert the full document
        if self.mongo_collection:
            try:
                self.mongo_collection.replace_one(
                    {"session_id": session_data["session_id"]},
                    session_data,
                    upsert=True
                )
            except Exception as e:
                print(f"❌ Failed to save to MongoDB: {e}")
                
        # Google Sheets: Append summary row
        if self.sheet:
            try:
                # Create a flat row summary
                row = [
                    session_data.get("session_id", ""),
                    session_data.get("participant_name", "Anonymous"),
                    session_data.get("start_time", ""),
                    len(session_data.get("episodes", {})),
                    # Add more summary fields as needed
                ]
                self.sheet.append_row(row)
            except Exception as e:
                print(f"❌ Failed to save to Google Sheets: {e}")

# Global instance
db_manager = DatabaseManager()
