"""
GUI window setup using pywebview
"""
import webview
import os
import sys

# Add src to path if not already there
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.backend import API


class Window:
    def __init__(self):
        """Initialize window"""
        self.api = API()
        
        # Get absolute path to HTML file
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.html_path = os.path.join(current_dir, 'web', 'index.html')
    
    def create_window(self):
        """Create and return pywebview window"""
        window = webview.create_window(
            'SC Inventory Manager',
            self.html_path,
            js_api=self.api,
            width=1200,
            height=800,
            resizable=True,
            background_color='#1a1a1a'
        )
        return window
    
    def start(self):
        """Start the application"""
        window = self.create_window()
        webview.start(debug=False)
        
        # Cleanup on exit
        self.api.close()
