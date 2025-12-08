# -*- coding: utf-8 -*-
"""
database.py – loads all item names from your inventory.db once
Used by ocr_scanner.py for name correction
"""

import sqlite3
import os
from config import DB_PATH

# Global list with all item names
ITEM_DATABASE = []

def load_database():
    global ITEM_DATABASE
    if ITEM_DATABASE:  # already loaded
        return ITEM_DATABASE

    # Skip DB loading in Fast Debug Mode
    try:
        from config import FAST_DEBUG_MODE
        if FAST_DEBUG_MODE:
            print(f"[DB] Skipped loading (FAST_DEBUG_MODE=True)")
            return []
    except:
        pass

    if not os.path.exists(DB_PATH):
        print(f"[DB] Not found: {DB_PATH}")
        return []

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Simply get all names – GearCrate always has a "name" column
        cur.execute("SELECT name FROM items WHERE name IS NOT NULL AND trim(name) != ''")
        rows = cur.fetchall()
        conn.close()

        ITEM_DATABASE = sorted({row[0].strip() for row in rows})
        print(f"[DB] {len(ITEM_DATABASE)} items loaded from inventory.db.")

    except Exception as e:
        print(f"[DB] Error loading: {e}")
        ITEM_DATABASE = []

    return ITEM_DATABASE

# Load automatically on first import
load_database()