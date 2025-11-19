"""
Database models for Star Citizen Inventory Manager
"""
import sqlite3
import os
from pathlib import Path


class Database:
    def __init__(self, db_path='data/inventory.db'):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                item_type TEXT,
                image_url TEXT,
                image_path TEXT,
                count INTEGER DEFAULT 1,
                notes TEXT,
                damage_reduction TEXT,
                min_temp REAL,
                max_temp REAL,
                radiation_resistance REAL,
                radiation_scrub_rate REAL,
                capacity REAL,
                volume REAL,
                is_favorite INTEGER DEFAULT 0,  -- NEU: Favoriten-Status (0=false, 1=true)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index on name for faster searching
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)
        ''')
        
        # Create index on item_type for filtering
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type)
        ''')
        
        # Add new columns if they don't exist (for existing databases)
        columns_to_add = [
            ('damage_reduction', 'TEXT'),
            ('min_temp', 'REAL'),
            ('max_temp', 'REAL'),
            ('radiation_resistance', 'REAL'),
            ('radiation_scrub_rate', 'REAL'),
            ('capacity', 'REAL'),
            ('volume', 'REAL'),
            ('added_to_inventory_at', 'TIMESTAMP'),  # NEU: Wann Item ins Inventar kam
            ('is_favorite', 'INTEGER DEFAULT 0')  # NEU: Favoriten-Spalte hinzufügen
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                self.cursor.execute(f'ALTER TABLE items ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError:
                # Column already exists
                pass
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()