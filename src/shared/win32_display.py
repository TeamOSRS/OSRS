"""
OSRS Win32 Desktop & Window Focus Management
============================================
Ensures that native GUI windows (e.g., MuJoCo GLFW viewer, OpenCV highgui)
spawn onto the user's interactive desktop ('Default') even when the server or
parent script was started by a background service, daemon, or sandbox runner.
"""

import sys
import time

def ensure_interactive_desktop():
    """
    On Windows, attaches current thread and hooks threading.Thread.run
    so that all subsequent threads (including GLFW render threads) attach to
    the interactive desktop ('Default').
    """
    if sys.platform != 'win32':
        return
    import ctypes
    import threading

    user32 = ctypes.windll.user32
    try:
        hdesk = user32.OpenDesktopW('Default', 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

    if not getattr(threading.Thread, '_osrs_interactive_patched', False):
        orig_run = threading.Thread.run

        def _patched_run(self, *args, **kwargs):
            try:
                hdesk = user32.OpenDesktopW('Default', 0, False, 0x01FF)
                if hdesk:
                    user32.SetThreadDesktop(hdesk)
            except Exception:
                pass
            return orig_run(self, *args, **kwargs)

        threading.Thread.run = _patched_run
        threading.Thread._osrs_interactive_patched = True


def show_and_focus_window(title_substr="MuJoCo", timeout=5.0):
    """
    Polls for a visible top-level window whose title matches `title_substr`
    and restores/brings it to the foreground on Windows.
    """
    if sys.platform != 'win32':
        return False
    import ctypes

    user32 = ctypes.windll.user32
    try:
        hdesk = user32.OpenDesktopW('Default', 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        hdesk = None

    deadline = time.time() + timeout
    found_hwnd = None

    while time.time() < deadline:
        found = []

        @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
        def _enum_proc(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    if title_substr.lower() in buf.value.lower():
                        found.append(hwnd)
                        return 0
            return 1

        if hdesk:
            user32.EnumDesktopWindows(hdesk, _enum_proc, 0)
        else:
            user32.EnumWindows(_enum_proc, 0)

        if found:
            found_hwnd = found[0]
            break
        time.sleep(0.08)

    if found_hwnd:
        SW_RESTORE = 9
        SW_SHOW = 5
        user32.ShowWindow(found_hwnd, SW_RESTORE)
        user32.ShowWindow(found_hwnd, SW_SHOW)
        user32.BringWindowToTop(found_hwnd)
        user32.SetForegroundWindow(found_hwnd)
        return True

    return False
