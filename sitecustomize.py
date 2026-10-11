"""
OSRS Global Site Customization
==============================
Automatically ensures that child processes started within the OSRS ecosystem
attach their threads to the interactive Windows desktop ('Default').
"""
import sys

if sys.platform == 'win32':
    try:
        import ctypes
        import threading
        u32 = ctypes.windll.user32
        
        def _attach_default_desktop():
            try:
                h = u32.OpenDesktopW('Default', 0, False, 0x01FF)
                if h:
                    u32.SetThreadDesktop(h)
            except Exception:
                pass
                
        _attach_default_desktop()
        
        if not getattr(threading.Thread, '_osrs_desktop_patched', False):
            _orig_run = threading.Thread.run
            def _patched_run(self, *args, **kwargs):
                _attach_default_desktop()
                return _orig_run(self, *args, **kwargs)
            threading.Thread.run = _patched_run
            threading.Thread._osrs_desktop_patched = True
    except Exception:
        pass
