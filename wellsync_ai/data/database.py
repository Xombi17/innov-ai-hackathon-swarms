"""
Database setup and management for WellSync AI system.

Handles SQLite database initialization, schema creation,
and connection management for persistent storage.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from wellsync_ai.utils.config import get_config

config = get_config()


class DatabaseManager:
    """Manages SQLite database operations for WellSync AI."""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            # Extract path from database URL
            self.db_path = config.database_url.replace("sqlite:///", "")
    
    def initialize_database(self):
        """Initialize the database with required tables."""
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
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_memory_name ON agent_memory(agent_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_memory_type ON agent_memory(memory_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wellness_plans_user ON wellness_plans(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_requests_endpoint ON api_requests(endpoint)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_requests_user ON api_requests(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_feedback_state ON user_feedback(state_id)")
            
            conn.commit()
            print("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def store_shared_state(self, state_data: Dict[str, Any]) -> int:
        """Store shared state data."""
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM shared_states ORDER BY created_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return json.loads(row['data']) if row else None
    
    def store_agent_memory(self, agent_name: str, memory_type: str, 
                          data: Dict[str, Any], session_id: Optional[str] = None) -> int:
        """Store agent memory data."""
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
    
    def get_agent_memory(self, agent_name: str, memory_type: str, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get agent memory data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT data, timestamp FROM agent_memory 
                   WHERE agent_name = ? AND memory_type = ? 
                   ORDER BY created_at DESC LIMIT ?""",
                (agent_name, memory_type, limit)
            )
            rows = cursor.fetchall()
            return [json.loads(row['data']) for row in rows]
    
    def store_wellness_plan(self, user_id: str, plan_data: Dict[str, Any], 
                           confidence: float) -> int:
        """Store a wellness plan."""
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
    
    def log_system_event(self, level: str, message: str, 
                        component: Optional[str] = None, 
                        data: Optional[Dict[str, Any]] = None):
        """Log a system event."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO system_logs 
                   (level, message, component, data, timestamp) 
                   VALUES (?, ?, ?, ?, ?)""",
                (level, message, component, 
                 json.dumps(data) if data else None, 
                 datetime.now().isoformat())
            )
            conn.commit()
    
    def log_api_request(self, endpoint: str, method: str, request_data: Dict[str, Any],
                       request_id: str, user_id: Optional[str] = None,
                       response_status: Optional[int] = None,
                       response_data: Optional[Dict[str, Any]] = None,
                       duration_ms: Optional[float] = None) -> int:
        """Log an API request."""
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
                           request_id: Optional[str] = None) -> int:
        """Store user feedback."""
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
    
    def get_user_feedback(self, state_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user feedback for a state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT feedback_data, timestamp FROM user_feedback 
                   WHERE state_id = ? ORDER BY created_at DESC LIMIT ?""",
                (state_id, limit)
            )
            rows = cursor.fetchall()
            return [json.loads(row['feedback_data']) for row in rows]
    
    def health_check(self) -> bool:
        """Check database health."""
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