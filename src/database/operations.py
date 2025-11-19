"""
Database operations (CRUD) for inventory items
"""
from datetime import datetime
import json


class ItemOperations:
    def __init__(self, database):
        """Initialize with database instance"""
        self.db = database
    
    def add_item(self, name, item_type=None, image_url=None, image_path=None, notes=None, initial_count=1, properties_json=None):
        """Add a new item or increment count if exists
        
        Args:
            initial_count: Starting count for new items (default 1, use 0 for imports)
        """
        try:
            # Check if item already exists
            existing = self.get_item_by_name(name)
            
            if existing:
                # Item exists - only increment if initial_count > 0
                if initial_count > 0:
                    new_count = existing['count'] + initial_count
                    
                    # Setze added_to_inventory_at, wenn Item von 0 zu >0 wechselt
                    if existing['count'] == 0 and new_count > 0:
                        self.db.cursor.execute('''
                            UPDATE items 
                            SET count = ?, updated_at = ?, added_to_inventory_at = ?
                            WHERE name = ?
                        ''', (new_count, datetime.now(), datetime.now(), name))
                    else:
                        self.db.cursor.execute('''
                            UPDATE items 
                            SET count = ?, updated_at = ? 
                            WHERE name = ?
                        ''', (new_count, datetime.now(), name))
                
                # Check if item_type was missing and is now provided (important for imported items)
                if existing['item_type'] is None and item_type:
                    self.db.cursor.execute('''
                        UPDATE items 
                        SET item_type = ?, updated_at = ? 
                        WHERE name = ?
                    ''', (item_type, datetime.now(), name))
                        
                self.db.conn.commit()
                return {'success': True, 'action': 'updated', 'count': new_count}
            else:
                # Item is new
                # Set added_to_inventory_at only if count > 0
                added_at = datetime.now() if initial_count > 0 else None
                
                self.db.cursor.execute('''
                    INSERT INTO items 
                    (name, item_type, image_url, image_path, count, notes, properties_json, added_to_inventory_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, item_type, image_url, image_path, initial_count, notes, properties_json, added_at))
                self.db.conn.commit()
                return {'success': True, 'action': 'added', 'count': initial_count}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_item_by_name(self, name):
        """Retrieve one item by name"""
        self.db.cursor.execute('SELECT * FROM items WHERE name = ?', (name,))
        result = self.db.cursor.fetchone()
        return dict(result) if result else None

    def update_item_count(self, name, count):
        """Update the count of an existing item"""
        count = int(count)
        now = datetime.now()
        
        # Holen des aktuellen Counts, um zu prüfen, ob der added_to_inventory_at Zeitstempel aktualisiert werden muss
        existing = self.get_item_by_name(name)
        if not existing:
             return {'success': False, 'error': f"Item '{name}' not found."}
        
        current_count = existing['count']
        added_at = existing['added_to_inventory_at']
        
        if count > 0 and (current_count == 0 or added_at is None):
            # Item wird neu ins Inventar aufgenommen oder hatte keinen Zeitstempel
            added_at = now
        elif count == 0:
            # Item wird auf 0 gesetzt
            added_at = None

        try:
            self.db.cursor.execute('''
                UPDATE items 
                SET count = ?, updated_at = ?, added_to_inventory_at = ? 
                WHERE name = ?
            ''', (count, now, added_at, name))
            self.db.conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def toggle_favorite_status(self, name, status):
        """Toggle the favorite status (0 or 1) of an item."""
        try:
            self.db.cursor.execute('''
                UPDATE items 
                SET is_favorite = ?, updated_at = ? 
                WHERE name = ?
            ''', (status, datetime.now(), name))
            self.db.conn.commit()
            return {'success': True, 'is_favorite': status}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_all_items(self, is_favorite=None, include_zero_count=False):
        """
        Retrieve all items from the database.
        
        Args:
            is_favorite (int, optional): Filter by favorite status (1 or 0).
            include_zero_count (bool): If False, only return items with count > 0 (Inventory View).
        """
        where_clauses = []
        params = []
        
        # 1. Count Filter
        if not include_zero_count:
            where_clauses.append('count > 0')
            
        # 2. Favorite Filter
        if is_favorite is not None:
            where_clauses.append('is_favorite = ?')
            params.append(is_favorite)
            
        where_sql = ' WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''
        
        query = f'SELECT * FROM items {where_sql} ORDER BY name COLLATE NOCASE'
        
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]

    def search_items(self, query, include_zero_count=True):
        """
        Search for items by name. Default behavior is to search ALL items (count >= 0).
        """
        like_query = f'%{query}%'
        where_clauses = ['name LIKE ?']
        params = [like_query]

        if not include_zero_count:
            where_clauses.append('count > 0')
        
        where_sql = ' WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''
        
        sql = f'SELECT * FROM items {where_sql} ORDER BY name COLLATE NOCASE'
        
        self.db.cursor.execute(sql, params)
        return [dict(row) for row in self.db.cursor.fetchall()]
        
    def get_category_stats(self):
        """Get inventory stats by item category (only counts > 0)"""
        self.db.cursor.execute('''
            SELECT item_type, SUM(count) as total_count 
            FROM items 
            WHERE item_type IS NOT NULL AND count > 0
            GROUP BY item_type
        ''')
        stats = {row['item_type']: row['total_count'] for row in self.db.cursor.fetchall()}
        
        # Separate Abfrage für Favoriten (count > 0)
        self.db.cursor.execute('SELECT SUM(count) as total_count FROM items WHERE is_favorite = 1 AND count > 0')
        favorite_count = self.db.cursor.fetchone()['total_count']
        if favorite_count and favorite_count > 0:
            stats['Favorites'] = favorite_count
            
        return stats
        
    def update_item_notes(self, name, notes):
        """Update item notes"""
        try:
            self.db.cursor.execute('''
                UPDATE items 
                SET notes = ?, updated_at = ? 
                WHERE name = ?
            ''', (notes, datetime.now(), name))
            self.db.conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_item(self, name):
        """Delete an item (removes from DB)"""
        try:
            self.db.cursor.execute('DELETE FROM items WHERE name = ?', (name,))
            self.db.conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def clear_inventory(self):
        """Set all item counts to 0 (empty inventory but keep items in database)"""
        try:
            self.db.cursor.execute('UPDATE items SET count = 0, added_to_inventory_at = NULL')
            self.db.conn.commit()
            affected = self.db.cursor.rowcount
            return {'success': True, 'affected': affected}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_all_items(self):
        """Delete ALL items from database"""
        try:
            self.db.cursor.execute('DELETE FROM items')
            self.db.conn.commit()
            affected = self.db.cursor.rowcount
            return {'success': True, 'deleted': affected}
        except Exception as e:
            return {'success': False, 'error': str(e)}