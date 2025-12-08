# -*- coding: utf-8 -*-
"""
inventory_detector.py – FINAL VERSION
Implements:
1. Correct 97px row shift.
2. Stable drift compensation (e.g. 16px).
3. Robust scrolling via color detection of dynamic scrollbar.
4. Corrected scroll direction (drag down = content scrolls down).
"""

import pyautogui
import time
import config
import ocr_scanner
import keyboard
import os
from collections import Counter 

def log_print(*args, **kwargs):
    msg = " ".join(map(str, args))
    print(msg, **kwargs)
    try:
        # Ensure log file from config is read and written
        with open(config.LOG_FILE, "a", encoding="utf-8", buffering=1) as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except:
        pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01  # faster execution

class ScanAbortedException(Exception):
    """Custom Exception for DELETE abort"""
    pass

class InventoryScanner:
    def __init__(self):
        self.detected_items = Counter()  # Counter instead of set() for duplicate counting
        self.block_counter = 0   # incremented AFTER scrolling → correct!
        self.scan_active = False  # Flag for active scan
        self.last_row_items = []  # Stores items from last row before reverse scan
        self.not_detected_items = {}  # Stores OCR text with position: {text: [(page, row, col), ...]}
        self.current_page = 0  # Track current page number
        self.current_row = 0  # Track current row number
        self.current_col = 0  # Track current column number

        # Create output file on start if not exists
        if not os.path.exists(config.OUTPUT_FILE):
            try:
                with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    f.write("# Inventory Scan Results\n")
                    f.write("# Format: Count, Item-Name\n")
                    f.write("# Waiting for scan to complete...\n")
                log_print(f"[INFO] Output file created: {config.OUTPUT_FILE}")
            except Exception as e:
                log_print(f"[WARNING] Could not create output file: {e}")

    def check_abort(self):
        """Checks if DELETE was pressed and throws exception"""
        if keyboard.is_pressed('delete'):
            self.scan_active = False
            import traceback
            # Debug: Show where abort occurred
            stack = traceback.extract_stack()
            caller = stack[-2]  # The calling function
            log_print(f"\n[ABORT] DELETE pressed at {caller.name}:{caller.lineno}")
            raise ScanAbortedException("DELETE pressed")

    def check_button_brightness(self):
        """
        Checks the average grayscale brightness of the button in region x1608-1616, y1034-1047.
        Returns:
            bool: True if button is active (brightness 65-85), False otherwise
        """
        # Screenshot of button region
        button_region = (1608, 1034, 8, 13)  # x, y, width, height
        screenshot = pyautogui.screenshot(region=button_region)

        # Convert to grayscale and calculate average brightness
        import numpy as np
        from PIL import Image

        # Convert PIL Image to grayscale
        gray_image = screenshot.convert('L')

        # Convert to numpy array for calculation
        gray_array = np.array(gray_image)

        # Calculate average brightness
        avg_brightness = np.mean(gray_array)

        # Button is only active when brightness is in range 65-85
        # Too dark (< 65) = no button or inactive
        # Too bright (> 85) = background without button
        is_active = 65 <= avg_brightness <= 85

        if is_active:
            status = "Active"
        elif avg_brightness > 85:
            status = "Too bright (background)"
        else:
            status = "Inactive"

        log_print(f"[BUTTON] Brightness: {avg_brightness:.1f} → {status}")

        return is_active

    def reset_to_top(self):
        log_print("Scrolling to top...")

        # First, move to first tile (top left) so scroll works in inventory area
        first_tile_x = config.START_X + config.HOVER_OFFSET_X
        first_tile_y = config.START_Y + config.FIRST_ROW_Y_OFFSET

        pyautogui.moveTo(first_tile_x, first_tile_y, duration=0)
        time.sleep(0.1)

        # Scroll to top (mouse is now over inventory, so scroll works)
        for i in range(40):
            self.check_abort()
            pyautogui.scroll(1200)
            time.sleep(0.04)

        for _ in range(15):
            self.check_abort()
            time.sleep(0.1)

        # Move mouse away briefly to reset tooltip state
        pyautogui.moveTo(config.START_X + 200, config.INVENTORY_BOTTOM + 20, duration=0.1)
        time.sleep(0.1)

        # Move back to first tile - this is a fresh movement that triggers tooltip
        pyautogui.moveTo(first_tile_x, first_tile_y, duration=0.15)
        time.sleep(0.25)  # Give tooltip time to appear after fresh movement

        self.block_counter = 0
        log_print("Reset complete")

    def calculate_scroll_distance(self, scrollbar_height):
        """
        Calculates dynamic scroll distance based on scrollbar thumb height.

        Args:
            scrollbar_height: Measured height of scrollbar thumb in pixels

        Returns:
            int: Scroll distance in pixels for ROWS_PER_BLOCK rows
        """
        # Get constants from config
        track_height = config.TRACK_HEIGHT
        visible_rows = config.VISIBLE_ROWS
        rows_per_block = config.ROWS_PER_BLOCK
        correction_factor = config.SCROLL_CORRECTION_FACTOR

        # Calculate estimated total rows from thumb height
        # Formula: total_rows = (track_height × visible_rows) / thumb_height
        total_rows_estimated = (track_height * visible_rows) / scrollbar_height

        # Store for use in scan logic
        self.total_rows_estimated = total_rows_estimated

        # Calculate travel space (space available for thumb movement)
        travel_space = track_height - scrollbar_height

        # Calculate invisible rows (rows outside viewport)
        invisible_rows = total_rows_estimated - visible_rows

        # Debug logging
        if getattr(config, 'DEBUG_SCROLL_CALCULATION', False):
            log_print(f"\n[SCROLL CALC DEBUG]")
            log_print(f"  Scrollbar Height: {scrollbar_height}px")
            log_print(f"  Track Height: {track_height}px")
            log_print(f"  Travel Space: {travel_space}px")
            log_print(f"  Estimated Total Rows: {total_rows_estimated:.1f}")
            log_print(f"  Visible Rows: {visible_rows}")
            log_print(f"  Invisible Rows: {invisible_rows:.1f}")

        # Handle edge cases
        if invisible_rows <= 0:
            # All rows visible, no scrolling needed
            if getattr(config, 'DEBUG_SCROLL_CALCULATION', False):
                log_print(f"  → Result: 0px (all rows visible)")
            return 0

        # Calculate base scroll distance
        # Formula: travel_space × (rows_per_block / invisible_rows)
        scroll_distance_base = travel_space * (rows_per_block / invisible_rows)

        # Apply dynamic correction factor based on number of invisible rows
        # Empirical data from testing:
        # - At 17+ invisible rows (25+ total): factor = 1.21 works correctly
        # - At 10 invisible rows (19 total): factor = 1.31 overshoots by 1 row (too high)
        # - Solution: Use standard factor 1.21 for 10+ invisible rows
        # - For very small inventories (<10 invisible): slightly higher factor needed
        if invisible_rows >= 10:
            # Medium to large inventories: use reference factor
            dynamic_correction = correction_factor  # 1.21
        elif invisible_rows <= 8:
            # Very small inventories: need slightly higher factor
            dynamic_correction = 1.28
        else:
            # Interpolate between 8 and 10 invisible rows
            # factor = 1.28 + (invisible_rows - 8) / (10 - 8) × (1.21 - 1.28)
            dynamic_correction = 1.28 + (invisible_rows - 8) / 2.0 * (1.21 - 1.28)

        scroll_distance = scroll_distance_base * dynamic_correction

        if getattr(config, 'DEBUG_SCROLL_CALCULATION', False):
            log_print(f"  Dynamic Correction Factor: {dynamic_correction:.2f} (base: {correction_factor})")

        # Debug logging
        if getattr(config, 'DEBUG_SCROLL_CALCULATION', False):
            log_print(f"  Base Distance: {scroll_distance_base:.1f}px")
            log_print(f"  Correction Factor: {correction_factor}")
            log_print(f"  → Final Distance: {int(scroll_distance)}px")

            # Compare with legacy value for 25 rows
            if 24 <= total_rows_estimated <= 26:
                legacy = config.SCROLL_PIXELS_UP
                diff = int(scroll_distance) - legacy
                log_print(f"  [REF] Legacy value for ~25 rows: {legacy}px (diff: {diff:+d}px)")

        return int(scroll_distance)

    def precise_scroll_down_once(self, scroll_distance=None, use_dynamic_calculation=True):
        """
        Scrolls down with adjusted distance.

        Args:
            scroll_distance: Pixels to scroll (if None, uses dynamic calculation or config default)
            use_dynamic_calculation: If True, calculates scroll distance from scrollbar height

        Scrolls down with adjusted distance.

        Args:
            scroll_distance: Pixels to scroll (default: config.SCROLL_PIXELS_UP)
        """
        self.check_abort()

        log_print(f"  Scrollbar detection...")



        log_print(f"  Scrollbar detection (distance: {scroll_distance}px)...")


        # 1. Take screenshot of scroll region
        scroll_shot = pyautogui.screenshot(region=(
            config.SCROLL_AREA_LEFT,
            config.SCROLL_AREA_TOP,
            config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT,
            config.SCROLL_AREA_BOTTOM - config.SCROLL_AREA_TOP
        ))

        # 2. Find all pixels with scrollbar color and largest contiguous area
        import numpy as np
        img_array = np.array(scroll_shot)

        # Create mask for scrollbar color (both colors: normal and hovered)
        tolerance = config.SCROLL_COLOR_TOLERANCE

        # Check both colors
        color1 = np.array(config.SCROLLBAR_COLOR)  # Not hovered
        color2 = np.array(config.SCROLLBAR_COLOR_HOVER)  # Hovered

        # Calculate distance of each pixel to both target colors
        color_diff1 = np.abs(img_array - color1)
        matches1 = np.all(color_diff1 <= tolerance, axis=2)

        color_diff2 = np.abs(img_array - color2)
        matches2 = np.all(color_diff2 <= tolerance, axis=2)

        # Combine both masks (OR operation)
        matches = matches1 | matches2

        # Find Y-coordinates of all matching pixels in middle X column
        mid_x = (config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT) // 2
        matching_ys = np.where(matches[:, mid_x])[0]

        found_y = -1
        found_y_bottom = -1
        scrollbar_height = 0

        if len(matching_ys) > 0:
            # Find largest contiguous group (scrollbar)
            groups = []
            current_group = [matching_ys[0]]

            for i in range(1, len(matching_ys)):
                if matching_ys[i] - matching_ys[i-1] <= 2:  # Max 2px gap
                    current_group.append(matching_ys[i])
                else:
                    groups.append(current_group)
                    current_group = [matching_ys[i]]
            groups.append(current_group)

            # Largest group = scrollbar
            largest_group = max(groups, key=len)
            if len(largest_group) >= 10:  # At least 10px tall
                # Center and bottom end of largest group
                found_y = int(np.mean(largest_group))
                found_y_bottom = int(np.max(largest_group))  # Bottom end (relative)
                scrollbar_height = len(largest_group)

                # Calculate absolute coordinates
                absolute_y = found_y + config.SCROLL_AREA_TOP
                absolute_y_bottom = found_y_bottom + config.SCROLL_AREA_TOP

                log_print(f"  Scrollbar found: Y={absolute_y}, Bottom={absolute_y_bottom}, Height={scrollbar_height}px")

                # Check if scrollbar is at bottom
                end_min = getattr(config, 'SCROLLBAR_END_MIN', 930)
                end_max = getattr(config, 'SCROLLBAR_END_MAX', 1021)
                if absolute_y_bottom >= end_min and absolute_y_bottom <= end_max:
                    log_print(f"  ✓ [END] Scrollbar at bottom (Y={absolute_y_bottom})")
                    return "END"

                # Calculate dynamic scroll distance if enabled and not provided
                if scroll_distance is None and use_dynamic_calculation:
                    scroll_distance = self.calculate_scroll_distance(scrollbar_height)
                    log_print(f"  Using dynamic scroll distance: {scroll_distance}px")
                elif scroll_distance is None:
                    scroll_distance = config.SCROLL_PIXELS_UP
                    log_print(f"  Using legacy scroll distance: {scroll_distance}px")
            else:
                log_print(f"  [WARNING] Scrollbar too small: {len(largest_group)}px")

        # Determine drag start point
        if found_y == -1:
            log_print("  [NO_SCROLLBAR] Scrollbar not found - no scrolling needed")
            return "NO_SCROLLBAR"
        else:
            # Success: Absolute coordinates
            cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
            cy = found_y + config.SCROLL_AREA_TOP

        # 4. Check if drag would pull scrollbar out of bounds
        drag_distance = scroll_distance
        target_y = cy + drag_distance
        # Allow up to just before SCROLLBAR_END_MAX (so scrollbar can land in target area)
        end_max = getattr(config, 'SCROLLBAR_END_MAX', 1021)
        max_y = end_max + 5  # 5px buffer above target area

        if target_y > max_y:
            adjusted_drag = max_y - cy
            log_print(f"  [WARNING] Drag too far, adjusting: {drag_distance}px → {adjusted_drag}px")
            drag_distance = adjusted_drag

        log_print(f"  Dragging from X={cx}, Y={cy}, distance={drag_distance}px")

        self.check_abort()
        pyautogui.moveTo(cx, cy, duration=0.05)
        time.sleep(0.15)

        self.check_abort()
        pyautogui.drag(0, drag_distance, duration=0.3, button='left')

        wait_steps = 8
        for _ in range(wait_steps):
            self.check_abort()
            time.sleep(config.SCROLL_WAIT / wait_steps)

        self.block_counter += 1
        log_print(f"  Scrolled (block {self.block_counter})")

        # Check if scrollbar reached end after drag
        time.sleep(0.2)  # Brief wait for scrollbar to settle
        scroll_shot_after = pyautogui.screenshot(region=(
            config.SCROLL_AREA_LEFT,
            config.SCROLL_AREA_TOP,
            config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT,
            config.SCROLL_AREA_BOTTOM - config.SCROLL_AREA_TOP
        ))

        # Find scrollbar position after drag
        img_array_after = np.array(scroll_shot_after)
        color1 = np.array(config.SCROLLBAR_COLOR)
        color2 = np.array(config.SCROLLBAR_COLOR_HOVER)
        tolerance = config.SCROLL_COLOR_TOLERANCE

        color_diff1_after = np.abs(img_array_after - color1)
        matches1_after = np.all(color_diff1_after <= tolerance, axis=2)
        color_diff2_after = np.abs(img_array_after - color2)
        matches2_after = np.all(color_diff2_after <= tolerance, axis=2)
        matches_after = matches1_after | matches2_after

        mid_x = (config.SCROLL_AREA_RIGHT - config.SCROLL_AREA_LEFT) // 2
        matching_ys_after = np.where(matches_after[:, mid_x])[0]

        if len(matching_ys_after) > 0:
            # Find largest contiguous group
            groups_after = []
            current_group_after = [matching_ys_after[0]]
            for i in range(1, len(matching_ys_after)):
                if matching_ys_after[i] - matching_ys_after[i-1] <= 2:
                    current_group_after.append(matching_ys_after[i])
                else:
                    groups_after.append(current_group_after)
                    current_group_after = [matching_ys_after[i]]
            groups_after.append(current_group_after)

            largest_group_after = max(groups_after, key=len)
            if len(largest_group_after) >= 10:
                found_y_bottom_after = int(np.max(largest_group_after))
                absolute_y_bottom_after = found_y_bottom_after + config.SCROLL_AREA_TOP

                # Check if now at bottom
                end_min = getattr(config, 'SCROLLBAR_END_MIN', 930)
                end_max = getattr(config, 'SCROLLBAR_END_MAX', 1021)
                if absolute_y_bottom_after >= end_min and absolute_y_bottom_after <= end_max:
                    log_print(f"  ✓ [END] Scrollbar reached bottom after drag (Y={absolute_y_bottom_after})")
                    return "END"

        return "SCROLLED"


    def scan_rows_block(self, rows_per_block, row_step, tile_height, skip_rows=0):
        """
        Scans a block with variable row count (8 for 1x1, 4 for 1x2).

        Args:
            rows_per_block: Number of rows per block (8 or 4)
            row_step: Distance between rows in px (97 or 180)
            tile_height: Height of tiles in px (86 or 170)
            skip_rows: Number of rows to skip at the start (for overlap handling)

        Returns:
            int: Number of consecutive empty items (for abort logic), or -1 if items found
        """
        found = 0
        consecutive_empty_items = 0  # Counter for consecutive empty items

        items_found_this_block = 0   # Track items found in this block


        # 1. Calculate base Y (start point + offset to center of first row)
        # Y-offset = center of tile
        first_row_y_offset = tile_height // 2
        base_y = config.START_Y + first_row_y_offset

        # 2. Calculate and apply drift compensation (mouse moves upward)
        drift_val = int(config.DRIFT_COMPENSATION_PER_BLOCK)
        drift_correction = int(self.block_counter * drift_val)
        base_y -= drift_correction

        if skip_rows > 0:
            log_print(f"  Block {self.block_counter + 1}: {rows_per_block} rows, {row_step}px step, drift -{drift_correction}px, skip {skip_rows} rows")
        else:
            log_print(f"  Block {self.block_counter + 1}: {rows_per_block} rows, {row_step}px step, drift -{drift_correction}px")

        # 3. Dynamic row_offsets based on scan mode

        # Start from skip_rows to avoid scanning duplicate rows
        row_offsets = [i * row_step for i in range(skip_rows, skip_rows + rows_per_block)]
        row_offsets = [i * row_step for i in range(rows_per_block)]

        for row_idx, offset in enumerate(row_offsets):
            self.check_abort()
            row_y = base_y + offset

            if row_y < 0:
                log_print(f"  [WARNING] Y-coordinate {row_y} < 0! Skipped.")
                continue

            # Check if row_y is outside inventory bounds (would trigger failsafe)
            if row_y > config.INVENTORY_BOTTOM:
                log_print(f"  [WARNING] Y-coordinate {row_y} > INVENTORY_BOTTOM ({config.INVENTORY_BOTTOM})! Skipped.")
                continue

            # Calculate absolute row number (1-based)
            # Add skip_rows to account for skipped rows at start of block
            self.current_row = (self.block_counter * rows_per_block) + skip_rows + row_idx + 1

            for col in range(config.MAX_COLUMNS):
                self.check_abort()

                # Track current column (1-based)
                self.current_col = col + 1

                # Calculate X-coordinate
                x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
                y = row_y

                # FAST DEBUG MODE: Skip OCR, just move mouse and count
                if getattr(config, 'FAST_DEBUG_MODE', False):
                    pyautogui.moveTo(x, y, duration=0.1)
                    time.sleep(0.25)  # Wait so you can see what's happening
                    # Simulate finding an item (count but don't OCR)
                    text = f"DEBUG_ITEM_{self.current_row}_{col+1}"
                    self.detected_items[text] += 1
                    items_found_this_block += 1
                    found += 1
                    consecutive_empty_items = 0
                    continue


                # Adaptive retry logic:
                # - 5 attempts when OCR detects text but no DB match
                # - 2 attempts when OCR detects no text at all
                text = ""
                raw_ocr = ""
                max_attempts = 2  # Start with 2 (for "no text")

                for attempt in range(1, 6):  # Max 5 attempts possible
                    self.check_abort()

                    # Very short movement (20ms) so game detects mouse event
                    pyautogui.moveTo(x, y, duration=0.02)

                    # Wiggle: Briefly move up and down to trigger tooltip
                    self.check_abort()
                    pyautogui.moveRel(0, -3, duration=0.02)  # 3px up
                    time.sleep(0.05)
                    self.check_abort()
                    pyautogui.moveRel(0, 3, duration=0.02)   # 3px down (back)

                    # Check multiple times during wait
                    for _ in range(8):
                        self.check_abort()
                        time.sleep(0.025)  # 8 x 0.025 = 0.2s (reduced because of wiggle)

                    # Screenshot of OCR region
                    self.check_abort()
                    shot = pyautogui.screenshot(region=(
                        config.OCR_LEFT, config.OCR_TOP,
                        config.OCR_WIDTH, config.OCR_HEIGHT
                    ))

                    # OCR now returns tuple: (corrected_text, raw_text, was_corrected)
                    scan_result = ocr_scanner.scan_image_for_text(shot)
                    text = scan_result[0].strip()
                    raw_ocr = scan_result[1]

                    # IMPORTANT: Check right after OCR, as OCR takes long (100-300ms)
                    self.check_abort()

                    if text:
                        if attempt > 1:
                            log_print(f"    [RETRY] Text found after {attempt} attempts")
                        break
                    elif raw_ocr:
                        if max_attempts < 5:
                            max_attempts = 5
                            log_print(f"    [RETRY] OCR text found but no DB match → max attempts: 5")

                        if attempt < max_attempts:
                            log_print(f"    [RETRY] {attempt}/{max_attempts}: No DB match for '{raw_ocr}'")
                        else:
                            log_print(f"    [FAILED] OCR: '{raw_ocr}' - No DB match after {max_attempts} attempts")
                            # Track unmatched OCR text with position (page, row, column)
                            if raw_ocr not in self.not_detected_items:
                                self.not_detected_items[raw_ocr] = []
                            self.not_detected_items[raw_ocr].append((self.current_page, self.current_row, self.current_col))
                            break
                    else:
                        if attempt < max_attempts:
                            log_print(f"    [RETRY] {attempt}/{max_attempts}: No text")
                        else:
                            log_print(f"    [RETRY] All {max_attempts} attempts failed - empty slot")
                            break

                pyautogui.moveTo(100, 100, duration=0)  # Move mouse out of way instantly

                if text:
                    self.detected_items[text] += 1  # Count each item (including duplicates)
                    count = self.detected_items[text]
                    # In Fast Debug Mode, don't spam log with every item
                    if not getattr(config, 'FAST_DEBUG_MODE', False):
                        log_print(f"  → {text} (#{count})")
                    found += 1
                    consecutive_empty_items = 0  # Reset on find
                elif raw_ocr:
                    # OCR detected text but no DB match → continue anyway
                    consecutive_empty_items = 0  # Reset, since not really empty
                else:
                    # Completely empty (no OCR text) → Check for next page button
                    consecutive_empty_items += 1
                    log_print(f"  [EMPTY] Checking for next page...")
                    button_active = self.check_button_brightness()

                    if not button_active:
                        log_print(f"  [INACTIVE] No more pages → Ending scan")
                        return 999
                    else:
                        log_print(f"  [ACTIVE] More pages available → Continuing")

        return -1 if found > 0 else consecutive_empty_items

    def scan_last_row(self, tile_height=86):
        """
        Scans only the last row (row 25).

        Args:
            tile_height: Tile height in px (86 or 170)

        Returns:
            int: Number of consecutive empty items, or -1 if items found
        """
        log_print("\n=== SCANNING LAST ROW (25) ===")

        row_y = config.INVENTORY_BOTTOM - config.BORDER_OFFSET_TOP - (tile_height // 2)
        log_print(f"  Scanning at Y={row_y} (tile height: {tile_height}px)")

        found = 0
        consecutive_empty_items = 0

        # Set row number to 25 (last row)
        self.current_row = 25

        for col in range(config.MAX_COLUMNS):
            self.check_abort()

            # Track current column (1-based)
            self.current_col = col + 1

            x = config.START_X + config.HOVER_OFFSET_X + col * (config.TILE_WIDTH + config.TILE_SPACING)
            y = row_y

            # FAST DEBUG MODE: Skip OCR, just move mouse and count
            if getattr(config, 'FAST_DEBUG_MODE', False):
                pyautogui.moveTo(x, y, duration=0.1)
                time.sleep(0.25)  # Wait so you can see what's happening
                # Simulate finding an item (count but don't OCR)
                text = f"DEBUG_ITEM_{self.current_row}_{col+1}"
                found += 1
                consecutive_empty_items = 0
                self.detected_items[text] += 1
                continue

            # Adaptive Retry-Logik (wie in scan_8_rows_block)
            text = ""
            raw_ocr = ""
            max_attempts = 2

            for attempt in range(1, 6):
                self.check_abort()

                pyautogui.moveTo(x, y, duration=0.02)

                # Wiggle
                self.check_abort()
                pyautogui.moveRel(0, -3, duration=0.02)
                time.sleep(0.05)
                self.check_abort()
                pyautogui.moveRel(0, 3, duration=0.02)

                for _ in range(8):
                    self.check_abort()
                    time.sleep(0.025)

                # Screenshot
                self.check_abort()
                shot = pyautogui.screenshot(region=(
                    config.OCR_LEFT, config.OCR_TOP,
                    config.OCR_WIDTH, config.OCR_HEIGHT
                ))

                scan_result = ocr_scanner.scan_image_for_text(shot)
                text = scan_result[0].strip()
                raw_ocr = scan_result[1]

                self.check_abort()

                if text:
                    if attempt > 1:
                        log_print(f"    [RETRY] Text found after {attempt} attempts")
                    break
                elif raw_ocr:
                    if max_attempts < 5:
                        max_attempts = 5
                        log_print(f"    [RETRY] OCR text found but no DB match → max attempts: 5")

                    if attempt < max_attempts:
                        log_print(f"    [RETRY] {attempt}/{max_attempts}: No DB match for '{raw_ocr}'")
                    else:
                        log_print(f"    [FAILED] OCR: '{raw_ocr}' - No DB match after {max_attempts} attempts")
                        # Track unmatched OCR text with position (page, row, column)
                        if raw_ocr not in self.not_detected_items:
                            self.not_detected_items[raw_ocr] = []
                        self.not_detected_items[raw_ocr].append((self.current_page, self.current_row, self.current_col))
                        break
                else:
                    if attempt < max_attempts:
                        log_print(f"    [RETRY] {attempt}/{max_attempts}: No text")
                    else:
                        log_print(f"    [RETRY] All {max_attempts} attempts failed - empty slot")
                        break

            pyautogui.moveTo(100, 100, duration=0)

            if text:
                self.detected_items[text] += 1
                count = self.detected_items[text]
                log_print(f"  → {text} (#{count})")
                found += 1
                consecutive_empty_items = 0  # Reset on find
            elif raw_ocr:
                # OCR detected text but no DB match → continue anyway
                consecutive_empty_items = 0  # Reset, since not really empty
            else:
                # Completely empty (no OCR text) → Check for next page button
                consecutive_empty_items += 1
                log_print(f"  [EMPTY] Checking for next page...")
                button_active = self.check_button_brightness()

                if not button_active:
                    log_print(f"  [INACTIVE] No more pages → Ending scan")
                    return 999
                else:
                    log_print(f"  [ACTIVE] More pages available → Continuing")

        return -1 if found > 0 else consecutive_empty_items

    def write_not_detected(self):
        """Writes OCR text that couldn't be matched to database to not_detected.md"""
        if not self.not_detected_items:
            return

        not_detected_file = "not_detected.md"

        try:
            # Read existing items if file exists
            existing_items = {}  # {text: [(page, row, col), ...]}
            if os.path.exists(not_detected_file):
                try:
                    with open(not_detected_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and not line.startswith('---'):
                                # Parse line format: "Item Name - Page X, Row Y, Col Z; Page X, Row Y, Col Z"
                                if ' - ' in line:
                                    parts = line.split(' - ', 1)
                                    item_name = parts[0].strip()
                                    positions_str = parts[1].strip()

                                    positions = []
                                    for pos_str in positions_str.split('; '):
                                        if 'Page' in pos_str and 'Row' in pos_str:
                                            try:
                                                # Extract page, row, and col numbers
                                                pos_parts = pos_str.split(',')
                                                page_part = pos_parts[0].strip()
                                                row_part = pos_parts[1].strip()

                                                page = int(page_part.replace('Page', '').strip())
                                                row = int(row_part.replace('Row', '').strip())

                                                # Check if column exists (new format)
                                                if len(pos_parts) >= 3 and 'Col' in pos_parts[2]:
                                                    col_part = pos_parts[2].strip()
                                                    col = int(col_part.replace('Col', '').strip())
                                                    positions.append((page, row, col))
                                                else:
                                                    # Old format without column
                                                    positions.append((page, row, 0))
                                            except:
                                                pass

                                    if positions:
                                        existing_items[item_name] = positions
                                else:
                                    # Old format without positions
                                    existing_items[line] = []
                except Exception as e:
                    log_print(f"[WARNING] Could not read existing not_detected.md: {e}")

            # Merge with new items
            for item_name, positions in self.not_detected_items.items():
                if item_name in existing_items:
                    # Add new positions, avoiding exact duplicates
                    for pos in positions:
                        if pos not in existing_items[item_name]:
                            existing_items[item_name].append(pos)
                else:
                    existing_items[item_name] = positions

            # Write sorted list
            with open(not_detected_file, 'w', encoding='utf-8') as f:
                f.write("# Items detected by OCR but not matched to database\n")
                f.write("# These items may need to be added to inventory.db\n")
                f.write("# Format: Item Name - Page X, Row Y, Col Z; Page X, Row Y, Col Z\n\n")

                for item_name in sorted(existing_items.keys()):
                    positions = existing_items[item_name]
                    if positions:
                        # Sort positions by page, then row, then col
                        positions.sort()
                        positions_str = '; '.join([f"Page {p}, Row {r}, Col {c}" for p, r, c in positions])
                        f.write(f"{item_name} - {positions_str}\n")
                    else:
                        f.write(f"{item_name}\n")

            new_count = len(self.not_detected_items)
            total_count = len(existing_items)
            log_print(f"[NOT DETECTED] {new_count} new unmatched items ({total_count} total)")
            log_print(f"[NOT DETECTED] Saved to {not_detected_file}")
        except Exception as e:
            log_print(f"[ERROR] Could not write not_detected.md: {e}")

    def write_results(self):
        """Writes final results in format: count, item_name"""
        if not self.detected_items:
            return

        try:
            with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # Sort items by name
                for item_name in sorted(self.detected_items.keys()):
                    count = self.detected_items[item_name]
                    f.write(f"{count}, {item_name}\n")

            total_items = sum(self.detected_items.values())

            # In Fast Debug Mode, skip writing debug items to file
            if getattr(config, 'FAST_DEBUG_MODE', False):
                log_print(f"\n>>> FAST DEBUG MODE RESULTS <<<")
                log_print(f">>> Total items counted: {total_items} <<<")
            else:
                with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    # Sort items by name
                    for item_name in sorted(self.detected_items.keys()):
                        count = self.detected_items[item_name]
                        f.write(f"{count}, {item_name}\n")

                log_print(f"\n[RESULTS] {total_items} items scanned ({len(self.detected_items)} unique)")
                log_print(f"[RESULTS] Saved to {config.OUTPUT_FILE}")
        except Exception as e:
            log_print(f"[ERROR] Could not write results: {e}")

        # Write not detected items
        self.write_not_detected()

    def test_scroll_calculation(self, max_scrolls=10):
        """
        TEST MODE: Only tests scrolling and calculation without OCR scanning.
        Scrolls down multiple times and logs the calculated distances.

        Args:
            max_scrolls: Maximum number of scrolls to perform (default: 10)
        """
        log_print("\n" + "="*80)
        log_print("🧪 SCROLL CALCULATION TEST MODE")
        log_print("="*80)
        log_print("This will only test scrolling without scanning items.")
        log_print(f"Max scrolls: {max_scrolls}")
        log_print("Press DELETE to abort at any time.")
        log_print("="*80 + "\n")

        self.scan_active = True
        scroll_count = 0

        try:
            self.reset_to_top()
            log_print("\n✓ Ready to test scrolling\n")

            while self.scan_active and scroll_count < max_scrolls:
                scroll_count += 1
                log_print(f"\n{'='*80}")
                log_print(f"SCROLL TEST #{scroll_count}/{max_scrolls}")
                log_print(f"{'='*80}\n")

                self.check_abort()

                # Perform scroll with dynamic calculation
                scroll_result = self.precise_scroll_down_once()

                if scroll_result == "END":
                    log_print("\n✓ [END] Reached bottom of scrollbar")
                    break
                elif scroll_result == "NO_SCROLLBAR":
                    log_print("\n✓ [NO_SCROLLBAR] No scrollbar found (all items visible?)")
                    break
                else:
                    log_print(f"✓ Scroll #{scroll_count} completed")

                # Wait a bit before next scroll
                log_print("Waiting 1 second before next scroll...")
                for _ in range(10):
                    self.check_abort()
                    time.sleep(0.1)

            log_print("\n" + "="*80)
            log_print(f"🧪 TEST COMPLETED: {scroll_count} scrolls performed")
            log_print("="*80 + "\n")

        except ScanAbortedException:
            log_print(f"\n⚠️ Test aborted after {scroll_count} scrolls")

        finally:
            self.scan_active = False
            pyautogui.moveTo(100, 100, duration=0)
            log_print("Mouse stopped")

    def scan_all_tiles(self, scan_mode=1):
        """
        Scans all inventory tiles.

        Args:
            scan_mode: 1 for 1x1 items (default), 2 for 1x2 items (undersuits)
        """
        Scans all inventory tiles.

        Args:
            scan_mode: 1 for 1x1 items (default), 2 for 1x2 items (undersuits)
        """
        # Set parameters based on mode
        if scan_mode == 2:
            # 1x2 mode (undersuits)
            rows_per_block = 4
            row_step = 180  # 170px item + 10px spacing
            total_blocks = 6
            tile_height = 170
            # Scroll distance for 4 rows (based on tests)
            # 360px = 9 rows → 160px for 4 rows
            scroll_pixels = 160
            mode_name = "1x2 (Undersuits)"
        else:
            # 1x1 mode (default)
            rows_per_block = 8
            row_step = 97  # 86px item + 10px spacing + 1px
            total_blocks = 3
            tile_height = 86
            scroll_pixels = 322  # Original SCROLL_PIXELS_UP for 8 rows
            mode_name = "1x1 (Normal)"

        log_print("\n" + "="*80)
        log_print(f"SCAN STARTED - Mode: {mode_name}")
        log_print(f"Rows/Block: {rows_per_block} | Step: {row_step}px | Blocks: {total_blocks}")
        log_print("="*80 + "\n")

        self.scan_active = True
        scan_iteration = 0  # Counter for scan iterations

        try:
            self.reset_to_top()

            # FAST DEBUG MODE: Show estimated rows and wait 1 second
            if getattr(config, 'FAST_DEBUG_MODE', False):
                if hasattr(self, 'total_rows_estimated') and self.total_rows_estimated:
                    import math
                    rounded = math.ceil(self.total_rows_estimated)
                    log_print(f"\n>>> FAST DEBUG MODE ACTIVE <<<")
                    log_print(f">>> Estimated rows: {self.total_rows_estimated:.1f} (rounded: {rounded}) <<<\n")
                    time.sleep(1)

            while self.scan_active:
                scan_iteration += 1
                self.current_page = scan_iteration  # Track current page for not_detected
                log_print(f"\n{'='*80}")
                log_print(f"PAGE #{scan_iteration}")
                log_print(f"{'='*80}\n")

                scan_complete = False

                # Reset block_counter at the start of each page
                self.block_counter = 0

                for block_num in range(total_blocks):
                    self.check_abort()

                    # Calculate how many rows to scan in this block
                    # For dynamic scanning, use total_rows_estimated if available
                    rows_to_scan = rows_per_block
                    skip_rows = 0  # Number of rows to skip at start of block

                    if hasattr(self, 'total_rows_estimated') and self.total_rows_estimated:
                        rows_scanned_so_far = block_num * rows_per_block
                        # Round up to avoid missing rows due to measurement variance
                        import math
                        total_rows_rounded = math.ceil(self.total_rows_estimated)
                        rows_remaining = total_rows_rounded - rows_scanned_so_far

                        if rows_remaining < rows_per_block:
                            rows_to_scan = max(1, rows_remaining)  # Scan at least 1 row

                            # Calculate overlap: After scroll, viewport shows 8 rows, but we only need to scan N remaining
                            # The first (8 - N) rows are duplicates from previous block
                            visible_rows = config.VISIBLE_ROWS
                            if rows_remaining < visible_rows:
                                skip_rows = visible_rows - rows_remaining
                                log_print(f"\n=== SCANNING BLOCK {self.block_counter + 1} (Last {rows_to_scan} rows, skipping first {skip_rows}) ===")
                            else:
                                log_print(f"\n=== SCANNING BLOCK {self.block_counter + 1} (Last {rows_to_scan} rows) ===")
                        else:
                            log_print(f"\n=== SCANNING BLOCK {self.block_counter + 1} ===")
                    else:
                        log_print(f"\n=== SCANNING BLOCK {self.block_counter + 1} ===")

                    scan_result = self.scan_rows_block(rows_to_scan, row_step, tile_height, skip_rows)

                    if scan_result == 999:
                        log_print(f"[END] Button inactive → Scan complete")
                        scan_complete = True
                        break

                    if scan_result == -1:
                        log_print("  Items found")
                    else:
                        log_print(f"  {scan_result} empty slots (button active)")

                    # Check if we should scroll to next block
                    if block_num < (total_blocks - 1):
                        self.check_abort()
                        scroll_result = self.precise_scroll_down_once()  # Use dynamic calculation

                        # Check for scroll completion conditions
                        # If no scrollbar found, end scan
                        if scroll_result == "NO_SCROLLBAR":
                            log_print("[NO_SCROLLBAR] No scrollbar detected - all items scanned in first block")
                            scan_complete = True
                            break  # Exit immediately - no more blocks to scan
                        elif scroll_result == "END":
                            log_print("[END] Scrollbar at bottom - will scan last block with overlap handling")
                            scan_complete = True
                            # Don't break - scan next block with skip_rows to handle overlap

                if scan_complete:
                    # After last block scan, exit the loop
                    log_print("[INFO] Last block scanned, ending page scan")
                    break

                # Only scroll to row 25 if we actually have 25 rows
                # Skip this section if scrollbar was not found (8 rows or less)
                if not hasattr(self, 'total_rows_estimated') or self.total_rows_estimated >= 24:
                    log_print("\n→ Scrolling to last row...")
                    self.check_abort()

                    cx = (config.SCROLL_AREA_LEFT + config.SCROLL_AREA_RIGHT) // 2
                    cy = config.SCROLL_AREA_BOTTOM - 100

                    small_scroll = scroll_pixels // rows_per_block
                    log_print(f"  Scrolling {small_scroll}px down (1 row)")

                    pyautogui.moveTo(cx, cy, duration=0)
                    pyautogui.drag(0, small_scroll, duration=0.2, button='left')
                    time.sleep(0.3)

                    last_row_result = self.scan_last_row(tile_height)
                    if last_row_result == 999:
                        log_print(f"[END] Button inactive in row 25 → Scan complete")
                        break

                log_print("\n→ Final button check...")
                self.check_abort()

                button_active = self.check_button_brightness()

                if button_active:
                    log_print("[ACTIVE] Clicking next page button")

                    button_center_x = 1612
                    button_center_y = 1040

                    pyautogui.click(button_center_x, button_center_y)

                    log_print("  Waiting 5s for inventory to load...")
                    for _ in range(50):
                        self.check_abort()
                        time.sleep(0.1)

                    log_print("  Ready for next page\n")

                else:
                    log_print("[INACTIVE] No more pages → Scan complete")
                    break

            log_print("\nScan finished!")

        except ScanAbortedException:
            # Normal handling for DELETE abort
            pass

        finally:
            self.scan_active = False
            pyautogui.moveTo(100, 100, duration=0)
            log_print("Mouse stopped")

            self.write_results()