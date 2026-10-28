#!/usr/bin/env python3
"""
Screen Drawer Window - transparentny overlay z rysowaniem CTRL+LMB.

Rysowanie: przytrzymaj CTRL i LMB -> rysujesz; pusc CTRL -> rysunek znika.
Zamkniecie: ESC (albo Menadzer zadan).
"""

import ctypes as ctypes_mod
from ctypes import wintypes, windll, Structure, c_long, c_int, byref
import time
import sys


# ==================== Win32 ====================
user32 = windll.user32
gdi32 = windll.gdi32
kernel32 = windll.kernel32


# ==================== Struktury ====================
class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


class RECT(Structure):
    _fields_ = [("left", c_long), ("top", c_long),
                ("right", c_long), ("bottom", c_long)]


class MSG(Structure):
    _fields_ = [("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD),
                ("pt", POINT)]


class WNDCLASSW(Structure):
    _fields_ = [("style", wintypes.UINT),
                ("lpfnWndProc", ctypes_mod.c_void_p),
                ("cbClsExtra", c_int),
                ("cbWndExtra", c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR)]


# ==================== Sygnatury API ====================
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.CreateMutexW.argtypes = [ctypes_mod.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.GetLastError.restype = wintypes.DWORD

user32.RegisterClassW.argtypes = [ctypes_mod.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wintypes.ATOM

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    c_int, c_int, c_int, c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes_mod.c_void_p]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes_mod.c_void_p

user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF,
                                              wintypes.BYTE, wintypes.DWORD]
user32.SetLayeredWindowAttributes.restype = wintypes.BOOL

user32.SetTimer.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.UINT, ctypes_mod.c_void_p]
user32.SetTimer.restype = wintypes.UINT
user32.KillTimer.argtypes = [wintypes.HWND, wintypes.UINT]
user32.KillTimer.restype = wintypes.BOOL
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = c_int
user32.FillRect.argtypes = [wintypes.HDC, ctypes_mod.POINTER(RECT), wintypes.HBRUSH]
user32.FillRect.restype = c_int

user32.PeekMessageW.argtypes = [ctypes_mod.POINTER(MSG), wintypes.HWND,
                                wintypes.UINT, wintypes.UINT, wintypes.UINT]
user32.PeekMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes_mod.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes_mod.POINTER(MSG)]
user32.DispatchMessageW.restype = ctypes_mod.c_void_p

user32.GetAsyncKeyState.argtypes = [c_int]
user32.GetAsyncKeyState.restype = wintypes.SHORT
user32.GetCursorPos.argtypes = [ctypes_mod.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [c_int]
user32.GetSystemMetrics.restype = c_int

gdi32.CreateSolidBrush.argtypes = [wintypes.COLORREF]
gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
gdi32.CreatePen.argtypes = [c_int, c_int, wintypes.COLORREF]
gdi32.CreatePen.restype = wintypes.HPEN
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.MoveToEx.argtypes = [wintypes.HDC, c_int, c_int, ctypes_mod.c_void_p]
gdi32.MoveToEx.restype = wintypes.BOOL
gdi32.LineTo.argtypes = [wintypes.HDC, c_int, c_int]
gdi32.LineTo.restype = wintypes.BOOL
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, c_int, c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.BitBlt.argtypes = [wintypes.HDC, c_int, c_int, c_int, c_int,
                         wintypes.HDC, c_int, c_int, wintypes.DWORD]
gdi32.BitBlt.restype = wintypes.BOOL


# ==================== Stale ====================
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000

WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

LWA_COLORKEY = 0x00000001
SRCCOPY = 0x00CC0020
PS_SOLID = 0

WM_TIMER = 0x0113
WM_QUIT = 0x0012
PM_REMOVE = 0x0001

VK_LBUTTON = 0x01
VK_CONTROL = 0x11
VK_ESCAPE = 0x1B

ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "ScreenDrawerWindow_SingleInstance"

# COLORREF = 0x00BBGGRR
KEY_COLOR = 0x00000000   # czarny = przezroczysty (color key)
PEN_COLOR = 0x000000FF   # czerwony

# Bez WS_EX_TOOLWINDOW -> okno widoczne na pasku zadan (mozna je zamknac)
EX_STYLE = WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TRANSPARENT
CLASS_NAME = "ScreenDrawerWindow"
TIMER_ID = 1
TIMER_MS = 16


class DrawOverlayWindow:
    """Transparentny overlay: rysowanie CTRL+LMB, reset po puszczeniu CTRL."""

    def __init__(self):
        self.hwnd = None
        self.segments = []          # [(x1,y1,x2,y2), ...] we wspolrzednych ekranu
        self.drawing = False
        self._last_pt = None
        self._ctrl_prev = False
        self._lmb_prev = False
        self._quit = False
        self._origin = (0, 0)
        self._size = (0, 0)
        self._mem_dc = None
        self._mem_bmp = None

    # ---------- wejscie (nadpisywalne w testach) ----------
    def _is_ctrl_down(self):
        return bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)

    def _is_lmb_down(self):
        return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

    def _is_esc_down(self):
        return bool(user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000)

    def _cursor_pos(self):
        pt = POINT()
        if user32.GetCursorPos(byref(pt)):
            return (pt.x, pt.y)
        return None

    # ---------- okno ----------
    def create(self):
        self._origin = (user32.GetSystemMetrics(76), user32.GetSystemMetrics(77))
        self._size = (user32.GetSystemMetrics(78), user32.GetSystemMetrics(79))
        print(f"[INFO] Ekran wirtualny: {self._size[0]}x{self._size[1]} @ {self._origin}",
              file=sys.stderr)

        hinst = kernel32.GetModuleHandleW(None)

        wc = WNDCLASSW()
        wc.style = 0
        wc.lpfnWndProc = ctypes_mod.cast(user32.DefWindowProcW, ctypes_mod.c_void_p)
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = hinst
        wc.hIcon = None
        wc.hCursor = None
        wc.hbrBackground = None          # tlo malujemy sami w _paint()
        wc.lpszMenuName = None
        wc.lpszClassName = CLASS_NAME

        atom = user32.RegisterClassW(byref(wc))
        if not atom:
            print(f"[ERROR] RegisterClassW nie powiodlo sie: {kernel32.GetLastError()}",
                  file=sys.stderr)
            return False

        self.hwnd = user32.CreateWindowExW(
            EX_STYLE, CLASS_NAME, "", WS_POPUP | WS_VISIBLE,
            self._origin[0], self._origin[1], self._size[0], self._size[1],
            None, None, hinst, None)

        if not self.hwnd:
            print(f"[ERROR] CreateWindowExW nie powiodlo sie: {kernel32.GetLastError()}",
                  file=sys.stderr)
            return False

        # color key: piksele KEY_COLOR (czarne) staja sie przezroczyste
        user32.SetLayeredWindowAttributes(self.hwnd, KEY_COLOR, 0, LWA_COLORKEY)

        # bufor rysowania (double buffer - bez migotania)
        screen_dc = user32.GetDC(self.hwnd)
        self._mem_dc = gdi32.CreateCompatibleDC(screen_dc)
        self._mem_bmp = gdi32.CreateCompatibleBitmap(screen_dc, self._size[0], self._size[1])
        gdi32.SelectObject(self._mem_dc, self._mem_bmp)
        user32.ReleaseDC(self.hwnd, screen_dc)

        user32.SetTimer(self.hwnd, TIMER_ID, TIMER_MS, None)

        print(f"[OK] Okno utworzone (hwnd={self.hwnd}), CTRL+LMB = rysuj, CTRL pusc = reset, ESC = wyjscie",
              file=sys.stderr)
        self._paint()
        return True

    # ---------- rysowanie ----------
    def _paint(self):
        if not self._mem_dc:
            return
        w, h = self._size

        # wyczysc bufor kolorem klucza
        brush = gdi32.CreateSolidBrush(KEY_COLOR)
        user32.FillRect(self._mem_dc, byref(RECT(0, 0, w, h)), brush)
        gdi32.DeleteObject(brush)

        if self.segments:
            pen = gdi32.CreatePen(PS_SOLID, 3, PEN_COLOR)
            old = gdi32.SelectObject(self._mem_dc, pen)
            ox, oy = self._origin
            for x1, y1, x2, y2 in self.segments:
                gdi32.MoveToEx(self._mem_dc, x1 - ox, y1 - oy, None)
                gdi32.LineTo(self._mem_dc, x2 - ox, y2 - oy)
            gdi32.SelectObject(self._mem_dc, old)
            gdi32.DeleteObject(pen)

        hdc = user32.GetDC(self.hwnd)
        gdi32.BitBlt(hdc, 0, 0, w, h, self._mem_dc, 0, 0, SRCCOPY)
        user32.ReleaseDC(self.hwnd, hdc)

    # ---------- logika ----------
    def _on_timer(self):
        """Zwraca True jesli trzeba odswiezyc rysunek."""
        if self._is_esc_down():
            print("[INFO] ESC -> koncze", file=sys.stderr)
            self._quit = True
            return False

        ctrl = self._is_ctrl_down()
        lmb = self._is_lmb_down()
        changed = False

        # RESET: puszczono CTRL -> czyscimy rysunek
        if self._ctrl_prev and not ctrl:
            if self.segments or self.drawing:
                changed = True
            self.segments.clear()
            self.drawing = False
            self._last_pt = None
            print("[LOG] CTRL puszczony -> reset", file=sys.stderr)

        # rysowanie tylko gdy CTRL + LMB
        if ctrl and lmb:
            pt = self._cursor_pos()
            if pt is not None:
                if not self.drawing:
                    self.drawing = True
                    self._last_pt = pt
                    print(f"[LOG] Start rysowania @ {pt}", file=sys.stderr)
                elif pt != self._last_pt:
                    self.segments.append((self._last_pt[0], self._last_pt[1], pt[0], pt[1]))
                    self._last_pt = pt
                    changed = True
        elif self.drawing:
            # puszczono LMB -> koniec kreski (rysunek zostaje do puszczenia CTRL)
            print("[LOG] LMB puszczony -> koniec kreski", file=sys.stderr)
            self.drawing = False
            self._last_pt = None

        self._ctrl_prev = ctrl
        self._lmb_prev = lmb
        return changed

    # ---------- petla ----------
    def run(self):
        if not self.create():
            return 1

        msg = MSG()
        print("[OK] Petla komunikatow dziala", file=sys.stderr)
        try:
            while True:
                if user32.PeekMessageW(byref(msg), None, 0, 0, PM_REMOVE):
                    if msg.message == WM_QUIT:
                        break
                    user32.TranslateMessage(byref(msg))
                    user32.DispatchMessageW(byref(msg))
                    if msg.message == WM_TIMER and msg.hwnd == self.hwnd:
                        if self._on_timer():
                            self._paint()
                        if self._quit:
                            break
                else:
                    time.sleep(0.005)
        except KeyboardInterrupt:
            print("[INFO] Przerwano z klawiatury", file=sys.stderr)
        finally:
            self._cleanup()
        return 0

    def _cleanup(self):
        try:
            if self.hwnd:
                user32.KillTimer(self.hwnd, TIMER_ID)
                user32.DestroyWindow(self.hwnd)
                self.hwnd = None
            if self._mem_dc:
                gdi32.DeleteDC(self._mem_dc)
                self._mem_dc = None
            if self._mem_bmp:
                gdi32.DeleteObject(self._mem_bmp)
                self._mem_bmp = None
        except Exception as e:
            print(f"[WARN] Blad sprzatania: {e}", file=sys.stderr)


def acquire_single_instance():
    """Zwraca True jesli to jedyna instancja aplikacji."""
    kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return kernel32.GetLastError() != ERROR_ALREADY_EXISTS


def main():
    if not acquire_single_instance():
        print("[ERROR] Aplikacja juz dziala (jedna instancja).", file=sys.stderr)
        return 1
    return DrawOverlayWindow().run()


if __name__ == "__main__":
    sys.exit(main())
