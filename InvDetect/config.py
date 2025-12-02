# -*- coding: utf-8 -*-
"""
config.py – Final corrected geometry and scroll parameters for Star Citizen inventory scan
"""

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Inventory frame (Universal Inventory at 1920×1080)
INVENTORY_TOP = 220
INVENTORY_BOTTOM = 1021
INVENTORY_LEFT = 1348
INVENTORY_RIGHT = 1790

# Scrollbar end detection (bottom end of scrollbar)
SCROLLBAR_END_MIN = 1010  # Lower limit for "at end" (previously 930 - too low!)
SCROLLBAR_END_MAX = 1021  # Upper limit (INVENTORY_BOTTOM)

BORDER_OFFSET_TOP = 4
BORDER_OFFSET_LEFT = 4

TILE_WIDTH = 86
TILE_HEIGHT = 86         # Tile height (added for clarity)
TILE_SPACING = 10

# NEW: Exact step size to next row
ROW_STEP = 97            # 86px tile + 10px spacing + 1px correction = 97px

# --- SCROLL PARAMETERS (FOR PIXEL-PRECISE DRAG-SCROLLING WITH COLOR DETECTION) ---
# The defined area where the scrollbar is located
SCROLL_AREA_LEFT = 1790
SCROLL_AREA_TOP = 220
SCROLL_AREA_RIGHT = 1800
SCROLL_AREA_BOTTOM = 1022

# The colors of the scrollbar thumb
SCROLLBAR_COLOR = (0, 131, 158)  # RGB for #00839e (not hovered)
SCROLLBAR_COLOR_HOVER = (0, 193, 178)  # RGB for #00c1b2 (hovered)
SCROLL_COLOR_TOLERANCE = 15     # Tolerance for color differences (important for reliability)

# Fixed OCR region (tooltip at top center)
OCR_LEFT   = 1095
OCR_TOP    = 100
OCR_RIGHT  = 1326
OCR_BOTTOM = 135
OCR_WIDTH  = OCR_RIGHT - OCR_LEFT
OCR_HEIGHT = OCR_BOTTOM - OCR_TOP

MAX_COLUMNS = 4

START_X = INVENTORY_LEFT + BORDER_OFFSET_LEFT    # 1352
START_Y = INVENTORY_TOP + BORDER_OFFSET_TOP      # 224

# Exact 101px drag-scroll
SCROLL_PIXELS_UP = 322
SCROLL_DURATION = 0.5  # Drag duration (used in pyautogui.drag)
SCROLL_WAIT = 0.6      # Wait time after scroll (for game latency)

# FILES
OUTPUT_FILE = "detected_items.txt"
LOG_FILE    = "scan_log.txt"

# YOUR DATABASE
DB_PATH = r"C:\Users\kruem\PycharmProjects\GearCrate\data\inventory.db"

# SCAN MODE (set by GearCrate web interface)
# 1 = 1x1 Items (Normal)
# 2 = 1x2 Items (Undersuits)
SCAN_MODE = 1

# ←←← CORE CORRECTIONS HERE ←←←
HOVER_OFFSET_X = 53                     # X-position within tile
FIRST_ROW_Y_OFFSET = 38                 # Y-offset to center of first row
DRIFT_COMPENSATION_PER_BLOCK = 0      # 28px-4px = 24px correction per scroll (scrolled too much)