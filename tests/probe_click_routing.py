#!/usr/bin/env python3
"""
Diagnostyka routingu klikniec: WindowFromPoint = okno, ktore DOSTANIE klikniecie.

Sprawdza te same punkty ekranu dwa razy:
  1) bez CTRL  - spodziewamy sie, ze klik przechodzi do tego, co pod overlayem
  2) z CTRL    - overlay MA przechwycic klik, wiec WindowFromPoint powinien
                 zwrocic okno klasy ScreenDrawerWindow

Jesli w obu przypadkach wynik jest taki sam (i to nie overlay), to znaczy ze
klik nadal przechodzi na pulpit - dokladnie to, co zglasza uzytkownik.

Uruchom:  python tests/probe_click_routing.py
"""

import ctypes
import sys
import time
from ctypes import wintypes

user32 = ctypes.windll.user32

user32.WindowFromPoint.argtypes = [wintypes.POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.ChildWindowFromPointEx.argtypes = [wintypes.HWND, wintypes.POINT, wintypes.UINT]
user32.ChildWindowFromPointEx.restype = wintypes.HWND
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p]

# DPI per-monitor v2 jak w aplikacji -> wspolrzedne fizyczne, bez wirtualizacji
try:
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    pass

VK_CONTROL = 0x11
KEYEVENTF_KEYUP = 0x0002
GA_ROOT = 2

# punkty na monitorze podstawowym (3840x2160, 150 %)
POINTS = [(600, 300), (1180, 700), (1700, 1500), (300, 1900)]


def target(x, y):
    h = user32.WindowFromPoint(wintypes.POINT(x, y))
    if not h:
        return None, "<brak>"
    root = user32.GetAncestor(h, GA_ROOT) or h
    b = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(root, b, 256)
    return root, b.value


def main():
    print("Punkty monitora 1 (fizyczne wspolrzedne):")
    before = {}
    for p in POINTS:
        hwnd, cls = target(*p)
        before[p] = (hwnd, cls)
        print(f"  {p}:  bez CTRL -> klasa={cls!r} hwnd={hwnd}")

    user32.keybd_event(VK_CONTROL, 0, 0, None)
    try:
        time.sleep(0.4)
        print("\nZ CTRL wcisnietym:")
        after = {}
        for p in POINTS:
            hwnd, cls = target(*p)
            after[p] = (hwnd, cls)
            print(f"  {p}:  z CTRL   -> klasa={cls!r} hwnd={hwnd}")
    finally:
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, None)

    captured = [p for p in POINTS if after[p][1] == "ScreenDrawerWindow"]
    print(f"\nPunkty, w ktorych overlay przechwytuje klik: {len(captured)}/{len(POINTS)}")
    ok = len(captured) == len(POINTS)
    print("[ROUTING] RESULT=" + ("PASS" if ok else "FAIL - klik nadal idzie na pulpit"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
