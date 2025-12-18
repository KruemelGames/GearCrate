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
from utils.logger import setup_logger
import pyautogui
import webview

# Setup logger
logger = setup_logger(__name__)
#

class DesktopServer:
    """Desktop server with pywebview"""

    def __init__(self, port=8080):
        self.port = port
        self.httpd = None
        self.server_thread = None
        self.api = None
        self.window = None
        self.devtools_open = False
        self.last_known_geometry = {}  # Store last valid non-maximized geometry
        self._handlers_registered = False  # Flag to prevent double registration
        
    def start_http_server(self):
        """Start HTTP server in background thread"""
        logger.info("Starting HTTP server...", extra={'emoji': '🔧'})
        
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

        logger.info(f"HTTP Server running on http://localhost:{self.port}", extra={'emoji': '✅'})
        
        # Wait a bit to ensure server is ready
        time.sleep(0.5)
    
    def on_loaded(self):
        """
        Called when the window finishes loading.
        Restores window geometry and deals with DevTools.
        """
        logger.info("Attempting to restore window geometry...", extra={'emoji': '🔄'})

        try:
            # Get saved geometry from the backend API
            result = self.api.get_window_geometry()
            logger.info(f"Saved window data: {result}", extra={'emoji': '📋'})

            if result.get('success'):
                saved_maximized = result.get('maximized', False)

                if saved_maximized:
                    # If the window was maximized, just maximize it.
                    self.window.maximize()
                    logger.info("Window restored to maximized state.", extra={'emoji': '✅'})
                elif result.get('width') and result.get('height'):
                    # Otherwise, restore to specific dimensions and position.
                    saved_width = result['width']
                    saved_height = result['height']
                    saved_x = result.get('x')
                    saved_y = result.get('y')

                    # Validate window size
                    MIN_WIDTH, MAX_WIDTH = 800, 4000
                    MIN_HEIGHT, MAX_HEIGHT = 600, 3000
                    if not (MIN_WIDTH <= saved_width <= MAX_WIDTH):
                        logger.warning(f"Invalid saved width {saved_width}, using default 1400", extra={'emoji': '⚠️'})
                        saved_width = 1400
                    if not (MIN_HEIGHT <= saved_height <= MAX_HEIGHT):
                        logger.warning(f"Invalid saved height {saved_height}, using default 900", extra={'emoji': '⚠️'})
                        saved_height = 900

                    # 1. Restore size
                    self.window.resize(saved_width, saved_height)
                    logger.info(f"Window size restored: {saved_width}x{saved_height}", extra={'emoji': '✅'})

                    # 2. Restore position with validation
                    if saved_x is not None and saved_y is not None:
                        # Check against screen dimensions to prevent off-screen placement
                        try:
                            screen_width, screen_height = pyautogui.size()
                            is_off_screen = (
                                saved_x > screen_width or saved_y > screen_height or
                                saved_x < -saved_width + 100 or saved_y < -saved_height + 100
                            )
                            is_minimized = saved_x <= -30000 or saved_y <= -30000

                            if is_minimized:
                                logger.warning("Saved position indicates a minimized window; centering instead.", extra={'emoji': '⚠️'})
                                center_x = (screen_width - saved_width) // 2
                                center_y = (screen_height - saved_height) // 2
                                self.window.move(center_x, center_y)
                            elif is_off_screen:
                                logger.warning(f"Saved position ({saved_x}, {saved_y}) is off-screen; centering.", extra={'emoji': '⚠️'})
                                center_x = (screen_width - saved_width) // 2
                                center_y = (screen_height - saved_height) // 2
                                self.window.move(center_x, center_y)
                            else:
                                self.window.move(saved_x, saved_y)
                                logger.info(f"Window position restored: ({saved_x}, {saved_y})", extra={'emoji': '✅'})
                        except Exception as e:
                            logger.error(f"Failed to validate screen position, using default: {e}", extra={'emoji': '❌'})
                            self.window.move(100, 100)
                
                # After restoring, capture the current geometry as the "last known good one"
                if not saved_maximized:
                    self.last_known_geometry = {
                        'x': self.window.x, 'y': self.window.y,
                        'width': self.window.width, 'height': self.window.height
                    }
                    logger.info(f"Initial non-maximized geometry cached: {self.last_known_geometry}", extra={'emoji': '📝'})

        except Exception as e:
            logger.error(f"Could not restore window geometry: {e}", extra={'emoji': '❌'})

        # Asynchronously close DevTools if they opened automatically
        def close_devtools_if_needed():
            try:
                import pyautogui
                time.sleep(0.3)
                pyautogui.press('f12')
                logger.info("DevTools closed (re-open with F12 or 🐛 Debug button)", extra={'emoji': '✅'})
            except Exception as e:
                logger.warning(f"Could not close DevTools automatically: {e}", extra={'emoji': '⚠️'})
            logger.info("DevTools are available via F12 or the 🐛 Debug button.", extra={'emoji': '📌'})

        threading.Thread(target=close_devtools_if_needed, daemon=True).start()

    def on_closing(self):
        """Called when the window is about to be closed. Saves the final geometry."""
        try:
            # Heuristic: A maximized window on Windows often has negative or zero coordinates.
            is_maximized = self.window.x <= 0 and self.window.y <= 0
            
            # If the window is not maximized, update last_known_geometry to the current state.
            if not is_maximized:
                x, y, width, height = self.window.x, self.window.y, self.window.width, self.window.height
                # Do not save if the window is minimized or has an invalid size
                if not (x <= -30000 or y <= -30000 or width < 800 or height < 600):
                    self.last_known_geometry = {'x': x, 'y': y, 'width': width, 'height': height}

            # Prepare data to save. Use last_known_geometry if it exists.
            if self.last_known_geometry:
                saved_geometry = self.last_known_geometry.copy()
                saved_geometry['maximized'] = is_maximized
            else:
                # Fallback to safe defaults if no valid geometry was ever captured
                saved_geometry = {'x': 100, 'y': 100, 'width': 1400, 'height': 900, 'maximized': is_maximized}

            self.api.save_window_geometry(saved_geometry)
            logger.info(f"Window geometry saved on close: {saved_geometry}", extra={'emoji': '💾'})

        except Exception as e:
            logger.warning(f"Exception saving window geometry on close: {e}", extra={'emoji': '⚠️'})

        return True  # Allow window to close

    def on_resize(self, width, height):
        """Called on window resize. Updates in-memory 'last_known_geometry' if not maximized."""
        try:
            # Heuristic: A maximized window on Windows often has negative or zero coordinates.
            is_maximized = self.window.x <= 0 and self.window.y <= 0

            # Only update our in-memory geometry cache if the window is not maximized.
            if not is_maximized and self.window.x is not None and self.window.y is not None:
                x, y = self.window.x, self.window.y

                # Do not cache invalid states (minimized or too small)
                if x > -30000 and y > -30000 and width >= 800 and height >= 600:
                    self.last_known_geometry = {'x': x, 'y': y, 'width': width, 'height': height}
                    logger.debug(f"Cached non-maximized geometry: {self.last_known_geometry}", extra={'emoji': '📝'})
        except Exception as e:
            logger.warning(f"Exception caching geometry on resize: {e}", extra={'emoji': '⚠️'})

    def on_move(self, x, y):
        """Called on window move. Triggers the same logic as resize."""
        if self.window:
            self.on_resize(self.window.width, self.window.height)

    def _register_event_handlers(self):
        """Register event handlers with safety check to prevent double registration"""
        if self._handlers_registered:
            logger.warning("Event handlers already registered, skipping...", extra={'emoji': '⚠️'})
            return

        try:
            # Remove any existing handlers first (just in case)
            self.window.events.loaded -= self.on_loaded
            self.window.events.closing -= self.on_closing
            self.window.events.resized -= self.on_resize
            self.window.events.moved -= self.on_move
        except:
            # Handlers weren't registered yet, that's fine
            pass

        # Now register the handlers
        self.window.events.loaded += self.on_loaded
        self.window.events.closing += self.on_closing
        self.window.events.resized += self.on_resize
        self.window.events.moved += self.on_move

        self._handlers_registered = True
        logger.info("Event handlers registered", extra={'emoji': '✅'})

    def _unregister_event_handlers(self):
        """Safely unregister all event handlers"""
        if not self._handlers_registered:
            return

        try:
            self.window.events.loaded -= self.on_loaded
            self.window.events.closing -= self.on_closing
            self.window.events.resized -= self.on_resize
            self.window.events.moved -= self.on_move
            self._handlers_registered = False
            logger.info("Event handlers unregistered", extra={'emoji': '✅'})
        except Exception as e:
            logger.warning(f"Error unregistering handlers: {e}", extra={'emoji': '⚠️'})

    def reload_event_handlers(self):
        """Force reload of event handlers (unregister + register)"""
        self._unregister_event_handlers()
        self._register_event_handlers()

    def start_desktop_window(self):
        """Start pywebview window"""
        logger.info("Opening desktop window...", extra={'emoji': '🖥️'})

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

        # Set event handlers (with safety check to prevent double registration)
        self._register_event_handlers()

        logger.info("Desktop window ready!", extra={'emoji': '✅'})
        logger.info("=" * 60)
        logger.info("GearCrate is running!", extra={'emoji': '📦'})
        logger.info("Drücke F12 oder klicke 🐛 Debug um DevTools zu öffnen", extra={'emoji': '💡'})
        logger.info("=" * 60)

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
            logger.info("\nShutting down...", extra={'emoji': '🛑'})
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup on exit"""
        logger.info("Cleaning up...", extra={'emoji': '🧹'})

        if self.httpd:
            self.httpd.shutdown()

        if self.api and hasattr(self.api, 'close'):
            self.api.close()

        logger.info("GearCrate stopped!", extra={'emoji': '✅'})


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("GearCrate - Desktop Mode", extra={'emoji': '📦'})
    logger.info("=" * 60)
    logger.info("")
    
    server = DesktopServer(port=8080)
    server.start()


if __name__ == '__main__':
    main()
