"""
GearCrate - Desktop Mode (pywebview + HTTP Server)
- HTTP server running in background thread
- pywebview window for desktop experience
- Ready for hotkey integration
"""
import os
import sys
import threading
import time
from http.server import HTTPServer

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from main_browser import GearCrateAPIHandler
from api.backend import API
import webview


class DesktopServer:
    """Desktop server with pywebview"""

    def __init__(self, port=8080):
        self.port = port
        self.httpd = None
        self.server_thread = None
        self.api = None
        self.window = None
        self.devtools_open = False
        
    def start_http_server(self):
        """Start HTTP server in background thread"""
        print("🔧 Starting HTTP server...")
        
        # Initialize API
        self.api = API()
        GearCrateAPIHandler.api = self.api
        
        # Set cache directory
        GearCrateAPIHandler.cache_dir = os.path.join(project_root, 'data', 'images')
        
        # Change to web directory
        web_dir = os.path.join(project_root, 'web')
        os.chdir(web_dir)
        
        # Create server
        server_address = ('', self.port)
        self.httpd = HTTPServer(server_address, GearCrateAPIHandler)
        
        # Start in background thread
        self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()
        
        print(f"✅ HTTP Server running on http://localhost:{self.port}")
        
        # Wait a bit to ensure server is ready
        time.sleep(0.5)
    
    def on_loaded(self):
        """Called when window finishes loading - restore window size and hide DevTools"""
        def restore_window_size_and_close_devtools():
            time.sleep(0.5)  # Wait for window to be ready

            # Restore window size from localStorage
            try:
                js_code = """
                (function() {
                    const savedWidth = localStorage.getItem('windowWidth');
                    const savedHeight = localStorage.getItem('windowHeight');
                    const savedX = localStorage.getItem('windowX');
                    const savedY = localStorage.getItem('windowY');
                    const isMaximized = localStorage.getItem('windowMaximized') === 'true';

                    return {
                        width: savedWidth ? parseInt(savedWidth) : null,
                        height: savedHeight ? parseInt(savedHeight) : null,
                        x: savedX ? parseInt(savedX) : null,
                        y: savedY ? parseInt(savedY) : null,
                        maximized: isMaximized
                    };
                })();
                """
                result = self.window.evaluate_js(js_code)

                if result and result.get('maximized'):
                    # Window was maximized - maximize it
                    # pywebview doesn't have a direct maximize method, so we set it to screen size
                    try:
                        # Execute JavaScript to get screen dimensions
                        screen_info = self.window.evaluate_js("""
                        (function() {
                            return {
                                width: screen.availWidth,
                                height: screen.availHeight
                            };
                        })();
                        """)
                        if screen_info:
                            self.window.resize(screen_info['width'], screen_info['height'])
                            self.window.move(0, 0)
                            print(f"✅ Window maximized to {screen_info['width']}x{screen_info['height']}")
                    except Exception as e:
                        print(f"Could not maximize window: {e}")
                elif result and result.get('width') and result.get('height'):
                    # Resize window to saved size
                    self.window.resize(result['width'], result['height'])
                    print(f"✅ Window size restored: {result['width']}x{result['height']}")

                    # Move window if position was saved
                    if result.get('x') is not None and result.get('y') is not None:
                        self.window.move(result['x'], result['y'])
                        print(f"✅ Window position restored: ({result['x']}, {result['y']})")
            except Exception as e:
                print(f"Could not restore window size: {e}")

            # Close DevTools if they opened automatically
            # This allows F12 and Debug button to work later
            try:
                import pyautogui
                time.sleep(0.3)  # Wait a bit more for DevTools to open
                pyautogui.press('f12')  # Close DevTools
                print("✅ DevTools geschlossen (können mit F12 oder 🐛 Debug geöffnet werden)")
            except Exception as e:
                print(f"⚠️ Could not close DevTools automatically: {e}")

            print("📌 DevTools verfügbar - drücke F12 oder klicke 🐛 Debug")

        # Run in thread to not block the UI
        threading.Thread(target=restore_window_size_and_close_devtools, daemon=True).start()

    def start_desktop_window(self):
        """Start pywebview window"""
        print("🖥️  Opening desktop window...")

        # Create window pointing to localhost
        self.window = webview.create_window(
            'GearCrate - Star Citizen Inventory Manager',
            f'http://localhost:{self.port}/index.html',
            width=1400,
            height=900,
            resizable=True,
            background_color='#1a1a1a',
            confirm_close=False,
            on_top=False
        )

        # Store window reference in API for DevTools access
        API.set_webview_window(self.window)

        # Set loaded event handler
        self.window.events.loaded += self.on_loaded

        print("✅ Desktop window ready!")
        print("=" * 60)
        print("📦 GearCrate is running!")
        print("💡 Drücke F12 oder klicke 🐛 Debug um DevTools zu öffnen")
        print("=" * 60)

        # Start webview WITH debug=True to enable DevTools
        # DevTools will auto-open but we close them immediately in on_loaded()
        # This allows F12 and Debug button to work
        webview.start(debug=True)  # debug=True enables DevTools functionality
        
    def start(self):
        """Start the complete desktop application"""
        try:
            # 1. Start HTTP server in background
            self.start_http_server()
            
            # 2. Start desktop window (blocking)
            self.start_desktop_window()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup on exit"""
        print("🧹 Cleaning up...")
        
        if self.httpd:
            self.httpd.shutdown()
        
        if self.api and hasattr(self.api, 'close'):
            self.api.close()
        
        print("✅ GearCrate stopped!")


def main():
    """Main entry point"""
    print("=" * 60)
    print("📦 GearCrate - Desktop Mode")
    print("=" * 60)
    print()
    
    server = DesktopServer(port=8080)
    server.start()


if __name__ == '__main__':
    main()
