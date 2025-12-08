# -*- coding: utf-8 -*-
"""
test_scroll.py - Test script for dynamic scroll calculation
Only scrolls down without OCR scanning to verify scroll distances.
"""
import keyboard
import time
import os
from inventory_detector import InventoryScanner, ScanAbortedException
import config
import pyautogui
import win32gui
import win32con
import win32process
import psutil

# Reset log file
if os.path.exists(config.LOG_FILE):
    try:
        os.remove(config.LOG_FILE)
    except:
        pass

def log_print(*args, **kwargs):
    msg = " ".join(map(str, args))
    print(msg, **kwargs)
    try:
        with open(config.LOG_FILE, "a", encoding="utf-8", buffering=1) as f:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

def switch_to_star_citizen():
    """
    Switches to the Star Citizen window by finding StarCitizen.exe process.
    Returns True if successful, False if process/window not found.
    """
    log_print("\n[WINDOW] Searching for StarCitizen.exe process...")

    # First, check if StarCitizen.exe process is running
    sc_process = None
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == 'starcitizen.exe':
                sc_process = proc
                log_print(f"[WINDOW] Found StarCitizen.exe (PID: {proc.info['pid']})")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if not sc_process:
        log_print("[WINDOW] StarCitizen.exe is not running!")
        log_print("[WINDOW] Please start Star Citizen first.")
        return False

    # Now find the window belonging to StarCitizen.exe
    hwnd = None
    found_title = None

    def enum_windows_callback(window_hwnd, _):
        nonlocal hwnd, found_title
        try:
            if win32gui.IsWindowVisible(window_hwnd):
                # Get the process ID of this window
                _, window_pid = win32process.GetWindowThreadProcessId(window_hwnd)

                # Check if this window belongs to StarCitizen.exe
                if window_pid == sc_process.pid:
                    window_title = win32gui.GetWindowText(window_hwnd)
                    # Only main windows have titles
                    if window_title:
                        hwnd = window_hwnd
                        found_title = window_title
        except:
            pass
        return True  # Always continue enumeration

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except:
        pass  # Ignore EnumWindows errors

    if hwnd:
        try:
            # Bring window to foreground
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # Restore if minimized
            win32gui.SetForegroundWindow(hwnd)
            log_print(f"[WINDOW] Switched to: {found_title}")
            time.sleep(0.5)  # Wait for window to be in focus
            return True
        except Exception as e:
            log_print(f"[WINDOW] Error switching to window: {e}")
            return False
    else:
        log_print("[WINDOW] Star Citizen window not found (process is running but no window)!")
        return False

def main():
    log_print("\n" + "="*80)
    log_print("🧪 SCROLL CALCULATION TEST - InvDetect")
    log_print("="*80)
    log_print("This script only tests scrolling WITHOUT scanning items.")
    log_print("It will scroll down multiple times and log the calculated distances.")
    log_print("")
    log_print("Controls:")
    log_print("  INSERT → Start test")
    log_print("  DELETE → Stop test")
    log_print("  ESC    → Exit")
    log_print("="*80 + "\n")

    # Get max scrolls from command line (optional)
    import sys
    max_scrolls = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    log_print(f"[INFO] Max scrolls per test: {max_scrolls}")
    log_print(f"[INFO] Debug mode: {config.DEBUG_SCROLL_CALCULATION}")
    log_print(f"[INFO] Correction factor: {config.SCROLL_CORRECTION_FACTOR}")

    # Main loop - allows multiple tests
    while True:
        log_print("\nPress INSERT to start test, or ESC to exit...")

        # Wait for INSERT or ESC
        while True:
            if keyboard.is_pressed('insert'):
                break
            if keyboard.is_pressed('esc'):
                log_print("\n[EXIT] ESC pressed - Exiting test...")
                time.sleep(1)
                return
            time.sleep(0.05)

        time.sleep(0.3)

        # Switch to Star Citizen window before starting test
        if not switch_to_star_citizen():
            log_print("\n[ERROR] Cannot start test without Star Citizen window.")
            log_print("[ERROR] Please start Star Citizen and open Universal Inventory...")
            time.sleep(3)
            continue  # Back to waiting for INSERT

        scanner = InventoryScanner()

        try:
            scanner.test_scroll_calculation(max_scrolls)
            log_print("\n✅ TEST COMPLETE! Check scan_log.txt for details.")

        except (KeyboardInterrupt, ScanAbortedException):
            log_print("\n⚠️ Test aborted (DELETE pressed).")

        except pyautogui.FailSafeException:
            log_print("\n⚠️ PyAutoGUI Fail-Safe triggered (mouse moved to screen corner)")
            log_print("Test aborted.")

        except Exception as e:
            log_print(f"\n❌ UNEXPECTED ERROR: {e}")
            import traceback
            log_print(traceback.format_exc())
            log_print("\nPress INSERT to try again, or ESC to exit...")
            time.sleep(2)

        # After test, wait a moment before next test
        log_print("\n" + "="*80)
        time.sleep(1)

if __name__ == "__main__":
    main()
