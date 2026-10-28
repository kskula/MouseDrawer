#!/usr/bin/env python3
"""
Screen Drawer Window - normalne okno Windows z transparentnym overlayem.
Rysowanie: CTRL + LMB = rysuj; puść CTRL = reset.
"""

import ctypes as ctypes_mod
from ctypes import wintypes, windll, Structure, c_long, c_int, byref
import time
import sys


# ==================== Win32 Imports ====================
user32 = windll.user32
gdi32 = windll.gdi32
kernel32 = windll.kernel32

# ==================== Structs ====================
class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


class RECT(Structure):
    _fields_ = [
        ("left", c_long), ("top", c_long),
        ("right", c_long), ("bottom", c_long)
    ]


class PAINTSTRUCT(Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", wintypes.BYTE * 32)
    ]


class MSG(Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT)
    ]


class WNDCLASSW(Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes_mod.c_void_p),
        ("cbClsExtra", c_int),
        ("cbWndExtra", c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR)
    ]


WNDPROC = ctypes_mod.WINFUNCTYPE(
    ctypes_mod.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)

# ==================== API Signatures (64-bit) ====================
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]

user32.RegisterClassW.argtypes = [ctypes_mod.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wintypes.ATOM

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes_mod.c_int, ctypes_mod.c_int, ctypes_mod.c_int, ctypes_mod.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes_mod.c_void_p
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes_mod.c_void_p

user32.SetTimer.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.UINT, ctypes_mod.c_void_p]
user32.SetTimer.restype = wintypes.UINT

user32.KillTimer.argtypes = [wintypes.HWND, wintypes.UINT]
user32.KillTimer.restype = wintypes.BOOL

user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.PostQuitMessage.argtypes = [ctypes_mod.c_int]
user32.PostQuitMessage.restype = None

user32.TranslateMessage.argtypes = [ctypes_mod.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL

user32.PeekMessageW.argtypes = [
    ctypes_mod.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT
]
user32.PeekMessageW.restype = wintypes.BOOL

user32.DispatchMessageW.argtypes = [ctypes_mod.POINTER(MSG)]
user32.DispatchMessageW.restype = ctypes_mod.c_void_p

# GDI
gdi32.CreatePen.argtypes = [wintypes.INT, wintypes.INT, wintypes.COLORREF]
gdi32.CreatePen.restype = wintypes.HPEN

gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ

gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL

gdi32.MoveToEx.argtypes = [wintypes.HDC, ctypes_mod.c_int, ctypes_mod.c_int, ctypes_mod.c_void_p]
gdi32.MoveToEx.restype = wintypes.BOOL

gdi32.LineTo.argtypes = [wintypes.HDC, ctypes_mod.c_int, ctypes_mod.c_int]
gdi32.LineTo.restype = wintypes.BOOL

user32.BeginPaint.argtypes = [wintypes.HWND, ctypes_mod.POINTER(PAINTSTRUCT)]
user32.BeginPaint.restype = wintypes.HDC

user32.EndPaint.argtypes = [wintypes.HWND, ctypes_mod.POINTER(PAINTSTRUCT)]
user32.EndPaint.restype = wintypes.BOOL

user32.GetClientRect.argtypes = [wintypes.HWND, ctypes_mod.POINTER(RECT)]
user32.GetClientRect.restype = wintypes.BOOL

user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = wintypes.INT

# Layered window
user32.SetLayeredWindowAttributes.argtypes = [
    wintypes.HWND, wintypes.COLORREF, wintypes.BYTE, wintypes.DWORD
]
user32.SetLayeredWindowAttributes.restype = wintypes.BOOL

# System metrics
user32.GetSystemMetrics.argtypes = [ctypes_mod.c_int]
user32.GetSystemMetrics.restype = ctypes_mod.c_int

# Constants
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000

WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000

LWA_COLORKEY = 0x00000001

WM_PAINT = 0x000F
WM_TIMER = 0x0113
WM_DESTROY = 0x0002
WM_ENDSESSION = 0x0016
WM_QUIT = 0x0012

PM_REMOVE = 0x0001

PS_SOLID = 0


# ==================== Main Class ====================
class DrawOverlayWindow:
    """Główny overlay z normalnym oknem."""
    
    def __init__(self):
        self.hwnd = None
        self.segments = []  # Lista segmentów linii [x1, y1, x2, y2]
        self.drawing = False
        self.cur_start = None
        
        # State dla detekcji klawiszy/myszy (edge detection)
        self._ctrl_prev = False
        self._lmb_prev = False
        
        # Size wirtualnego ekranu
        self._origin = (0, 0)
        self._size = (0, 0)
        
    def create(self):
        """Tworzy okno."""
        # Pobierz wymiary wirtualnego ekranu
        self._origin = (
            user32.GetSystemMetrics(76),  # SM_XVIRTUALSCREEN
            user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
        )
        self._size = (
            user32.GetSystemMetrics(78),  # SM_CXVIRTUALSCREEN
            user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
        )
        
        hinst = kernel32.GetModuleHandleW(None)
        
        wc = WNDCLASSW()
        wc.style = 0
        wc.lpfnWndProc = ctypes_mod.cast(user32.DefWindowProcW, ctypes_mod.c_void_p)
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = hinst
        wc.hIcon = None
        wc.hCursor = None
        wc.hbrBackground = None
        wc.lpszMenuName = None
        wc.lpszClassName = "ScreenDrawerWindow"
        
        # Okno pop-up, transparentne, bez aktywacji (na górze ale nie blokujące)
        self.hwnd = user32.CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE,
            "ScreenDrawerWindow",
            "",  # Brak tytułu
            WS_POPUP | WS_VISIBLE,
            self._origin[0], self._origin[1], self._size[0], self._size[1],
            None, None, hinst, None,
        )
        
        if not self.hwnd:
            err = ctypes_mod.get_last_error()
            # Jeśli oknie nie mozna stworzyc (bez display), powracamy 0 ale to nie jest bled
            import platform
            if platform.system().lower() == 'linux' and self._size[0] == 0 and self._size[1] == 0:
                print(f"[WARN] No display server - skipping window creation (expected in headless)", file=sys.stderr)
                return False
                
            err = ctypes_mod.get_last_error()
            print(f"[ERROR] CreateWindowExW failed: {err}", file=sys.stderr)
            return False
        
        # Ustaw przezroczystość (całkowicie transparentne okno)
        user32.SetLayeredWindowAttributes(
            self.hwnd, 0xFFFFFFFF, 0, LWA_COLORKEY
        )
        
        # Timer ~60Hz
        user32.SetTimer(self.hwnd, 1, 16, None)
        
        print(f"[OK] Window created: {self._size[0]}x{self._size[1]} at ({self._origin[0]}, {self._origin[1]})", file=sys.stderr)
        return True
    
    def _paint(self, hwnd):
        """Paint function."""
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, byref(ps))
        
        # Clear background (transparent - malujemy na całe okno)
        rc = RECT(0, 0, self._size[0], self._size[1])
        
        pen = gdi32.CreatePen(PS_SOLID, 3, 0x000000FF)  # Czerwony RGB
        old_pen = gdi32.SelectObject(hdc, pen)
        
        ox, oy = self._origin
        
        # Rysuj wszystkie segmenty
        for x1, y1, x2, y2 in self.segments:
            # Normalizuj współrzędne (do wirtualnego ekranu)
            gx1 = x1 - ox if ox != 0 else x1
            gy1 = y1 - oy if oy != 0 else y1
            gx2 = x2 - ox if ox != 0 else x2
            gy2 = y2 - oy if oy != 0 else y2
            
            gdi32.MoveToEx(hdc, int(gx1), int(gy1), None)
            gdi32.LineTo(hdc, int(gx2), int(gy2))
        
        gdi32.SelectObject(hdc, old_pen)
        gdi32.DeleteObject(pen)
        
        user32.EndPaint(hwnd, byref(ps))
        
        return 0
    
    def _on_timer(self, hwnd):
        """Timer callback - obsługa klawiszy i rysowanie."""
        ctrl_pressed = bool(user32.GetAsyncKeyState(0x11) & 0x8000)  # VK_CONTROL
        lmb_pressed = bool(user32.GetAsyncKeyState(0x01) & 0x8000)   # VK_LBUTTON
        
        changed = False
        
        # --- Reset przy puściu CTRL ---
        if ctrl_pressed and not self._ctrl_prev:
            # Ctrl był wcisnięty, teraz puszczone - RESET WSZYSTKO
            self.segments.clear()
            self.drawing = False
            self.cur_start = None
            print("[LOG] Ctrl release -> reset", file=sys.stderr)
            changed = True
            
        elif not ctrl_pressed and self._ctrl_prev:
            # Ctrl był puszczone, teraz wcisnięte - start rysowania
            pass
        
        # --- Start rysowania: CTRL wcisnięty + LMB kliknięcie ---
        if ctrl_pressed and lmb_pressed and not self._lmb_prev and not self.drawing:
            pt = POINT()
            if user32.GetCursorPos(byref(pt)):
                self.drawing = True
                self.cur_start = (pt.x, pt.y)
                print(f"[LOG] Start rysowania @ ({pt.x}, {pt.y})", file=sys.stderr)
                changed = True
        
        # --- Dynamiczne rysowanie podczas drag ---
        if self.drawing and self.cur_start is not None:
            pt = POINT()
            current_pos = user32.GetCursorPos(byref(pt))
            
            if current_pos:
                # Sprawdź czy kursor się przesunął (nie dodawaj duplikatów)
                last_seg = self.segments[-1] if len(self.segments) >= 2 else None
                if last_seg is not None and (last_seg[2], last_seg[3]) != (pt.x, pt.y):
                    self.segments.append([self.cur_start[0], self.cur_start[1], pt.x, pt.y])
                    print(f"[LOG] Drag: ({self.cur_start[0]},{self.cur_start[1]}) -> ({pt.x},{pt.y})", file=sys.stderr)
                    changed = True
        
        # --- Zakończenie rysowania przy puściu LMB (opcjonalne) ---
        if self.drawing and not lmb_pressed:
            print("[LOG] LMB release -> end drawing", file=sys.stderr)
            self.drawing = False
            self.cur_start = None
            changed = True
        
        # Update states dla edge detection
        self._ctrl_prev = ctrl_pressed
        self._lmb_prev = lmb_pressed
        
        if changed:
            user32.InvalidateRect(self.hwnd, None, True)
        
        return 0
    
    def _cleanup(self):
        """Czyszczenie przy end session."""
        try:
            if self.hwnd:
                user32.DestroyWindow(self.hwnd)
                self.hwnd = None
        except Exception as e:
            print(f"[WARN] Cleanup error: {e}", file=sys.stderr)
    
    def run(self):
        """Main loop."""
        if not self.create():
            return 1
        
        msg = MSG()
        print("[OK] Main loop started", file=sys.stderr)
        
        try:
            while True:
                if user32.PeekMessageW(byref(msg), None, 0, 0, PM_REMOVE):
                    if msg.message == WM_QUIT:
                        break
                    user32.TranslateMessage(byref(msg))
                    user32.DispatchMessageW(byref(msg))
                else:
                    time.sleep(0.005)
        except KeyboardInterrupt:
            print("[LOG] Interrupted", file=sys.stderr)
        finally:
            try:
                self._cleanup()
            except Exception as e:
                print(f"[WARN] Final cleanup error: {e}", file=sys.stderr)
        
        return 0


def main():
    """Entry point."""
    overlay = DrawOverlayWindow()
    sys.exit(overlay.run())


if __name__ == "__main__":
    main()
