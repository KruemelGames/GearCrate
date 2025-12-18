# -*- coding: utf-8 -*-
"""
config.py – DYNAMICALLY SCALED geometry and scroll parameters for Star Citizen inventory scan
"""

# --- BASE GEOMETRY (for 1920x1080) ---
BASE_WIDTH = 1920
BASE_HEIGHT = 1080

# --- DYNAMIC GEOMETRY (DO NOT EDIT - SET BY initialize_geometry) ---
SCREEN_WIDTH = None
SCREEN_HEIGHT = None
INVENTORY_TOP = None
INVENTORY_BOTTOM = None
INVENTORY_LEFT = None
INVENTORY_RIGHT = None
SCROLLBAR_END_MIN = None
SCROLLBAR_END_MAX = None
BORDER_OFFSET_TOP = None
BORDER_OFFSET_LEFT = None
TILE_WIDTH = None
TILE_HEIGHT = None
TILE_SPACING = None
ROW_STEP = None
SCROLL_AREA_LEFT = None
SCROLL_AREA_TOP = None
SCROLL_AREA_RIGHT = None
SCROLL_AREA_BOTTOM = None
OCR_LEFT = None
OCR_TOP = None
OCR_RIGHT = None
OCR_BOTTOM = None
OCR_WIDTH = None
OCR_HEIGHT = None
START_X = None
START_Y = None
SCROLL_PIXELS_UP = None
TRACK_HEIGHT = None
HOVER_OFFSET_X = None
FIRST_ROW_Y_OFFSET = None

def initialize_geometry(target_width, target_height):
    """
    Calculates all geometry values based on a target resolution.
    Assumes a 16:9 aspect ratio for scaling.
    """
    global SCREEN_WIDTH, SCREEN_HEIGHT, INVENTORY_TOP, INVENTORY_BOTTOM, INVENTORY_LEFT, INVENTORY_RIGHT
    global SCROLLBAR_END_MIN, SCROLLBAR_END_MAX, BORDER_OFFSET_TOP, BORDER_OFFSET_LEFT, TILE_WIDTH, TILE_HEIGHT
    global TILE_SPACING, ROW_STEP, SCROLL_AREA_LEFT, SCROLL_AREA_TOP, SCROLL_AREA_RIGHT, SCROLL_AREA_BOTTOM
    global OCR_LEFT, OCR_TOP, OCR_RIGHT, OCR_BOTTOM, OCR_WIDTH, OCR_HEIGHT, START_X, START_Y
    global SCROLL_PIXELS_UP, TRACK_HEIGHT, HOVER_OFFSET_X, FIRST_ROW_Y_OFFSET

    # Calculate scaling factor based on width
    scale = target_width / BASE_WIDTH
    
    # Screen
    SCREEN_WIDTH = target_width
    SCREEN_HEIGHT = target_height

    # Inventory frame
    INVENTORY_TOP = int(220 * scale)
    INVENTORY_BOTTOM = int(1021 * scale)
    INVENTORY_LEFT = int(1348 * scale)
    INVENTORY_RIGHT = int(1790 * scale)

    # Scrollbar end detection
    SCROLLBAR_END_MIN = int(1010 * scale)
    SCROLLBAR_END_MAX = int(1021 * scale)

    # Tile geometry
    BORDER_OFFSET_TOP = int(4 * scale)
    BORDER_OFFSET_LEFT = int(4 * scale)
    TILE_WIDTH = int(86 * scale)
    TILE_HEIGHT = int(86 * scale)
    TILE_SPACING = int(10 * scale)
    ROW_STEP = int(97 * scale)

    # Scroll area
    SCROLL_AREA_LEFT = int(1790 * scale)
    SCROLL_AREA_TOP = int(220 * scale)
    SCROLL_AREA_RIGHT = int(1800 * scale)
    SCROLL_AREA_BOTTOM = int(1022 * scale)

    # OCR region
    OCR_LEFT = int(1095 * scale)
    OCR_TOP = int(100 * scale)
    OCR_RIGHT = int(1326 * scale)
    OCR_BOTTOM = int(135 * scale)
    OCR_WIDTH = OCR_RIGHT - OCR_LEFT
    OCR_HEIGHT = OCR_BOTTOM - OCR_TOP
    
    # Start positions
    START_X = INVENTORY_LEFT + BORDER_OFFSET_LEFT
    START_Y = INVENTORY_TOP + BORDER_OFFSET_TOP
    
    # Scroll distances
    SCROLL_PIXELS_UP = int(322 * scale)
    TRACK_HEIGHT = SCROLL_AREA_BOTTOM - SCROLL_AREA_TOP
    
    # Core corrections
    HOVER_OFFSET_X = int(53 * scale)
    FIRST_ROW_Y_OFFSET = int(38 * scale)

# --- STATIC PARAMETERS (NOT SCALED) ---

# The colors of the scrollbar thumb
SCROLLBAR_COLOR = (17, 103, 120)  
SCROLLBAR_COLOR_HOVER = (29, 160, 145)  
SCROLL_COLOR_TOLERANCE = 15     # Tolerance for color differences

MAX_COLUMNS = 4
VISIBLE_ROWS = 8
ROWS_PER_BLOCK = 8

# Empirical correction factor (calibrated with 322px @ 25 rows)
SCROLL_CORRECTION_FACTOR = 1.21

# Enable debug logging for scroll calculations
DEBUG_SCROLL_CALCULATION = False

# FAST DEBUG MODE - Skip OCR, only test mouse movement and scroll logic
FAST_DEBUG_MODE = False

SCROLL_DURATION = 0.5  # Drag duration (used in pyautogui.drag)
SCROLL_WAIT = 0.6      # Wait time after scroll

# FILES
OUTPUT_FILE = "detected_items.txt"
LOG_FILE    = "scan_log.txt"

# YOUR DATABASE (Universal path - works on any PC)
import os as _os
DB_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'data', 'inventory.db')

# SCAN MODE (set by GearCrate web interface, but can be overridden)
SCAN_MODE = 1

DRIFT_COMPENSATION_PER_BLOCK = 0

# --- INITIALIZE WITH DEFAULT 1920x1080 RESOLUTION ---
# This ensures the script runs correctly if not called with custom resolution
initialize_geometry(BASE_WIDTH, BASE_HEIGHT)