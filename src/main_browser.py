"""
GearCrate - Browser Mode Server (FIXED)
- Static image serving with caching
- Query parameter support for sorting/filtering
- Favorites support
"""
import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from api.backend import API


class GearCrateAPIHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler with API Support & Static Image Serving"""
    api = None
    cache_dir = None
    
    def __init__(self, *args, **kwargs):
        # Set the web directory as base
        web_dir = os.path.join(project_root, 'web')
        os.chdir(web_dir)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        
        # Parse URL and query parameters
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Handle STATIC IMAGE FILES from cache - CRITICAL!
        if path.startswith('/cache/'):
            try:
                cache_rel_path = path[7:]  # Remove '/cache/' prefix
                cache_rel_path = cache_rel_path.replace('/', os.sep)
                image_path = os.path.join(GearCrateAPIHandler.cache_dir, cache_rel_path)
                
                # Security check
                image_path = os.path.abspath(image_path)
                cache_dir_abs = os.path.abspath(GearCrateAPIHandler.cache_dir)
                if not image_path.startswith(cache_dir_abs):
                    self.send_error(403, "Access denied")
                    return
                
                if not os.path.exists(image_path):
                    self.send_error(404, f"Image not found: {cache_rel_path}")
                    return
                
                # Determine content type
                ext = os.path.splitext(image_path)[1].lower()
                content_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.webp': 'image/webp',
                    '.gif': 'image/gif'
                }
                content_type = content_types.get(ext, 'image/png')
                
                # Read and send file
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Content-Length', len(image_data))
                self.send_header('Cache-Control', 'public, max-age=31536000')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(image_data)
                return
            
            except Exception as e:
                print(f"❌ Error serving image: {e}")
                self.send_error(500, str(e))
                return
        
        # Handle inventory API with query parameters
        if path == '/api/get_inventory_items':
            try:
                # Extract query parameters
                sort_by = query_params.get('sort_by', ['name'])[0]
                sort_order = query_params.get('sort_order', ['asc'])[0]
                
                # Check for 'category' (new) OR 'category_filter' (old)
                category = query_params.get('category', [None])[0]
                if not category:
                    category = query_params.get('category_filter', [None])[0]
                
                # NEU: is_favorite Parameter auslesen
                is_favorite = query_params.get('is_favorite', [None])[0]
                
                # Rufe die inventory-Funktion im Backend auf
                # Wir prüfen, ob die Methode 'inventory' existiert (neues Backend) oder 'get_inventory_items' (altes Backend)
                if hasattr(GearCrateAPIHandler.api, 'inventory'):
                    result = GearCrateAPIHandler.api.inventory(
                        sort_by=sort_by,
                        sort_order=sort_order,
                        category=category,
                        is_favorite=is_favorite
                    )
                else:
                    # Fallback für Kompatibilität
                    print("⚠️ Warning: Using legacy backend method 'get_inventory_items'")
                    result = GearCrateAPIHandler.api.get_inventory_items(
                        sort_by=sort_by,
                        sort_order=sort_order,
                        category_filter=category
                    )
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            
            except Exception as e:
                print(f"❌ Error getting inventory: {e}")
                import traceback
                traceback.print_exc()
                self.send_error(500, str(e))
                return
        
        # NEU: Search Items Local (für Fuse.js Initialisierung)
        if path == '/api/search_items_local':
            try:
                query = query_params.get('query', [''])[0]
                result = GearCrateAPIHandler.api.search_items_local(query)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            
            except Exception as e:
                print(f"❌ Error searching items: {e}")
                import traceback
                traceback.print_exc()
                self.send_error(500, str(e))
                return
        
        # GEAR SETS API
        if path == '/api/get_all_gear_sets':
            try:
                result = GearCrateAPIHandler.api.get_all_gear_sets()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            except Exception as e:
                self.send_error(500, str(e))
                return
        
        if path == '/api/get_gear_set_details':
            try:
                set_name = query_params.get('set_name', [''])[0]
                variant = query_params.get('variant', [''])[0]
                
                result = GearCrateAPIHandler.api.get_gear_set_details(set_name, variant)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            except Exception as e:
                self.send_error(500, str(e))
                return
        
        if path == '/api/get_gear_set_variants':
            try:
                set_name = query_params.get('set_name', [''])[0]
                
                result = GearCrateAPIHandler.api.get_gear_set_variants(set_name)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            except Exception as e:
                self.send_error(500, str(e))
                return
        
        # Handle bulk-import API
        if path.startswith('/api/bulk-import/'):
            try:
                category_url = path.split('/api/bulk-import/')[1]
                result = GearCrateAPIHandler.api.get_category_items(category_url)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            
            except Exception as e:
                self.send_error(500, str(e))
                return
        
        # Default file serving
        super().do_GET()
    
    def do_POST(self):
        """Handle API POST requests"""
        if self.path.startswith('/api/'):
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                data = json.loads(post_data.decode('utf-8'))
                method = self.path.split('/api/')[1]
                
                # Call API method
                if hasattr(GearCrateAPIHandler.api, method):
                    result = getattr(GearCrateAPIHandler.api, method)(**data)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                else:
                    print(f"❌ API method not found: {method}")
                    self.send_error(404, f"API method {method} not found")
            
            except Exception as e:
                print(f"❌ API POST Error: {e}")
                import traceback
                traceback.print_exc()
                self.send_error(500, str(e))
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


def start_server():
    """Start the HTTP server"""
    port = 8080
    server_address = ('', port)
    
    # Initialize API
    GearCrateAPIHandler.api = API()
    
    # Set cache directory to images subfolder
    GearCrateAPIHandler.cache_dir = os.path.join(project_root, 'data', 'cache', 'images')
    
    httpd = HTTPServer(server_address, GearCrateAPIHandler)
    
    print("=" * 60)
    print("📦 GearCrate - Star Citizen Inventory Manager")
    print("=" * 60)
    print(f"✅ Server running on http://localhost:{port}")
    print(f"✅ Static image serving enabled")
    print(f"✅ Cache directory: {GearCrateAPIHandler.cache_dir}")
    print("=" * 60)
    print("📂 Opening browser...")
    
    # Open browser
    webbrowser.open(f'http://localhost:{port}/index.html')
    
    print("\n⌨️  Press Ctrl+C to stop server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopping...")
        try:
            if hasattr(GearCrateAPIHandler.api, 'close'):
                GearCrateAPIHandler.api.close()
        except:
            pass
        httpd.shutdown()
        print("✅ GearCrate stopped!")


if __name__ == '__main__':
    start_server()