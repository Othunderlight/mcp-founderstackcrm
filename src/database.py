
import sqlite3
import logging
import json
from .config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create oauth_clients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oauth_clients (
        client_id TEXT PRIMARY KEY,
        client_secret TEXT NOT NULL,
        client_name TEXT NOT NULL,
        client_uri TEXT,
        redirect_uris TEXT NOT NULL,
        grant_types TEXT NOT NULL,
        response_types TEXT NOT NULL,
        scope TEXT NOT NULL,
        client_id_issued_at INTEGER NOT NULL,
        client_secret_expires_at INTEGER NOT NULL,
        created_at REAL NOT NULL
    )
    """)
    
    # Create oauth_codes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oauth_codes (
        code TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        redirect_uri TEXT NOT NULL,
        scope TEXT NOT NULL,
        user_info TEXT,
        code_challenge TEXT,
        code_challenge_method TEXT,
        created_at REAL NOT NULL,
        expires_at REAL NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database tables created or already exist.")

def dict_to_client(row):
    """Convert a dictionary to a client object, handling JSON strings."""
    if not row:
        return None
    client = dict(row)
    client['redirect_uris'] = json.loads(client['redirect_uris'])
    client['grant_types'] = json.loads(client['grant_types'])
    client['response_types'] = json.loads(client['response_types'])
    return client

def dict_to_code(row):
    """Convert a dictionary to a code object, handling JSON strings."""
    if not row:
        return None
    code = dict(row)
    if code.get('user_info'):
        code['user_info'] = json.loads(code['user_info'])
    return code
