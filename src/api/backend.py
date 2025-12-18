"""
API Backend for frontend communication
"""
import os
import sys
import json
import sqlite3
import tempfile
import requests
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
from cache.gear_sets import GearSetsManager
from utils.logger import setup_logger
from utils.exceptions import DatabaseError, ConfigError, CacheError, ScraperError

# Setup logger
logger = setup_logger(__name__)
#

class API:
    # Class-level variable to store webview window reference
    _webview_window = None

    def __init__(self):
        """Initialize API with database, scraper, and cache"""
        self.db = Database()
        self.operations = ItemOperations(self.db)
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'user_config.json')
        self.scraper = CStoneScraper()
        self.cache = ImageCache()
        self.gear_sets = GearSetsManager()
        self.current_scan_mode = 1  # Default to 1x1
        self.current_scan_resolution = "1920x1080" # Default resolution

    @classmethod
    def set_webview_window(cls, window):
        """Store reference to webview window for DevTools access"""
        cls._webview_window = window
        logger.info("Webview window reference stored", extra={'emoji': '✅'})

    def open_devtools(self):
        """Open DevTools in the webview window (can be called as instance or class method)"""
        # Use class variable to access window
        if API._webview_window is None:
            logger.warning("No webview window reference available", extra={'emoji': '⚠️'})
            return {'success': False, 'error': 'No webview window available'}

        try:
            # Use pywebview's evaluate_js to trigger DevTools via JavaScript
            # This executes JavaScript in the context of the webview window
            API._webview_window.evaluate_js('''
                // Try to open DevTools using Chrome DevTools Protocol
                if (window.chrome && window.chrome.webview) {
                    window.chrome.webview.hostObjects.sync.open_devtools();
                }
            ''')
            logger.info("DevTools opened via JS", extra={'emoji': '✅'})
            return {'success': True}
        except (AttributeError, RuntimeError) as e:
            # Fallback: Try F12 keypress
            try:
                import pyautogui
                import time
                # Focus the window first
                API._webview_window.on_top = True
                time.sleep(0.1)
                pyautogui.press('f12')
                API._webview_window.on_top = False
                logger.info("DevTools opened (F12 pressed)", extra={'emoji': '✅'})
                return {'success': True}
            except (ImportError, AttributeError, RuntimeError) as e2:
                logger.warning(f"Could not open DevTools: {e}, {e2}", extra={'emoji': '⚠️'})
                return {'success': False, 'error': str(e)}

    def set_scan_resolution(self, resolution):
        """
        Sets the scan resolution for InvDetect scanner
        resolution: '1920x1080', '2560x1440', etc.
        """
        try:
            # Basic validation
            if 'x' not in resolution:
                return {'success': False, 'error': f'Invalid resolution format: {resolution}'}
            
            self.current_scan_resolution = resolution
            logger.info(f"Scan resolution set to: {resolution}", extra={'emoji': '✅'})
            return {'success': True, 'resolution': resolution}
        except (AttributeError, ValueError) as e:
            logger.error(f"Error setting scan resolution: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}


    def _path_to_url(self, path):
        """
        Converts an absolute cache path (containing category subfolders)
        to a relative URL path usable by the browser server (starting with /images/).
        Returns None if the file doesn't exist (so frontend can show placeholder).
        """
        if not path:
            return None

        # 1. Normalisieren des Pfadtrenners für URL
        normalized_path = path.replace('\\', '/')

        # 2. Bestimme den absoluten Dateipfad für Existenzprüfung
        absolute_path = None
        if os.path.isabs(path):
            # Ist bereits ein absoluter Pfad
            absolute_path = path
        else:
            # Relativer Pfad - versuche ihn zu konstruieren
            # Annahme: Relativer Pfad ist relativ zum Projektroot
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            absolute_path = os.path.join(project_root, path)

        # 3. Prüfe ob Datei existiert
        if absolute_path and not os.path.exists(absolute_path):
            # Datei existiert nicht -> None zurückgeben für Placeholder
            return None

        # 4. Versuche verschiedene Muster zu finden und zu ersetzen
        # Pattern 1: data/cache/images/ -> /cache/
        if 'data/cache/images/' in normalized_path:
            parts = normalized_path.split('data/cache/images/')
            if len(parts) > 1:
                return f"/cache/{parts[1]}"

        # Pattern 2: data/images/ -> /images/
        if 'data/images/' in normalized_path:
            parts = normalized_path.split('data/images/')
            if len(parts) > 1:
                return f"/images/{parts[1]}"

        # Pattern 3: Wenn es ein absoluter Pfad ist, extrahiere alles nach 'data/'
        if '/data/' in normalized_path or 'data/' in normalized_path:
            # Finde den Index von 'data/' und nimm alles danach
            data_index = normalized_path.find('data/')
            if data_index != -1:
                relative_part = normalized_path[data_index + 5:]  # Skip 'data/'
                return f"/images/{relative_part}"

        # Fallback: Wenn der Pfad mit /images/ oder /cache/ beginnt, behalte ihn
        if normalized_path.startswith('/images/') or normalized_path.startswith('/cache/'):
            return normalized_path

        # Letzter Fallback
        return normalized_path

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
            logger.info(f"No image_url provided for {name}, attempting to scrape full details...", extra={'emoji': 'ℹ️'})
            full_details = self.scraper.get_item_details(name)
            if full_details:
                image_url = full_details.get('image_url')
                # Wenn wir scraped properties haben, nutzen wir diese
                if full_details.get('properties'):
                    properties_json = json.dumps(full_details.get('properties', {}))

        # 2. Bild herunterladen und cachen
        image_path = None
        if image_url:
            # Check if already cached
            cached_path = self.cache.get_cached_path(image_url, item_type)
            if cached_path:
                image_path = cached_path
            else:
                # Download image to temporary file first
                import tempfile
                import requests
                import os as os_lib
                try:
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                            tmp_file.write(response.content)
                            tmp_path = tmp_file.name

                        # Save to cache (this also generates thumbnails)
                        image_path = self.cache.save_image(image_url, tmp_path, item_type)

                        # Clean up temp file
                        try:
                            os_lib.remove(tmp_path)
                        except (OSError, PermissionError):
                            pass  # Temp file cleanup is not critical
                except requests.RequestException as e:
                    logger.error(f"Network error downloading image for {name}: {e}", extra={'emoji': '❌'})
                except (IOError, OSError) as e:
                    logger.error(f"File error saving image for {name}: {e}", extra={'emoji': '❌'})

        # 3. In DB speichern (ohne properties_json wenn die Spalte nicht existiert)
        try:
            result = self.operations.add_item(name, item_type, image_url, image_path, notes, initial_count, properties_json)
        except sqlite3.OperationalError as e:
            # Falls properties_json Spalte nicht existiert, versuche ohne
            if 'properties_json' in str(e):
                logger.warning(f"properties_json column not found, retrying without it", extra={'emoji': '⚠️'})
                result = self.operations.add_item(name, item_type, image_url, image_path, notes, initial_count)
            else:
                logger.error(f"Database operation error: {e}", extra={'emoji': '❌'})
                raise DatabaseError(f"Failed to add item: {e}") from e
        except sqlite3.IntegrityError as e:
            logger.error(f"Item '{name}' already exists", extra={'emoji': '❌'})
            raise DatabaseError(f"Item already exists: {name}") from e

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
        except (TypeError, KeyError, AttributeError):
            # Fallback auf Name, falls Sortierung fehlschlägt
            logger.warning(f"Sort failed on column '{sort_by}', falling back to name sort", extra={'emoji': '⚠️'})
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
        except sqlite3.Error as e:
            logger.error(f"Database error toggling favorite for '{name}': {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    # =========================================================
    # GEAR SETS FUNKTIONEN
    # =========================================================

    def get_all_gear_sets(self):
        """
        Gibt eine Liste aller verfügbaren Gear Sets zurück.
        Jedes Set enthält: Name, Anzahl Varianten, Beispiel-Varianten
        """
        try:
            summary = self.gear_sets.get_all_sets_summary(self.db.conn)
            return {'success': True, 'sets': summary}
        except sqlite3.Error as e:
            logger.error(f"Database error getting gear sets: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def get_gear_set_details(self, set_name, variant=''):
        """
        Gibt Details zu einem spezifischen Set zurück.
        Enthält alle 4 Teile mit Bildern und Inventar-Status.
        """
        try:
            pieces = self.gear_sets.get_set_pieces(self.db.conn, set_name, variant)
            
            if not pieces:
                return {'success': False, 'error': 'Set nicht gefunden'}
            
            # Bereite Daten für Frontend auf
            result = {
                'set_name': set_name,
                'variant': variant if variant else 'Base',
                'pieces': {}
            }
            
            # Zähle wie viele Teile vorhanden sind
            owned_count = 0
            
            for part_type, piece in pieces.items():
                if piece:
                    # Teil existiert in DB
                    piece_data = {
                        'exists': True,
                        'name': piece['name'],
                        'count': piece.get('count', 0),
                        'owned': piece.get('count', 0) > 0,
                        'image_url': None,
                        'item_type': piece.get('item_type', part_type)  # Include item_type for placeholder
                    }

                    # Bild-URL hinzufügen
                    if piece.get('image_path'):
                        piece_data['image_url'] = self._path_to_url(piece['image_path'])
                    elif piece.get('image_url'):
                        piece_data['image_url'] = piece['image_url']

                    if piece_data['owned']:
                        owned_count += 1

                    result['pieces'][part_type] = piece_data
                else:
                    # Teil nicht in DB gefunden
                    result['pieces'][part_type] = {
                        'exists': False,
                        'name': None,
                        'count': 0,
                        'owned': False,
                        'image_url': None,
                        'item_type': part_type  # Include item_type for placeholder
                    }
            
            result['owned_count'] = owned_count
            result['total_count'] = 4
            result['completion'] = f"{owned_count}/4"

            return {'success': True, 'set': result}

        except sqlite3.Error as e:
            logger.error(f"Database error getting gear set details for '{set_name}': {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def get_gear_set_variants(self, set_name):
        """
        Gibt alle Farbvarianten eines Sets zurück.
        """
        try:
            variants = self.gear_sets.get_set_variants(self.db.conn, set_name)
            return {'success': True, 'variants': variants}
        except sqlite3.Error as e:
            logger.error(f"Database error getting gear set variants for '{set_name}': {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    # =========================================================
    # BULK IMPORT FUNKTIONEN
    # =========================================================

    def get_category_items(self, category_url):
        """
        Holt alle Items einer Kategorie von CStone.space
        category_url: z.B. 'FPSArmors?type=Torsos' oder 'FPSClothes?type=Hat'
        Returns: List of items with name and image_url
        """
        try:
            items = self.scraper.get_category_items(category_url)
            return items
        except requests.RequestException as e:
            logger.error(f"Network error in get_category_items: {e}", extra={'emoji': '❌'})
            raise ScraperError(f"Failed to fetch category items: {e}") from e
        except (ValueError, KeyError) as e:
            logger.error(f"Parse error in get_category_items: {e}", extra={'emoji': '❌'})
            raise ScraperError(f"Failed to parse category items: {e}") from e

    # =========================================================
    # SCANNER FUNKTIONEN (InvDetect Integration)
    # =========================================================

    def set_scan_mode(self, mode):
        """
        Sets the scan mode for InvDetect scanner
        mode: '1x1' or '1x2'
        """
        try:
            # Convert mode to integer for main.py
            if mode == '1x1':
                self.current_scan_mode = 1
            elif mode == '1x2':
                self.current_scan_mode = 2
            else:
                return {'success': False, 'error': f'Invalid scan mode: {mode}'}

            logger.info(f"Scan mode set to: {mode} (mode {self.current_scan_mode})", extra={'emoji': '✅'})
            return {'success': True, 'mode': mode}
        except (AttributeError, ValueError) as e:
            logger.error(f"Error setting scan mode: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def start_scanner(self):
        """
        Starts the InvDetect scanner in a subprocess
        """
        try:
            import subprocess
            import sys

            # Path to InvDetect scanner
            invdetect_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'InvDetect')
            scanner_script = os.path.join(invdetect_path, 'main.py')

            if not os.path.exists(scanner_script):
                return {'success': False, 'error': 'Scanner script not found'}

            # Clear previous scan results before starting new scan
            detected_items_file = os.path.join(invdetect_path, 'detected_items.txt')
            not_detected_file = os.path.join(invdetect_path, 'not_detected.md')

            # Clear detected_items.txt
            try:
                with open(detected_items_file, 'w', encoding='utf-8') as f:
                    f.write('# Detected Items\n# Format: count, item_name\n\n')
                logger.info('Cleared detected_items.txt', extra={'emoji': '✅'})
            except (IOError, OSError, PermissionError) as e:
                logger.warning(f'Could not clear detected_items.txt: {e}', extra={'emoji': '⚠️'})

            # Clear not_detected.md
            try:
                with open(not_detected_file, 'w', encoding='utf-8') as f:
                    f.write('# Not Detected Items\n# Format: Item Name - Page X, Row Y, Col Z\n\n')
                logger.info('Cleared not_detected.md', extra={'emoji': '✅'})
            except (IOError, OSError, PermissionError) as e:
                logger.warning(f'Could not clear not_detected.md: {e}', extra={'emoji': '⚠️'})

            # Get current scan mode (default to 1 if not set)
            scan_mode = getattr(self, 'current_scan_mode', 1)
            scan_resolution = getattr(self, 'current_scan_resolution', "1920x1080")

            # Start scanner in new console window with scan mode and resolution as arguments
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Run scanner with scan mode as command line argument
            subprocess.Popen(
                [sys.executable, scanner_script, str(scan_mode), scan_resolution],
                cwd=invdetect_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            logger.info(f"Scanner started in new console with mode {scan_mode} and resolution {scan_resolution}", extra={'emoji': '✅'})
            return {'success': True}
        except FileNotFoundError as e:
            logger.error(f"Scanner script not found: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': f'Scanner script not found: {e}'}
        except (OSError, PermissionError) as e:
            logger.error(f"Error starting scanner process: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def get_scan_results(self):
        """
        Reads scan results from InvDetect output file
        Returns: {found: [...], not_found: [...]}
        """
        try:
            # Path to InvDetect files
            invdetect_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'InvDetect')

            output_file = os.path.join(invdetect_path, 'detected_items.txt')
            not_detected_file = os.path.join(invdetect_path, 'not_detected.md')

            found_items = []
            not_found_items = []

            # Read found items (format: count, item_name)
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments
                        if line and not line.startswith('#'):
                            # Format: count, item_name
                            if ',' in line:
                                parts = line.split(',', 1)
                                try:
                                    count = int(parts[0].strip())
                                    name = parts[1].strip()

                                    # Look up item in database to get full details
                                    item_details = self.operations.get_item_by_name(name)

                                    if item_details:
                                        # Item exists in database - use its details
                                        item_type = item_details.get('item_type', 'Unknown')

                                        # Use same logic as search_items_local (line 128-131)
                                        if item_details.get('image_path'):
                                            # Item has local image cached
                                            image_url = self._path_to_url(item_details['image_path'])
                                            logger.debug(f"Item: {name}, Type: {item_type}, Using cached image: {image_url}", extra={'emoji': '🔍'})
                                        else:
                                            # No local image, use placeholder based on item_type
                                            image_url = f'/images/Placeholder/{item_type}.png'
                                            logger.debug(f"Item: {name}, Type: {item_type}, Using placeholder: {image_url}", extra={'emoji': '🔍'})

                                        found_items.append({
                                            'name': name,
                                            'count': count,
                                            'scanned_name': name,  # Same as name since it matched
                                            'image_url': image_url,
                                            'item_type': item_type
                                        })
                                    else:
                                        # Item not in database - still add with minimal info
                                        found_items.append({
                                            'name': name,
                                            'count': count,
                                            'scanned_name': name,
                                            'image_url': '/images/Placeholder/Unknown.png',
                                            'item_type': 'Unknown'
                                        })
                                except (ValueError, IndexError):
                                    pass

            # Read not found items (format: Item Name - Page X, Row Y, Col Z)
            if os.path.exists(not_detected_file):
                with open(not_detected_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and headers
                        if line and not line.startswith('#') and not line.startswith('---'):
                            # Extract item name (before " - Page")
                            if ' - Page' in line:
                                item_name = line.split(' - Page')[0].strip()
                            else:
                                item_name = line

                            if item_name:
                                not_found_items.append({'ocr_text': item_name, 'count': 1})

            return {
                'success': True,
                'found': found_items,
                'not_found': not_found_items
            }
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"File access error reading scan results: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}
        except sqlite3.Error as e:
            logger.error(f"Database error reading scan results: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def import_scanned_items(self, items):
        """
        Imports scanned items into inventory
        items: [{'name': str, 'count': int}, ...]
        """
        try:
            results = []

            for item_data in items:
                name = item_data.get('name')
                count = item_data.get('count', 1)

                if not name:
                    results.append({'success': False, 'name': '', 'error': 'No name provided'})
                    continue

                # Clean up name: strip whitespace and normalize multiple spaces
                name = ' '.join(name.strip().split())

                try:
                    # Try to get item from database
                    existing_item = self.operations.get_item_by_name(name)

                    if existing_item:
                        # Update count
                        new_count = existing_item.get('count', 0) + count
                        self.operations.update_item_count(name, new_count)
                        results.append({'success': True, 'name': name, 'action': 'updated', 'count': new_count})
                    else:
                        # Item not in DB - try to scrape details
                        details = self.scraper.get_item_details(name)

                        if details:
                            # Add item with scraped details
                            self.add_item(
                                name=name,
                                item_type=details.get('item_type'),
                                image_url=details.get('image_url'),
                                notes='Imported from InvDetect scan',
                                initial_count=count
                            )
                            results.append({'success': True, 'name': name, 'action': 'added', 'count': count})
                        else:
                            # Add item without details
                            self.operations.add_item(
                                name=name,
                                item_type='Unknown',
                                image_url=None,
                                image_path=None,
                                notes='Imported from InvDetect scan (no details found)',
                                initial_count=count
                            )
                            results.append({'success': True, 'name': name, 'action': 'added', 'count': count, 'warning': 'No details found'})

                except sqlite3.Error as item_error:
                    logger.error(f"Database error importing item '{name}': {item_error}", extra={'emoji': '❌'})
                    results.append({'success': False, 'name': name, 'error': str(item_error)})
                except requests.RequestException as item_error:
                    logger.error(f"Network error scraping details for '{name}': {item_error}", extra={'emoji': '❌'})
                    results.append({'success': False, 'name': name, 'error': str(item_error)})

            return {'success': True, 'results': results}
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid data in import_scanned_items: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    # =========================================================
    # USER CONFIG (Language persistence)
    # =========================================================

    def get_user_language(self):
        """
        Get saved user language from config file
        Returns: {'language': 'en'} or {'language': None} if not set
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return {'success': True, 'language': config.get('language')}
            return {'success': True, 'language': None}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': f"Invalid config file format: {e}"}
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"File access error reading user config: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def set_user_language(self, language):
        """
        Save user language to config file
        language: 'de', 'en', 'fr', or 'es'
        """
        try:
            # Load existing config or create new
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # Update language
            config['language'] = language

            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            # Save config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            logger.info(f"User language saved: {language}", extra={'emoji': '✅'})
            return {'success': True, 'language': language}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in existing config file: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': f"Invalid config file format: {e}"}
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"File access error saving user config: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def _load_config(self):
        """Helper to load config safely."""
        config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except json.JSONDecodeError as e:
                logger.warning(f"Error decoding JSON in config file: {self.config_file}. Starting with empty config. Error: {e}", extra={'emoji': '⚠️'})
        return config

    def _save_config(self, config):
        """Helper to save config safely."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    def get_window_geometry(self):
        """
        Get saved window geometry from config file
        Returns: {'width': int, 'height': int, 'x': int, 'y': int, 'maximized': bool}
        """
        try:
            config = self._load_config()
            window = config.get('window', {})
            return {
                'success': True,
                'width': window.get('width'),
                'height': window.get('height'),
                'x': window.get('x'),
                'y': window.get('y'),
                'maximized': window.get('maximized', False)
            }
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"File access error reading window geometry: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def save_window_geometry(self, geometry_data):
        """
        Save window geometry to config file
        geometry_data: dict with keys 'width', 'height', 'x', 'y', 'maximized'
        """
        try:
            config = self._load_config()

            if 'window' not in config:
                config['window'] = {}

            # Only update values that were passed (not None)
            config['window'].update({k: v for k, v in geometry_data.items() if v is not None})

            # Ensure 'maximized' is present
            if 'maximized' not in config['window']:
                config['window']['maximized'] = False

            self._save_config(config)

            logger.info(f"Window geometry saved: {geometry_data}", extra={'emoji': '✅'})
            return {'success': True}
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"File access error saving window geometry: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def set_window_geometry(self, width=None, height=None, x=None, y=None, maximized=False):
        """
        Save window geometry to config file (backward compatibility)
        Calls save_window_geometry internally
        """
        geometry_data = {
            'width': width,
            'height': height,
            'x': x,
            'y': y,
            'maximized': maximized
        }
        return self.save_window_geometry(geometry_data)

    # =========================================================
    # CACHE MANAGEMENT FUNKTIONEN
    # =========================================================

    def get_cache_stats(self):
        """
        Get cache statistics (size, file count)
        Returns: {'size_bytes': int, 'size_mb': float, 'file_count': int}
        """
        try:
            stats = self.cache.get_cache_stats()
            return {'success': True, 'stats': stats}
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Error getting cache stats: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def cleanup_cache_orphaned(self):
        """
        Remove orphaned images (not referenced in database)
        Returns: {'removed_count': int, 'freed_mb': float, 'errors': list}
        """
        try:
            result = self.cache.cleanup_orphaned_images(self.db.conn)
            logger.info(f"Cleaned up {result['removed_count']} orphaned images, freed {result['freed_mb']} MB", extra={'emoji': '✅'})
            return {'success': True, 'result': result}
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Error cleaning up orphaned images: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}
        except sqlite3.Error as e:
            logger.error(f"Database error during orphaned cleanup: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def cleanup_cache_old(self, max_age_days=30):
        """
        Remove images older than max_age_days
        max_age_days: Maximum age in days (default: 30)
        Returns: {'removed_count': int, 'freed_mb': float, 'errors': list}
        """
        try:
            result = self.cache.cleanup_old_images(max_age_days)
            logger.info(f"Cleaned up {result['removed_count']} old images (>{max_age_days} days), freed {result['freed_mb']} MB", extra={'emoji': '✅'})
            return {'success': True, 'result': result}
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Error cleaning up old images: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}

    def cleanup_cache_by_size(self, max_size_mb=1000):
        """
        Remove least recently used images until cache is under max_size_mb
        max_size_mb: Maximum cache size in MB (default: 1000)
        Returns: {'removed_count': int, 'freed_mb': float, 'errors': list}
        """
        try:
            result = self.cache.cleanup_by_size(max_size_mb)
            logger.info(f"Cleaned up cache to max {max_size_mb} MB: removed {result['removed_count']} images, freed {result['freed_mb']} MB", extra={'emoji': '✅'})
            return {'success': True, 'result': result}
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Error cleaning up cache by size: {e}", extra={'emoji': '❌'})
            return {'success': False, 'error': str(e)}