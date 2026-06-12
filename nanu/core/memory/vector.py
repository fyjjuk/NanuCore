"""Búsqueda semántica usando SQLite con extensión FTS5 (trigramas)."""
import sqlite3
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class SQLiteVectorStore:
    """Almacén vectorial ligero basado en SQLite FTS5 trigramas."""
    
    def __init__(self, db_path: str = "nanu/data/vectors.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos y las tablas FTS."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents 
            USING fts5(content, tokenize='trigram');
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                doc_id TEXT PRIMARY KEY,
                namespace TEXT,
                source TEXT,
                timestamp TEXT,
                raw_metadata TEXT
            );
        """)
        self.conn.commit()
    
    async def index(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Indexa un documento en la tabla FTS y guarda metadatos."""
        # Insertar en FTS
        self.conn.execute("INSERT INTO documents (rowid, content) VALUES (null, ?)", (content,))
        rowid = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        # Guardar metadatos asociados al rowid
        meta_json = json.dumps(metadata, ensure_ascii=False)
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata (doc_id, namespace, source, timestamp, raw_metadata) VALUES (?, ?, ?, ?, ?)",
            (doc_id, metadata.get("namespace", "default"), metadata.get("source", ""), metadata.get("timestamp", ""), meta_json)
        )
        # También guardar relación rowid-doc_id
        self.conn.execute("CREATE TABLE IF NOT EXISTS doc_map (rowid INTEGER PRIMARY KEY, doc_id TEXT)")
        self.conn.execute("INSERT OR REPLACE INTO doc_map (rowid, doc_id) VALUES (?, ?)", (rowid, doc_id))
        self.conn.commit()
    
    async def search(self, query: str, top_k: int = 5, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca documentos similares por trigramas."""
        # Escapar comillas simples
        safe_query = query.replace("'", "''")
        # Búsqueda FTS
        sql = """
            SELECT documents.rowid, documents.content, metadata.raw_metadata,
                   bm25(documents) as rank
            FROM documents
            LEFT JOIN metadata ON documents.rowid = metadata.rowid
            WHERE documents.content MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        params = [safe_query, top_k]
        cursor = self.conn.execute(sql, params)
        results = []
        for row in cursor:
            results.append({
                "rowid": row[0],
                "content": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "rank": row[3]
            })
        return results
    
    async def delete_namespace(self, namespace: str) -> None:
        """Elimina todos los documentos de un namespace."""
        # Obtener rowids de los documentos a eliminar
        rows = self.conn.execute("SELECT rowid FROM metadata WHERE namespace = ?", (namespace,)).fetchall()
        rowids = [r[0] for r in rows]
        if rowids:
            placeholders = ",".join("?" * len(rowids))
            self.conn.execute(f"DELETE FROM documents WHERE rowid IN ({placeholders})", rowids)
            self.conn.execute(f"DELETE FROM metadata WHERE namespace = ?", (namespace,))
            self.conn.execute(f"DELETE FROM doc_map WHERE rowid IN ({placeholders})", rowids)
            self.conn.commit()
    
    def close(self):
        self.conn.close()
