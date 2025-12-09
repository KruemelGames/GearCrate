# -*- coding: utf-8 -*-
# Enable DPI-Awareness for correct coordinates with Windows scaling
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    print("[WARNING] Could not enable DPI-Awareness - coordinates may be incorrect with Windows scaling")

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
if os.path.exists(config.OUTPUT_FILE):
    try:
        os.remove(config.OUTPUT_FILE)
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
        return True  # Always continue enumeration (returning False causes error)

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
    log_print("\n=== InvDetect - Star Citizen Universal Inventory Scanner ===")
    log_print("INSERT → Start Scan | DELETE → Stop | ESC → Exit\n")

    # Get scan mode from command line argument (passed by GearCrate)
    import sys
    scan_mode = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # Default to 1 (1x1) if not provided
    mode_name = "1x2 (Undersuits)" if scan_mode == 2 else "1x1 (Normal)"

    log_print(f"\n[INFO] Scan mode: {mode_name}")

    # Main loop - allows multiple scans
    while True:
        log_print("\nPress INSERT to start scan, or ESC to exit...")

        # Wait for INSERT or ESC
        while True:
            if keyboard.is_pressed('insert'):
                break
            if keyboard.is_pressed('esc'):
                # Only exit if scanner window is in focus (not Star Citizen)
                try:
                    hwnd = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(hwnd)
                    # Check if current window is NOT Star Citizen
                    if "star citizen" not in window_title.lower():
                        log_print("\n[EXIT] ESC pressed - Exiting scanner...")
                        time.sleep(1)
                        return
                except:
                    # If check fails, allow exit anyway
                    log_print("\n[EXIT] ESC pressed - Exiting scanner...")
                    time.sleep(1)
                    return
            time.sleep(0.05)

        time.sleep(0.3)

        # Switch to Star Citizen window before starting scan
        if not switch_to_star_citizen():
            log_print("\n[ERROR] Cannot start scan without Star Citizen window.")
            log_print("[ERROR] Please start Star Citizen and try again...")
            time.sleep(3)
            continue  # Back to waiting for INSERT

        scanner = InventoryScanner()

        try:
            scanner.scan_all_tiles(scan_mode)
            log_print("\n✅ SCAN COMPLETE! See detected_items.txt")

        except (KeyboardInterrupt, ScanAbortedException):
            log_print("\n⚠️ Scan aborted (DELETE pressed).")
            log_print("Partial results saved.")

        except pyautogui.FailSafeException:
            log_print("\n⚠️ PyAutoGUI Fail-Safe triggered (mouse moved to screen corner)")
            log_print("Scan aborted.")

        except Exception as e:
            log_print(f"\n❌ UNEXPECTED ERROR: {e}")
            import traceback
            log_print(traceback.format_exc())
            log_print("\nPress INSERT to try again, or ESC to exit...")
            time.sleep(2)

        # After scan (successful or aborted), wait a moment before next scan
        log_print("\n" + "="*60)
        time.sleep(1)

if __name__ == "__main__":
    main()