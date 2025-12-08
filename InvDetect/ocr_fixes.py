# -*- coding: utf-8 -*-
"""
ocr_fixes.py - Configuration file for OCR corrections
Common OCR errors that should be automatically corrected can be defined here.
"""

# Dictionary with OCR errors and their corrections
# Format: "Incorrectly recognized text": "Correct text"
OCR_FIXES = {
    # === Known issues ===
    "Olve": "Olive",
    "Helment": "Helmet",
    "Hel met": "Helmet",
    "J-S": "J-5",
    "Morozov SH": "Morozov-SH",
    "CBH-3": "CBH-3",
    "Harizon": "Horizon",  # a ↔ o

    # === Errors detected from logs ===
    "@racle Helmet": "Oracle Helmet",
    "Harizon Helmet Rust Society": "Horizon Helmet Rust Society",
    "Paladin Helmet Black/ Silver": "Paladin Helmet Black/Silver",
    "cBH- 3 Helmet Yellow": "CBH-3 Helmet Yellow",
    "cBH-3 Helmet Yellow": "CBH-3 Helmet Yellow",
    'Venture Helmet Rust Society"': "Venture Helmet Rust Society",
    "Morozov-SH-CHelmet Vesper": "Morozov-SH-C Helmet Vesper",
    "AdP-mk4 Core Justified": "ADP-mk4 Core Justified",
    "@RC-mkX Helmet Justified": "ORC-mkX Helmet Justified",
    "orc-mkx Helmet Arctic": "ORC-mkX Helmet Arctic",
    "@RC-mkx Helmet Autumn": "ORC-mkX Helmet Autumn",
    "Argus Helmet Black/White/ Violet": "Argus Helmet Black/White/Violet",
    "Pembroke Helmet RSIIvory Edition": "Pembroke Helmet RSI Ivory Edition",
    "Aztalan Helmet Epoque": "Aztalan Helmet Epoque",  # Correct here if wrong
    "Aril Legs Modified)": "Aril Legs (Modified)",
    "Chamar Pants": "Chamar Pants (08_01_01)",
    "Morozov-SHcore": "Morozov-SH Core",
    "Ambrus Suit": "Ambrus Suit (01_01_01",
    "Snapback Boots": "Snapback Boots (04_01_01)",
    "Z1uf Gloves": "2Tuf Gloves",
    "ztuf Gloves": "2Tuf Gloves",
    "21uf Gloves": "2Tuf Gloves",
    "Z1iuf Gloves": "2Tuf Gloves",
    "Z1uf Gloves": "2Tuf Gloves",
    "ztuf Gloves": "2Tuf Gloves",
    # === Number-letter confusions ===
    "6-2": "G-2",   # 6 ↔ G
    "0RC": "ORC",   # 0 ↔ O
    "@RC": "ORC",   # @ ↔ O
    "R5I": "RSI",   # 5 ↔ S
    "R51": "RSI",   # 5+1 ↔ S+I
    "1-5": "I-5",   # 1 ↔ I (when I is meant)
    "8CS": "BCS",   # 8 ↔ B
    "C-S4": "C-54", # S ↔ 5

    # === Missing/wrong hyphens ===
    "J5": "J-5",
    "J 5": "J-5",
    "G2": "G-2",
    "G 2": "G-2",

    # === Upper/lowercase ===
    "orc-mkx": "ORC-mkX",
    "cbh-3": "CBH-3",
    "adp-mk4": "ADP-mk4",
}

# Additional characters to be removed
CHARS_TO_REMOVE = [
    '"',  # Quotation marks at end
    "'",  # Single quotation marks
]

def get_fixes():
    """
    Returns the OCR fixes dictionary.

    Returns:
        dict: Dictionary with OCR errors and corrections
    """
    return OCR_FIXES.copy()

def get_chars_to_remove():
    """
    Returns the list of characters to remove.

    Returns:
        list: List of characters that should be removed
    """
    return CHARS_TO_REMOVE.copy()
