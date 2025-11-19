"""
API Backend for frontend communication
"""
import os
import sys
import json
import tempfile
from urllib.parse import urlparse, parse_qs

# Add src to path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from database.models import Database
from database.operations import ItemOperations
from scraper.cstone import CStoneScraper
from cache.image_cache import ImageCache


class API:
    def __init__(self):
        """Initialize API with database, scraper, and cache"""
        self.db = Database()
        self.operations = ItemOperations(self.db)
        self.scraper = CStoneScraper()
        self.cache = ImageCache()

    def _path_to_url(self, path):
        """
        Converts an absolute cache path (containing category subfolders) 
        to a relative URL path usable by the browser server (starting with /cache/).
        (FIXED for subfolders)
        """
        if not path:
            return None
            
        # 1. Normalisieren des Pfadtrenners für URL
        path = path.replace('\\', '/')
        
        # 2. Den Teil ab 'data/cache/images/' finden und durch '/cache/' ersetzen
        search_string = 'data/cache/images/'
        if search_string in path:
            parts = path.split(search_string)
            if len(parts) > 1:
                return f"/cache/{parts[1]}"
        
        # Fallback 
        return path

    def search_items_local(self, query):
        """
        Search items in local database (for the Search Tab).
        CRITICAL: This must return ALL items (count >= 0) to allow searching for items not yet in inventory.
        """
        # Wir verwenden search_items mit include_zero_count=True (Standard in operations.py)
        if not query:
            items = self.operations.get_all_items(include_zero_count=True)
        else:
            items = self.operations.search_items(query, include_zero_count=True)

        # Daten für Frontend aufbereiten
        for item in items:
            item['is_favorite'] = bool(item.get('is_favorite', 0))
            if item.get('image_path'):
                item['icon_url'] = self._path_to_url(item['image_path'])
            else:
                item['icon_url'] = item.get('image_url')

        return items

    def search_items_cstone(self, query):
        """Search items on CStone.space"""
        if not query or len(query) < 2:
            return []
        return self.scraper.search_item(query)

    def add_item(self, name, item_type=None, image_url=None, notes=None, initial_count=1, properties_json=None):
        """Adds an item to the inventory"""
        
        # 1. Details und Properties scrapen, wenn URL fehlt
        if not image_url:
            print(f"INFO: No image_url provided for {name}, attempting to scrape full details...")
            full_details = self.scraper.get_item_details(name)
            if full_details:
                image_url = full_details.get('image_url')
                # Wenn wir scraped properties haben, nutzen wir diese
                if full_details.get('properties'):
                    properties_json = json.dumps(full_details.get('properties', {}))

        # 2. Bild herunterladen und cachen
        image_path = None
        if image_url:
            image_path = self.cache.download_and_cache(image_url, name)
            
        # 3. In DB speichern
        result = self.operations.add_item(name, item_type, image_url, image_path, notes, initial_count, properties_json)
        
        return result

    def update_item_count(self, name, count):
        """Update the count of an existing item"""
        return self.operations.update_item_count(name, count)
        
    def update_count(self, name, count):
        """Alias for update_item_count (used by some frontend quick actions)"""
        return self.update_item_count(name, count)
        
    def update_item_notes(self, name, notes):
        """Update item notes"""
        return self.operations.update_item_notes(name, notes)

    def delete_item(self, name):
        """Delete an item (removes from DB)"""
        return self.operations.delete_item(name)
    
    def delete_all_items(self):
        """Delete ALL items"""
        return self.operations.delete_all_items()

    def get_item(self, name):
        """Retrieve full details for an item from local DB (used by app.js)"""
        item = self.operations.get_item_by_name(name)
        if item:
            item['is_favorite'] = bool(item.get('is_favorite', 0))
            if item.get('image_path'):
                # URLs für verschiedene Zwecke setzen
                url = self._path_to_url(item['image_path'])
                item['full_image_url'] = url
                item['icon_url'] = url
                item['thumb_url'] = url
            else:
                url = item.get('image_url')
                item['full_image_url'] = url
                item['icon_url'] = url
                item['thumb_url'] = url
        return item
        
    def get_categories(self):
        """Retrieve all distinct item types for filters"""
        stats = self.get_category_stats()
        # 'Favorites' aus der Liste der normalen Kategorien filtern
        types = [t for t in stats.get('category_counts', {}).keys() if t != 'Favorites']
        return sorted(types)

    def get_category_stats(self):
        """Get inventory stats by item category"""
        stats = self.operations.get_category_stats()
        return {'category_counts': stats}
        
    def get_stats(self):
        """Get general stats"""
        # include_zero_count=True um alle Items in DB zu zählen
        all_items_db = self.operations.get_all_items(include_zero_count=True)
        all_items_inventory = self.operations.get_all_items(include_zero_count=False)
        
        total_count = sum(item['count'] for item in all_items_inventory)
        unique_items = len(all_items_inventory)
        total_db = len(all_items_db)
        
        # Cache size berechnen
        cache_size = 0
        cache_dir = os.path.join('data', 'cache', 'images')
        if os.path.exists(cache_dir):
            for root, _, files in os.walk(cache_dir):
                for f in files:
                    cache_size += os.path.getsize(os.path.join(root, f))
        
        return {
            'total_items_in_db': total_db,
            'inventory_unique_items': unique_items,
            'total_item_count': total_count,
            'cache_size_mb': round(cache_size / (1024 * 1024), 2),
            'category_counts': self.operations.get_category_stats()
        }

    def clear_inventory(self):
        """
        Set all item counts to 0 (empty inventory but keep items in database).
        """
        return self.operations.clear_inventory()

    def clear_cache(self):
        """Clear the image cache"""
        return self.cache.clear_cache()

    # =========================================================
    # HAUPTFUNKTIONEN FÜR INVENTAR & FAVORITEN
    # =========================================================

    def inventory(self, sort_by='name', sort_order='asc', query='', category=None, is_favorite=None):
        """
        Retrieves the filtered and sorted inventory list.
        Handler für /api/get_inventory_items
        CRITICAL: This must only show items with count > 0.
        """
        
        # 1. Daten aus DB holen (wir verwenden IMMER include_zero_count=False für Inventar-Ansichten)
        filter_favorite = 1 if str(is_favorite).lower() in ('1', 'true') else None
        
        if query:
            # Suche INNERHALB des Inventars (Count > 0)
            items = self.operations.search_items(query, include_zero_count=False)
        else:
            # Normale Listenansicht (Count > 0, optional Favorite Filter)
            items = self.operations.get_all_items(is_favorite=filter_favorite, include_zero_count=False)

        # 2. Kategorie-Filter anwenden (wenn nicht Favorites, da das schon oben passiert ist)
        if category and category != 'Favorites' and category != '':
             items = [item for item in items if item.get('item_type') == category]

        # 3. Daten aufbereiten (URLs & is_favorite Boolean)
        processed_items = []
        for item in items:
            # Das manuelle Count-Filter ist jetzt überflüssig, da die DB-Abfrage dies übernimmt!
            
            # Konvertiere für JSON
            item_dict = dict(item)
            item_dict['is_favorite'] = bool(item_dict.get('is_favorite', 0))
            
            if item_dict.get('image_path'):
                item_dict['thumb_url'] = self._path_to_url(item_dict['image_path'])
                item_dict['icon_url'] = item_dict['thumb_url']
            else:
                item_dict['thumb_url'] = item_dict.get('image_url')
                item_dict['icon_url'] = item_dict.get('image_url')
                
            processed_items.append(item_dict)

        # 4. Sortierung (Python-seitig, da wir hier flexibler sind)
        reverse_sort = (sort_order.lower() == 'desc')
        
        def sort_key(x):
            key = sort_by
            # FIX: Mapping von 'date' auf die korrekte DB-Spalte
            if key == 'date':
                key = 'added_to_inventory_at'
            
            val = x.get(key)
            if val is None:
                # Leere Werte (z.B. wenn added_to_inventory_at noch NULL ist) am Ende sortieren
                return ''
            if isinstance(val, str):
                return val.lower()
            return val

        try:
            processed_items.sort(key=sort_key, reverse=reverse_sort)
        except Exception:
            # Fallback auf Name, falls Sortierung fehlschlägt
            processed_items.sort(key=lambda x: x.get('name', '').lower(), reverse=reverse_sort)
            
        return processed_items

    def toggle_favorite(self, name, is_favorite):
        """
        Toggles the favorite status of an item.
        """
        try:
            # Sicherstellen, dass wir einen Integer (0 oder 1) haben
            if isinstance(is_favorite, str):
                status_val = 1 if is_favorite.lower() in ('1', 'true', 'yes') else 0
            else:
                status_val = 1 if is_favorite else 0
                
            return self.operations.toggle_favorite_status(name, status_val)
        except Exception as e:
            return {'success': False, 'error': str(e)}