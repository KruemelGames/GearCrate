# -*- coding: utf-8 -*-
"""
ocr_scanner.py – final version
EasyOCR + automatic name correction via your inventory.db
"""

import cv2
import numpy as np
from rapidfuzz import fuzz, process
from database import ITEM_DATABASE   # ← all names from your DB
from ocr_fixes import get_fixes, get_chars_to_remove  # ← OCR corrections from external file

# Start EasyOCR once (CPU is sufficient)
# Suppress warnings
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# Only load EasyOCR if not in Fast Debug Mode (saves ~5-10 seconds startup time)
reader = None
try:
    from config import FAST_DEBUG_MODE
    if not FAST_DEBUG_MODE:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    else:
        print("[OCR] Skipped loading EasyOCR (FAST_DEBUG_MODE=True)")
except:
    # If config not available or error, load normally
    import easyocr
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)

def preprocess(img):
    """Optimized for your 231×35px tooltip region"""
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
    gray = cv2.filter2D(gray, -1, kernel)
    return gray

def correct_with_database(text):
    """Corrects OCR errors – compatible with all rapidfuzz versions"""
    if not text or len(text) < 4 or not ITEM_DATABASE:
        return text.strip()

    # Load OCR fixes from external file
    fixes = get_fixes()
    chars_to_remove = get_chars_to_remove()

    # Remove unwanted characters
    for char in chars_to_remove:
        text = text.replace(char, '')

    # Apply fixes
    for wrong, right in fixes.items():
        text = text.replace(wrong, right)

    # Case-insensitive fuzzy matching: Convert to lowercase for comparison
    text_lower = text.lower()
    db_lower = [item.lower() for item in ITEM_DATABASE]

    # New call without limit parameter (works with 3.x and 4.x)
    result = process.extractOne(text_lower, db_lower, scorer=fuzz.token_sort_ratio)
    if result:
        best_match_lower, score, index = result
        # Threshold lowered from 88 to 75 for better partial word matches
        # e.g. "Oracle Helmet" → "Oracle Helmet Black" (Score ~80)
        if score >= 75:
            # Return the ORIGINAL name from DB (not lowercase)
            return ITEM_DATABASE[index]

    # No match found - return empty string
    # Raw OCR text is used separately for debug output
    return ""

def scan_image_for_text(image):
    """
    Main function – called by inventory_detector

    Returns:
        tuple: (corrected_text, raw_ocr_text, was_corrected)
               - corrected_text: The final text after database correction (or "" if invalid)
               - raw_ocr_text: The original OCR text before correction
               - was_corrected: True if text was corrected by database
    """
    try:
        processed = preprocess(image)
        results = reader.readtext(processed, detail=0, paragraph=True)
        raw_text = " ".join(results).strip()

        # Cut off Volume line and everything after
        if "Volume:" in raw_text:
            raw_text = raw_text.split("Volume:")[0].strip()

        # Save raw text for debug output
        raw_ocr_text = raw_text

        # Apply database correction
        final_text = correct_with_database(raw_text)

        # Check if text was corrected
        was_corrected = (final_text != raw_text) and final_text in ITEM_DATABASE

        # Only return meaningful results
        if len(final_text) >= 4 and not final_text[0].isdigit():
            return (final_text, raw_ocr_text, was_corrected)
        else:
            # Also return raw text for invalid results
            return ("", raw_ocr_text, False)

    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ("", "", False)
