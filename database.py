import sqlite3
import os
import chromadb
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from chromadb.api.types import EmbeddingFunction
from config import SQLITE_DB_PATH, CHROMA_DB_DIR

class SimpleEmbeddingFunction(EmbeddingFunction):
    def __init__(self, n_features=128):
        self.vectorizer = HashingVectorizer(n_features=n_features)

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        vectors = self.vectorizer.transform(input).toarray()
        return vectors.tolist()
    
    def name(self):
        return "hashing_vectorizer"

class DatabaseManager:
    def __init__(self):
        self._init_sqlite()
        self._init_chroma()

    def _init_sqlite(self):
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                type TEXT DEFAULT 'original', 
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                token_count INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                metric_name TEXT,
                value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.sqlite_conn.commit()

    def _init_chroma(self):
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        self.embedding_fn = SimpleEmbeddingFunction(n_features=128)
        self.collection = self.chroma_client.get_or_create_collection(
            name="memory_embeddings",
            embedding_function=self.embedding_fn
        )

    def add_message(self, session_id, role, content, msg_type='original', token_count=0):
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, type, token_count) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, msg_type, token_count)
        )
        msg_id = cursor.lastrowid
        self.sqlite_conn.commit()
        
        if msg_type == 'original':
            self.add_embedding(msg_id, content, {"session_id": session_id, "role": role})
            
        return msg_id

    def add_embedding(self, msg_id, content, metadata):
        self.collection.add(
            ids=[str(msg_id)],
            documents=[content],
            metadatas=[metadata]
        )

    def search_embeddings(self, query_text, n_results=3, session_id=None):
        count = self.collection.count()
        if count == 0:
            return {"documents": [[]], "ids": [[]], "metadatas": [[]]}
            
        where_filter = {"session_id": session_id} if session_id else None
        n = max(1, min(n_results, count))
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n,
            where=where_filter
        )
        return results

    def get_session_messages(self, session_id, msg_type=None, limit=None):
        cursor = self.sqlite_conn.cursor()
        query = "SELECT role, content, type FROM messages WHERE session_id = ?"
        params = [session_id]
        if msg_type:
            query += " AND type = ?"
            params.append(msg_type)
        query += " ORDER BY timestamp ASC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_latest_messages(self, session_id, n=5):
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "SELECT role, content, type FROM messages WHERE session_id = ? AND type = 'original' ORDER BY timestamp DESC LIMIT ?",
            (session_id, n)
        )
        return cursor.fetchall()[::-1]

    def close(self):
        self.sqlite_conn.close()
