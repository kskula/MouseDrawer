#!/usr/bin/env python3
"""
Self-test przechwytywania myszy.

Cel: gdy CTRL jest wcisniety (rysowanie), okna overlay maja ZJADAC klikniecia
(bez flagi WS_EX_TRANSPARENT), zeby pulpit nie zaznaczal ikon ani nie robil ramki.
Po puszczeniu CTRL ma wrocic tryb klik-through (WS_EX_TRANSPARENT z powrotem).

Test uruchamia PRAWDZIWE okna i PRAWDZIWE przelaczanie stylow, ale wejscie jest
skryptowane - nie rusza myszy ani klawiatury uzytkownika.

Uruchom:  python tests/selftest_input_capture.py
"""

import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import screen_drawer_window as m  # noqa: E402

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
SAMPLE_MS = 0.03


class ScriptedWindow(m.DrawOverlayWindow):
    """Overlay ze skryptowanym CTRL (bez dotykania klawiatury uzytkownika)."""

    def __init__(self):
        super().__init__()
        self.ctrl_on = True

    def _is_esc_down(self):
        return False

    def _is_ctrl_down(self):
        return self.ctrl_on

    def _is_lmb_down(self):
        return False

    def _cursor_pos(self):
        return (100, 100)


app = ScriptedWindow()
samples = []          # (t, passthrough) - tylko gdy okno juz istnieje


def sampler():
    t0 = time.time()
    while True:
        try:
            hwnd = app.monitors[0]["hwnd"] if app.monitors else None
        except Exception:
            hwnd = None
        if hwnd:
            ex = m.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            samples.append((round(time.time() - t0, 3), bool(ex & WS_EX_TRANSPARENT)))
        time.sleep(SAMPLE_MS)


def driver():
    # faza 1: CTRL trzymany -> kazda probka PO starcie aplikacji w trybie CAPTURE.
    # Probki z pierwszych 0.4 s pomijamy: wtedy okna dopiero powstaja i style sie ustawiaja.
    time.sleep(1.2)
    during = [s for s in samples if s[0] >= 0.4]
    ok_during = len(during) >= 10 and all(not p for _, p in during)
    leaks = [s for s in during if s[1]]

    # faza 2: puszczamy CTRL -> ma wrocic klik-through
    app.ctrl_on = False
    time.sleep(1.0)
    after = [s for s in samples if s[0] >= 1.35]
    ok_after = bool(after) and after[-1][1] is True

    print(f"[CAPTURE] probek podczas CTRL: {len(during)}  "
          f"(w trybie klik-through: {len(leaks)})")
    if leaks:
        print(f"[CAPTURE]   przecieki (t, passthrough): {leaks[:8]}")
    print(f"[CAPTURE] probek po puszczeniu CTRL: {len(after)}  "
          f"ostatnia probka passthrough={after[-1][1] if after else None}")
    print(f"[CAPTURE] capture_during_ctrl={'PASS' if ok_during else 'FAIL'} "
          f"passthrough_after_release={'PASS' if ok_after else 'FAIL'}")
    result = ok_during and ok_after
    print("[CAPTURE] RESULT=" + ("PASS" if result else "FAIL"))
    sys.stdout.flush()
    os._exit(0 if result else 1)


if __name__ == "__main__":
    m.set_dpi_awareness()
    threading.Thread(target=sampler, daemon=True).start()
    threading.Thread(target=driver, daemon=True).start()
    sys.exit(app.run())
