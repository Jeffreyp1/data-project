from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import logging
import pandas as pd
from pathlib import Path
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cache", "mappings.db")


class MappingCache:

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = DB_PATH
        Path(os.path.dirname(db_path)).mkdir(exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        # memory cache (first layer)
        self.memory = {}
        # SQLite database (second layer) 
        # self.conn = sqlite3.connect("cache/mappings.db")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS mapping_cache (
                signature     TEXT,
                column_name   TEXT,
                sap_field     TEXT,
                cleaning_fn   TEXT,
                custom_code   TEXT,
                use_count     INTEGER DEFAULT 0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY   (signature, column_name)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_overrides (
                user_id       TEXT,
                signature     TEXT,
                column_name   TEXT,
                sap_field     TEXT,
                cleaning_fn   TEXT,
                custom_code   TEXT,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY   (user_id, signature, column_name)
            )
        """)
        self.conn.commit()


    def build_signature(self, df: pd.DataFrame) -> str:
        # TODO CACHE-01: sort df.columns, JSON serialize, return SHA256 hex string
        columns = sorted(df.columns.tolist())

        raw = json.dumps(columns, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()


    def get(self, df: pd.DataFrame, user_id: str = None) -> dict | None:
        signature = self.build_signature(df)
        cache_key = f"{user_id}:{signature}" if user_id else signature
        if cache_key in self.memory:
            logger.info("Memory cache hit")
            return self.memory[cache_key]
        
        try:
            # retrieve value from database
            rows = self.conn.execute("SELECT column_name, sap_field, cleaning_fn, custom_code FROM mapping_cache WHERE signature = ? ", (signature,)).fetchall()
            # if rows return empty, then cache miss
            if not rows:
                logger.info(f"Cache MISS for {signature[:8]}")
                return None

            # rebuild the mappings 
            mappings = {}
            for row in rows:
                mappings[row[0]] = {
                    "source": row[0],
                    "target": row[1],
                    "cleaning_fn": row[2],
                    "custom_code": row[3]
                }
            if user_id:
                override = self.conn.execute("SELECT column_name, sap_field, cleaning_fn, custom_code FROM user_overrides WHERE user_id = ? and signature = ? ", (user_id, signature)).fetchall()

                # rebuild the mappings 
                for row in override:
                    mappings[row[0]] = {
                        "source": row[0],
                        "target": row[1],
                        "cleaning_fn": row[2],
                        "custom_code": row[3]
                    }
            #update user_count
            self.conn.execute(
                "UPDATE mapping_cache SET use_count = use_count + 1 WHERE signature = ?",
                (signature,)
            )
            self.conn.commit()

            # store field mappings in cache
            result = {"field_mappings":list(mappings.values())}
            self.memory[cache_key] = result

            logger.info(f"SQLite cache HIT for {signature[:8]} — {len(mappings)} mappings loaded")
            return result
        except Exception as e:
            logger.error(f"Cache read failed: {e}")
            return None
    def store(self, df: pd.DataFrame, agent_result: dict) -> None:
        signature = self.build_signature(df)
        mappings = agent_result.get("field_mappings",[])
        try:
            self.memory[signature] = agent_result
            for map in mappings:
                self.conn.execute("""INSERT OR REPLACE INTO mapping_cache 
                                        (signature, column_name, sap_field, cleaning_fn, custom_code)
                                        VALUES(?,?,?,?,?)
                                        
                """,
                                        (signature,map.get("source"), map.get("target"), map.get("cleaning_fn"), map.get("custom_code"))
                )
            self.conn.commit()
            logger.info(f"Cached {len(mappings)} mappings for {signature[:8]}")
        except Exception as e:
            logger.error(f"Cache store failed: {e}")

    def invalidate(self, df: pd.DataFrame, user_id: str = None) -> None:
        signature = self.build_signature(df)
        try:
            self.conn.execute(
                "DELETE FROM user_overrides WHERE user_id = ? and signature = ?",
                (user_id, signature)
            )
            self.memory.pop(f"{user_id}:{signature}", None)
            logger.info(f"Invalidated overrides for {user_id} on {signature[:8]}")
        except Exception as e:
            logger.error(f"Invalidate failed: {e}")            
            return None
    def store_user_override(self, df: pd.DataFrame, user_id: str, override: dict) -> None:
        signature = self.build_signature(df)
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO user_overrides
                    (user_id, signature, column_name, sap_field, cleaning_fn, custom_code)
                    VALUES(?,?,?,?,?,?)
            """,
                (user_id, signature, override["source"], override["target"], override["cleaning_fn"], override["custom_code"])
            )
            self.conn.commit()
            
            # delete memory_key 
            memory_key = f"{user_id}:{signature}"
            if memory_key in self.memory:
                del self.memory[memory_key]
            logger.info(f"Stored override for {user_id}: {override.get('source')} -> {override.get('target')}")
        except Exception as e:
            logger.error(f"Store override failed: {e}")
    ### clear is used for testing ONLY
    def clear(self) -> None:
        try:
            self.conn.execute("DELETE FROM mapping_cache")
            self.conn.execute("DELETE FROM user_overrides")
            self.conn.commit()
            self.memory.clear()
            logger.info("Cache cleared")

        except Exception as e:
            logger.error(f"Clear failed: {e}")