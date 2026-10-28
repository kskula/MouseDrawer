#!/usr/bin/env python3
"""
Instrument diagnostyczny: czy klikniecia przechodza PRZEZ overlay do tego, co pod spodem?

Tworzy wlasne okno-sonde (liczy otrzymane klikniecia) i sprawdza trzy sytuacje:
  A) CTRL nie wcisniety   -> klik MA dotrzec do sondy (tryb klik-through)
  B) CTRL wcisniety       -> klik NIE MOZE dotrzec do sondy (rysujemy, pulpit nie reaguje)
  C) CTRL puszczony       -> klik znowu MA dotrzec do sondy

Uzywa prawdziwych, syntetycznych klikniec (mouse_event) w pozycje sondy.

Uruchom:  python tests/selftest_click_blocking.py
"""

import ctypes
import ctypes as ctypes_mod
import os
import subprocess
import sys
import threading
import time
from ctypes import wintypes, byref

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# DPI per-monitor v2 -> wspolrzedne fizyczne, spojne z aplikacja (inaczej SetCursorPos
# i pozycja okna sa w roznych ukladach i klikniecie trafia obok sondy)
try:
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    pass

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT,
                                  wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = wintypes.LPARAM
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                               wintypes.DWORD, ctypes.c_void_p]
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p]
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.WindowFromPoint.argtypes = [wintypes.POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                wintypes.WPARAM, wintypes.LPARAM]

GA_ROOT = 2


def class_of(hwnd):
    """Klasa okna-korzenia, ktore dostanie klikniecie."""
    if not hwnd:
        return "<brak>"
    root = user32.GetAncestor(hwnd, GA_ROOT) or hwnd
    b = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(root, b, 256)
    return b.value

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_CONTROL = 0x11
KEYEVENTF_KEYUP = 0x0002

PROBE_W, PROBE_H = 240, 160
count = {"down": 0, "up": 0}

WNDPROC = ctypes_mod.WINFUNCTYPE(wintypes.LPARAM, wintypes.HWND, wintypes.UINT,
                                 wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", ctypes.c_void_p),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]


def probe_wndproc(hwnd, msg, wparam, lparam):
    if msg == 0x0201:      # WM_LBUTTONDOWN
        count["down"] += 1
    elif msg == 0x0202:    # WM_LBUTTONUP
        count["up"] += 1
    elif msg == 0x0002:    # WM_DESTROY
        user32.PostQuitMessage(0)
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


wndproc_ref = WNDPROC(probe_wndproc)


def create_probe(x, y):
    """Male okno NIE-topmost - overlay (topmost) jest nad nim, wiec klik musi przez niego przejsc."""
    hinst = kernel32.GetModuleHandleW(None)
    wc = WNDCLASSW()
    wc.lpfnWndProc = ctypes.cast(wndproc_ref, ctypes.c_void_p)
    wc.hInstance = hinst
    wc.hbrBackground = 6 + 1          # COLOR_WINDOW+1
    wc.lpszClassName = "ClickProbeWindow"
    user32.RegisterClassW(byref(wc))
    return user32.CreateWindowExW(
        0x00000080,                    # WS_EX_TOOLWINDOW (bez przycisku na pasku)
        "ClickProbeWindow", "ClickProbe", 0x80000000 | 0x10000000,  # WS_POPUP|WS_VISIBLE
        x, y, PROBE_W, PROBE_H, None, None, hinst, None)


def overlay_running():
    found = []

    def cb(hwnd, _):
        b = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, b, 256)
        if b.value == "ScreenDrawerWindow":
            found.append(hwnd)
        return True

    user32.EnumWindows(ctypes_mod.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return found


def click_at(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, None)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, None)


def driver(probe_hwnd, center):
    # sonda na wierzchu wsrod nie-topmost, wiec widoczna; overlay jest topmost -> nad nia
    time.sleep(0.6)

    def phase(name, hold_ctrl):
        if hold_ctrl:
            user32.keybd_event(VK_CONTROL, 0, 0, None)
            time.sleep(0.5)
        target = class_of(user32.WindowFromPoint(wintypes.POINT(*center)))
        count["down"] = count["up"] = 0
        click_at(*center)
        time.sleep(0.35)
        got = count["down"]
        if hold_ctrl:
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, None)
            time.sleep(0.45)
        print(f"[CLICK] {name}: cel klikniecia={target!r}  klikniec w sondzie={got}")
        return got

    a = phase("A) bez CTRL      ", False)
    b = phase("B) CTRL wcisniety", True)
    c = phase("C) CTRL puszczony", False)

    result = (a >= 1) and (b == 0) and (c >= 1)
    print(f"[CLICK] A={'PASS' if a >= 1 else 'FAIL'} "
          f"B(blokada)={'PASS' if b == 0 else 'FAIL - klik przeszedl na to, co pod spodem'} "
          f"C={'PASS' if c >= 1 else 'FAIL'}")
    print("[CLICK] RESULT=" + ("PASS" if result else "FAIL"))
    sys.stdout.flush()

    user32.PostMessageW(probe_hwnd, 0x0010, 0, 0)     # WM_CLOSE
    os._exit(0 if result else 1)


if __name__ == "__main__":
    # overlay musi dzialac (jesli nie - startujemy .exe)
    if not overlay_running():
        exe = os.path.join(ROOT, "dist", "screen_drawer_window.exe")
        if not os.path.exists(exe):
            print("[CLICK] brak dzialajacego overlay i brak dist/screen_drawer_window.exe")
            sys.exit(2)
        subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                        f"Start-Process -FilePath '{exe}'"],
                       capture_output=True, text=True, timeout=60)
        time.sleep(5)

    pt = wintypes.POINT()
    user32.GetCursorPos(byref(pt))
    saved_cursor = (pt.x, pt.y)

    # pozycja sondy: srodek monitora podstawowego (wirtualny ekran ma tu miejsce)
    cx, cy = 1180, 620
    hwnd = create_probe(cx - PROBE_W // 2, cy - PROBE_H // 2)
    if not hwnd:
        print("[CLICK] nie udalo sie utworzyc okna-sondy")
        sys.exit(2)

    threading.Thread(target=driver, args=(hwnd, (cx, cy)), daemon=True).start()
    try:
        msg = wintypes.MSG()
        while user32.GetMessageW(byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(byref(msg))
            user32.DispatchMessageW(byref(msg))
    finally:
        user32.SetCursorPos(*saved_cursor)
