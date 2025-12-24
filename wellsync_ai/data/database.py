import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except Exception:
    SUPABASE_AVAILABLE = False

from wellsync_ai.utils.config import get_config

config = get_config()
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages Supabase (Cloud) or SQLite (Local) operations for WellSync AI."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.use_supabase = SUPABASE_AVAILABLE and config.supabase_url and config.supabase_key
        
        if self.use_supabase:
            self.supabase: Client = create_client(config.supabase_url, config.supabase_key)
            print("🚀 DatabaseManager initialized with Supabase")
        else:
            if db_path:
                self.db_path = db_path
            else:
                self.db_path = config.database_url.replace("sqlite:///", "")
            print(f"📁 DatabaseManager initialized with SQLite: {self.db_path}")
    
    def initialize_database(self):
        """Initialize local database if using SQLite. Supabase schema is handled via migration tools."""
        if self.use_supabase:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Shared states table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shared_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Agent memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    session_id TEXT,
                    data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    profile_data TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Wellness plans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wellness_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    plan_data TEXT NOT NULL,
                    confidence REAL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    component TEXT,
                    data TEXT,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # API requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    user_id TEXT,
                    request_data TEXT,
                    response_status INTEGER,
                    response_data TEXT,
                    duration_ms REAL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state_id TEXT NOT NULL,
                    request_id TEXT,
                    feedback_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("Local database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection (SQLite only)."""
        if self.use_supabase:
            raise RuntimeError("DatabaseManager is using Supabase; get_connection is for SQLite only.")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def store_shared_state(self, state_data: Dict[str, Any]) -> Any:
        """Store shared state data."""
        if self.use_supabase:
            response = self.supabase.table("shared_states").insert({
                "data": state_data,
                "timestamp": datetime.now().isoformat()
            }).execute()
            return response.data[0]['id'] if response.data else None
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO shared_states (timestamp, data) VALUES (?, ?)",
                (datetime.now().isoformat(), json.dumps(state_data))
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_latest_shared_state(self) -> Optional[Dict[str, Any]]:
        """Get the most recent shared state."""
        if self.use_supabase:
            response = self.supabase.table("shared_states").select("data").order("created_at", desc=True).limit(1).execute()
            return response.data[0]['data'] if response.data else None
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM shared_states ORDER BY created_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return json.loads(row['data']) if row else None
    
    def store_agent_memory(self, agent_name: str, memory_type: str, 
                          data: Dict[str, Any], session_id: Optional[str] = None) -> Any:
        """Store agent memory data."""
        if self.use_supabase:
            response = self.supabase.table("agent_memory").insert({
                "agent_name": agent_name,
                "memory_type": memory_type,
                "session_id": session_id,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }).execute()
            return response.data[0]['id'] if response.data else None
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO agent_memory 
                   (agent_name, memory_type, session_id, data, timestamp) 
                   VALUES (?, ?, ?, ?, ?)""",
                (agent_name, memory_type, session_id, 
                 json.dumps(data), datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid
    
    def store_wellness_plan(self, user_id: str, plan_data: Dict[str, Any], 
                           confidence: float) -> Any:
        """Store a wellness plan."""
        if self.use_supabase:
            response = self.supabase.table("wellness_plans").insert({
                "user_id": user_id,
                "plan_data": plan_data,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }).execute()
            return response.data[0]['id'] if response.data else None
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO wellness_plans 
                   (user_id, plan_data, confidence, timestamp) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, json.dumps(plan_data), confidence, datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid
    
    def log_api_request(self, endpoint: str, method: str, request_data: Dict[str, Any],
                       request_id: str, user_id: Optional[str] = None,
                       response_status: Optional[int] = None,
                       response_data: Optional[Dict[str, Any]] = None,
                       duration_ms: Optional[float] = None) -> Any:
        """Log an API request."""
        if self.use_supabase:
            response = self.supabase.table("api_requests").insert({
                "request_id": request_id,
                "endpoint": endpoint,
                "method": method,
                "user_id": user_id,
                "request_data": request_data,
                "response_status": response_status,
                "response_data": response_data,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat()
            }).execute()
            return response.data[0]['id'] if response.data else None
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO api_requests 
                   (request_id, endpoint, method, user_id, request_data, 
                    response_status, response_data, duration_ms, timestamp) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (request_id, endpoint, method, user_id,
                 json.dumps(request_data), response_status,
                 json.dumps(response_data) if response_data else None,
                 duration_ms, datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid
    
    def store_user_feedback(self, state_id: str, feedback: Dict[str, Any],
                           request_id: Optional[str] = None) -> Any:
        """Store user feedback."""
        if self.use_supabase:
            response = self.supabase.table("user_feedback").insert({
                "state_id": state_id,
                "request_id": request_id,
                "feedback_data": feedback,
                "timestamp": datetime.now().isoformat()
            }).execute()
            return response.data[0]['id'] if response.data else None
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO user_feedback 
                   (state_id, request_id, feedback_data, timestamp) 
                   VALUES (?, ?, ?, ?)""",
                (state_id, request_id, json.dumps(feedback), datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid
    
    def health_check(self) -> bool:
        """Check database health."""
        if self.use_supabase:
            try:
                # Querying a system table or any existing table to check connectivity
                self.supabase.table("wellness_plans").select("id").limit(1).execute()
                return True
            except Exception as e:
                logger.error(f"Supabase health check failed: {e}")
                return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False


# Global database manager instance
db_manager = DatabaseManager()


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


def initialize_database():
    """Initialize the database with required tables."""
    db_manager.initialize_database()
