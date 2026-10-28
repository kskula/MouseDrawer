#!/usr/bin/env python3
"""
Self-test rysowania: uruchamia PRAWDZIWE okno overlay i PRAWDZIWE rysowanie GDI,
ale wejscie (CTRL/LMB/kursor) jest skryptowane - nie dotyka pulpitu uzytkownika.

Sprawdza:
  1) ile okien utworzyla aplikacja (ma byc dokladnie JEDNO)
  2) czy rysowanie tworzy segmenty (drawing)
  3) czy puszczenie CTRL czysci rysunek (reset)

Uruchom:  python tests/selftest_drawing.py
"""

import os
import sys
import threading
import time
import ctypes as ctypes_mod
from ctypes import wintypes, byref

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import screen_drawer_window as m  # noqa: E402

# sciezka kreski (coraz dalej od punktu startu)
POSITIONS = [(300, 300), (360, 340), (420, 310), (480, 380), (540, 420),
             (600, 460), (660, 430), (720, 500), (780, 540), (840, 600),
             (900, 560), (960, 620)]

TICKS_HOLD = 12   # CTRL+LMB trzymane przez tyle tickow
TICK_LMB_START = 3


class ScriptedWindow(m.DrawOverlayWindow):
    """Overlay ze skryptowanym wejsciem."""

    def __init__(self):
        super().__init__()
        self.t = 0
        self.max_segments = 0
        self.paint_calls = 0

    def _is_esc_down(self):
        return False

    def _is_ctrl_down(self):
        self.t += 1
        return 1 <= self.t <= TICKS_HOLD

    def _is_lmb_down(self):
        return TICK_LMB_START <= self.t <= TICKS_HOLD

    def _cursor_pos(self):
        i = min(max(self.t - TICK_LMB_START, 0), len(POSITIONS) - 1)
        return POSITIONS[i]

    def _on_timer(self):
        changed = super()._on_timer()
        self.max_segments = max(self.max_segments, len(self.segments))
        return changed

    def _paint(self):
        self.paint_calls += 1
        super()._paint()


def count_own_windows(pid):
    """Liczy widoczne okna najwyzszego poziomu nalezace do tego procesu."""
    found = []
    WNDENUMPROC = ctypes_mod.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        wpid = wintypes.DWORD()
        m.user32.GetWindowThreadProcessId(hwnd, byref(wpid))
        if wpid.value == pid:
            found.append((hwnd, m.user32.IsWindowVisible(hwnd)))
        return True

    m.user32.EnumWindows(WNDENUMPROC(cb), 0)
    return found


app = ScriptedWindow()
exit_code = {}


def watchdog():
    time.sleep(2.0)
    allw = count_own_windows(os.getpid())
    # liczymy tylko WIDOCZNE okna - systemowe okna IME (MSCTFIME UI, IME) sa niewidoczne
    windows = [w for w in allw if w[1]]
    classes = []
    for hwnd, visible in allw:
        buf = ctypes_mod.create_unicode_buffer(256)
        m.user32.GetClassNameW(hwnd, buf, 256)
        classes.append((buf.value, bool(visible)))

    # od v0.2 jest jedno okno overlay na monitor - nie zakladamy "1"
    expected = len(getattr(app, "monitors", [])) or 1
    ok_windows = len(windows) == expected
    ok_draw = app.max_segments >= 2
    ok_reset = len(app.segments) == 0
    ok_paint = app.paint_calls >= 2

    print(f"[SELFTEST] okien={len(windows)} klasy={classes}")
    print(f"[SELFTEST] ticks={app.t} max_segments={app.max_segments} "
          f"final_segments={len(app.segments)} paint_calls={app.paint_calls}")
    print(f"[SELFTEST] one_window={'PASS' if ok_windows else 'FAIL'} "
          f"drawing={'PASS' if ok_draw else 'FAIL'} "
          f"reset={'PASS' if ok_reset else 'FAIL'} "
          f"paint={'PASS' if ok_paint else 'FAIL'}")
    result = ok_windows and ok_draw and ok_reset and ok_paint
    print("[SELFTEST] RESULT=" + ("PASS" if result else "FAIL"))
    sys.stdout.flush()
    os._exit(0 if result else 1)


if __name__ == "__main__":
    threading.Thread(target=watchdog, daemon=True).start()
    sys.exit(app.run())
