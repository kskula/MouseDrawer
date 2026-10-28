#!/usr/bin/env python3
"""
Self-test multi-monitor: prawdziwe okna (jedno na monitor) + prawdziwe GDI,
wejscie (CTRL/LMB/kursor) skryptowane - nie dotyka pulpitu uzytkownika.

Sprawdza:
  1) liczba WIDOCZNYCH okien == liczba monitorow
  2) rysowanie: kreski powstaja (takze w obszarze monitora 2)
  3) geometria: kreski przeliczone na wspolrzedne klienta kazdego monitora mieszcza sie w jego buforze
  4) reset po puszczeniu CTRL
  5) kazde okno monitora zostalo odmalowane
  6) DPI awareness != unaware

Uruchom:  python tests/selftest_multi_monitor.py
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

# kreska: start na monitorze glownym, przejscie i koncowka na monitorze 2
POSITIONS = [(200, 200), (400, 300), (700, 500),
             (4300, 900), (4400, 1000), (4500, 1100),
             (4600, 1200), (4700, 1300)]

TICKS_HOLD = 40          # CTRL trzymany ~0.65 s - trzeba zdazyc sprawdzic przechwytywanie myszy
TICK_LMB_START = 3


class ScriptedWindow(m.DrawOverlayWindow):
    def __init__(self):
        super().__init__()
        self.t = 0
        self.max_segments = 0
        self.snapshot = []

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
        if len(self.segments) > self.max_segments:
            self.max_segments = len(self.segments)
            self.snapshot = list(self.segments)
        return changed


def count_visible_own_windows(pid):
    found = []
    WNDENUMPROC = ctypes_mod.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        wpid = wintypes.DWORD()
        m.user32.GetWindowThreadProcessId(hwnd, byref(wpid))
        if wpid.value == pid and m.user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    m.user32.EnumWindows(WNDENUMPROC(cb), 0)
    return found


app = ScriptedWindow()


def watchdog():
    time.sleep(1.2)

    # --- faza 2: symulacja zmiany konfiguracji ekranow (odpiecie / zmiana DPI / rozdzielczosci) ---
    hwnd_before = [mon["hwnd"] for mon in app.monitors]
    m.user32.PostMessageW(app.hwnd, m.WM_DISPLAYCHANGE, 0, 0)
    time.sleep(1.3)

    hwnd_after = [mon["hwnd"] for mon in app.monitors]
    ok_rebuild = (len(hwnd_after) == len(hwnd_before)
                  and hwnd_before != hwnd_after
                  and all(m.user32.IsWindow(h) for h in hwnd_after))

    n_mon = len(app.monitors)
    visible = count_visible_own_windows(os.getpid())

    ok_windows = len(visible) == n_mon and n_mon >= 1

    # geometria: przelicz snapshot na uklad klienta kazdego monitora
    saved = app.segments
    app.segments = app.snapshot
    per_mon = [app._monitor_client_segments(mon) for mon in app.monitors]
    app.segments = saved

    inside = {}
    for i, mon in enumerate(app.monitors):
        left, top, right, bottom = mon["rect"]
        w, h = right - left, bottom - top
        good = [s for s in per_mon[i]
                if 0 <= s[0] <= w and 0 <= s[1] <= h and 0 <= s[2] <= w and 0 <= s[3] <= h]
        inside[i] = len(good)

    ok_geom = all(inside[i] > 0 for i in range(n_mon))
    ok_painted = all(mon["paint_count"] > 0 for mon in app.monitors)
    ok_draw = app.max_segments >= 2
    ok_reset = len(app.segments) == 0

    awareness = m.set_dpi_awareness.__name__  # tylko etykieta, realnie sprawdzamy nizej
    aw = wintypes.UINT()
    try:
        m.shcore.GetProcessDpiAwareness(None, byref(aw))
        aw_val = aw.value
    except Exception:
        aw_val = -1
    ok_dpi = aw_val != 0

    print(f"[SELFTEST] monitory={n_mon} widoczne_okna={len(visible)}")
    for i, mon in enumerate(app.monitors):
        print(f"    [{i}] {mon['device']} rect={mon['rect']} dpi={mon['dpi']} "
              f"primary={mon['primary']} odmalowan={mon['paint_count']} "
              f"segmentow_w_ukladzie_monitora={len(per_mon[i])} w_buforze={inside[i]}")
    print(f"[SELFTEST] ticks={app.t} max_segments={app.max_segments} "
          f"final_segments={len(app.segments)} paint_total={app.paint_calls} "
          f"dpi_awareness={aw_val} rebuild_count={getattr(app, 'rebuild_count', -1)}")
    print(f"[SELFTEST] hwnd przed={hwnd_before} po={hwnd_after}")
    print(f"[SELFTEST] windows={'PASS' if ok_windows else 'FAIL'} "
          f"drawing={'PASS' if ok_draw else 'FAIL'} "
          f"geometry={'PASS' if ok_geom else 'FAIL'} "
          f"per_monitor_paint={'PASS' if ok_painted else 'FAIL'} "
          f"reset={'PASS' if ok_reset else 'FAIL'} "
          f"dpi_aware={'PASS' if ok_dpi else 'FAIL'} "
          f"rebuild={'PASS' if ok_rebuild else 'FAIL'}")
    result = all([ok_windows, ok_draw, ok_geom, ok_painted, ok_reset, ok_dpi, ok_rebuild])
    print("[SELFTEST] RESULT=" + ("PASS" if result else "FAIL"))
    sys.stdout.flush()
    os._exit(0 if result else 1)


if __name__ == "__main__":
    m.set_dpi_awareness()          # tak jak main() aplikacji - PRZED utworzeniem okien
    threading.Thread(target=watchdog, daemon=True).start()
    sys.exit(app.run())
