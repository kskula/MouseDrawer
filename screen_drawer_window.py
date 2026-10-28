#!/usr/bin/env python3
"""
Screen Drawer - rysowanie po ekranie (CTRL+ALT+LMB), wersja multi-monitor + tray.

Jedno okno overlay na KAZDY monitor (EnumDisplayMonitors), DPI per-monitor v2.
Okna overlay sa WS_EX_TOOLWINDOW -> nie ma ich na pasku zadan ani w Alt-Tab.

BEZ OKNA KONSOLI: jedynym widocznym znakiem aplikacji jest IKONA W ZASOBNIKU
(kolo zegara). Prawy przycisk na ikonie -> menu z pozycja "Zamknij".
Logi leca do pliku %TEMP%\\screen_drawer.log (albo pod SCREEN_DRAWER_LOG).

Rysowanie: przytrzymaj CTRL + ALT + LMB -> rysujesz; pusc CTRL lub ALT -> rysunek znika.
Zamkniecie: menu ikony -> "Zamknij" (albo ESC).
"""

import ctypes as ctypes_mod
from ctypes import wintypes, windll, Structure, c_long, c_int, c_uint, byref
import os
import threading
import time
import sys


class _NullStream:
    """Atrapa strumienia, gdy nie ma ani konsoli, ani pliku logu."""

    def write(self, *args):
        pass

    def flush(self):
        pass


# Log do pliku: bez konsoli nie ma gdzie pisac, a log jest potrzebny do diagnozy.
# SCREEN_DRAWER_LOG (jesli ustawione) = sciezka pliku logu, plik jest czyszczony.
_LOG_PATH = os.environ.get("SCREEN_DRAWER_LOG") or os.path.join(
    os.environ.get("TEMP", "."), "screen_drawer.log")
_LOG_FILE = None

if __name__ == "__main__":
    # TYLKO przy uruchomieniu programu. Przy imporcie (np. w testach) nie wolno
    # przekierowywac strumieni, bo znikneloby wyjscie procesu testujacego.
    try:
        _LOG_FILE = open(_LOG_PATH, "w" if os.environ.get("SCREEN_DRAWER_LOG") else "a",
                         encoding="utf-8", errors="replace", buffering=1)
        sys.stdout = _LOG_FILE
        sys.stderr = _LOG_FILE
    except Exception:
        _LOG_FILE = None
if getattr(sys, "stdout", None) is None:
    sys.stdout = _NullStream()
if getattr(sys, "stderr", None) is None:
    sys.stderr = _NullStream()


# ==================== Win32 ====================
user32 = windll.user32
gdi32 = windll.gdi32
kernel32 = windll.kernel32
shell32 = windll.shell32


# ==================== Struktury ====================
class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


class RECT(Structure):
    _fields_ = [("left", c_long), ("top", c_long),
                ("right", c_long), ("bottom", c_long)]


class MONITORINFOEXW(Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD),
                ("szDevice", wintypes.WCHAR * 32)]


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


class GUID(Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD), ("Data4", wintypes.BYTE * 8)]


class NOTIFYICONDATAW(Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128),
                ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256),
                ("uVersion", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64),
                ("dwInfoFlags", wintypes.DWORD),
                ("guidItem", GUID),
                ("hBalloonIcon", wintypes.HICON)]


MONITORENUMPROC = ctypes_mod.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
    ctypes_mod.POINTER(RECT), wintypes.LPARAM)

WNDPROC = ctypes_mod.WINFUNCTYPE(
    wintypes.LPARAM, wintypes.HWND, wintypes.UINT,
    wintypes.WPARAM, wintypes.LPARAM)

HOOKPROC = ctypes_mod.WINFUNCTYPE(
    wintypes.LPARAM, c_int, wintypes.WPARAM, wintypes.LPARAM)


# ==================== Sygnatury API ====================
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.CreateMutexW.argtypes = [ctypes_mod.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.GetLastError.restype = wintypes.DWORD

user32.SetProcessDpiAwarenessContext.argtypes = [ctypes_mod.c_void_p]
user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL

user32.RegisterClassW.argtypes = [ctypes_mod.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wintypes.ATOM

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    c_int, c_int, c_int, c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes_mod.c_void_p]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = wintypes.LPARAM

user32.PostQuitMessage.argtypes = [c_int]
user32.PostQuitMessage.restype = None
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL

user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes_mod.POINTER(RECT),
                                       MONITORENUMPROC, wintypes.LPARAM]
user32.EnumDisplayMonitors.restype = wintypes.BOOL
user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes_mod.POINTER(MONITORINFOEXW)]
user32.GetMonitorInfoW.restype = wintypes.BOOL

user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF,
                                              wintypes.BYTE, wintypes.DWORD]
user32.SetLayeredWindowAttributes.restype = wintypes.BOOL

user32.SetWindowLongW.argtypes = [wintypes.HWND, c_int, c_long]
user32.SetWindowLongW.restype = c_long
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, c_int, c_int,
                                c_int, c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL

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
user32.GetMessageW.argtypes = [ctypes_mod.POINTER(MSG), wintypes.HWND,
                               wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes_mod.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes_mod.POINTER(MSG)]
user32.DispatchMessageW.restype = wintypes.LPARAM
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL

user32.GetAsyncKeyState.argtypes = [c_int]
user32.GetAsyncKeyState.restype = wintypes.SHORT
user32.GetCursorPos.argtypes = [ctypes_mod.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
user32.MessageBoxW.restype = c_int

# hook myszy
user32.SetWindowsHookExW.argtypes = [c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = wintypes.LPARAM

# tray (ikona kolo zegara)
shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes_mod.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL
user32.LoadIconW.argtypes = [wintypes.HINSTANCE, ctypes_mod.c_void_p]
user32.LoadIconW.restype = wintypes.HICON
user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                              c_int, c_int, wintypes.UINT]
user32.LoadImageW.restype = wintypes.HANDLE
user32.CreatePopupMenu.argtypes = []
user32.CreatePopupMenu.restype = wintypes.HMENU
user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes_mod.c_void_p, wintypes.LPCWSTR]
user32.AppendMenuW.restype = wintypes.BOOL
user32.TrackPopupMenu.argtypes = [wintypes.HMENU, wintypes.UINT, c_int, c_int,
                                  c_int, wintypes.HWND, ctypes_mod.c_void_p]
user32.TrackPopupMenu.restype = wintypes.BOOL
user32.DestroyMenu.argtypes = [wintypes.HMENU]
user32.DestroyMenu.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL

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

try:
    shcore = windll.shcore
    shcore.GetDpiForMonitor.argtypes = [wintypes.HMONITOR, c_int,
                                        ctypes_mod.POINTER(c_uint),
                                        ctypes_mod.POINTER(c_uint)]
    shcore.GetDpiForMonitor.restype = c_int
except Exception:                                     # pragma: no cover
    shcore = None


# ==================== Stale ====================
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000

WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000

GWL_EXSTYLE = -20
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020

LWA_COLORKEY = 0x00000001
SRCCOPY = 0x00CC0020
PS_SOLID = 0

WM_NULL = 0x0000
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_QUIT = 0x0012
WM_COMMAND = 0x0111
WM_DISPLAYCHANGE = 0x007E
WM_DPICHANGED = 0x02E0
WM_TIMER = 0x0113
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
PM_REMOVE = 0x0001

VK_LBUTTON = 0x01
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_ESCAPE = 0x1B

WH_MOUSE_LL = 14
WM_LBUTTONDOWN = 0x0201
BLOCKED_MOUSE_MESSAGES = frozenset([
    WM_LBUTTONDOWN, WM_LBUTTONUP,
    0x0204,  # WM_RBUTTONDOWN
    WM_RBUTTONUP,
    0x0207,  # WM_MBUTTONDOWN
    0x0208,  # WM_MBUTTONUP
    0x020A,  # WM_MOUSEWHEEL
    0x020B,  # WM_XBUTTONDOWN
    0x020C,  # WM_XBUTTONUP
    0x020E,  # WM_MOUSEHWHEEL
])

# tray
TRAY_CLASS_NAME = "ScreenDrawerTrayWindow"
TRAY_CALLBACK_MSG = 0x8001          # WM_APP + 1
TRAY_ICON_ID = 1
ID_MENU_CLOSE = 1
MF_STRING = 0x00000000
TPM_RIGHTBUTTON = 0x0002
TPM_BOTTOMALIGN = 0x0020
NIM_ADD = 0x00000000
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
IDI_APPLICATION = 32512
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_SETFOREGROUND = 0x00010000

ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "ScreenDrawerWindow_SingleInstance"

MDT_EFFECTIVE_DPI = 0
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4

# COLORREF = 0x00BBGGRR
KEY_COLOR = 0x00000000   # czarny = przezroczysty (color key)
PEN_COLOR = 0x000000FF   # czerwony
PEN_WIDTH_BASE = 3       # px przy 100 % (96 DPI)

EX_STYLE_PASSTHROUGH = (WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_LAYERED
                        | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE)
EX_STYLE_CAPTURE = (WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_LAYERED
                    | WS_EX_NOACTIVATE)
EX_STYLE = EX_STYLE_PASSTHROUGH

CLASS_NAME = "ScreenDrawerWindow"
TIMER_ID = 1
TIMER_MS = 16


# ==================== Hook myszy (wlasny watek) ====================
_hook = {"handle": None, "proc": None, "app": None, "blocked": 0, "ready": False}


def _mouse_hook_proc(ncode, wparam, lparam):
    """
    WH_MOUSE_LL. Śledzi PRAWdziwy stan przycisku (zjedzone zdarzenie nie trafia do
    kolejki, wiec GetAsyncKeyState go nie widzi) i zjada klikniecia na czas rysowania.
    """
    try:
        if ncode >= 0:
            app = _hook["app"]
            if app is not None:
                if wparam == WM_LBUTTONDOWN:
                    app._phys_lmb = True
                elif wparam == WM_LBUTTONUP:
                    app._phys_lmb = False
                if getattr(app, "_capturing", False) and wparam in BLOCKED_MOUSE_MESSAGES:
                    _hook["blocked"] += 1
                    return 1                     # nie przepuszczamy na pulpit
    except Exception:
        pass
    return user32.CallNextHookEx(None, ncode, wparam, lparam)


def _mouse_hook_thread(app):
    """Osobny watek z ciasna petla GetMessage - hook nie czeka na petle rysowania."""
    _hook["app"] = app
    _hook["proc"] = HOOKPROC(_mouse_hook_proc)
    _hook["handle"] = user32.SetWindowsHookExW(WH_MOUSE_LL, _hook["proc"], None, 0)
    if not _hook["handle"]:
        print(f"[WARN] Hook myszy nie powstal (GetLastError={kernel32.GetLastError()}) "
              f"- klikniecia moga przechodzic na pulpit", file=sys.stderr)
        return
    _hook["ready"] = True
    print("[LOG] Hook myszy gotowy (klikniecia blokowane tylko podczas rysowania)",
          file=sys.stderr)
    msg = MSG()
    while user32.GetMessageW(byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(byref(msg))
        user32.DispatchMessageW(byref(msg))
    user32.UnhookWindowsHookEx(_hook["handle"])
    _hook["handle"] = None


def start_mouse_hook(app):
    threading.Thread(target=_mouse_hook_thread, args=(app,), daemon=True).start()


def set_input_capture(app, capture):
    """Wlacza/wylacza blokowanie klikniec (styl okien + flaga dla hooka)."""
    if capture == getattr(app, "_capturing", False):
        return
    style_want = EX_STYLE_CAPTURE if capture else EX_STYLE_PASSTHROUGH
    for mon in app.monitors:
        hwnd = mon.get("hwnd")
        if not hwnd:
            continue
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style_want)
        user32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
                            | SWP_NOACTIVATE | SWP_FRAMECHANGED)
    if capture:
        app._phys_lmb = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
    app._capturing = capture
    if not _hook["ready"]:
        print("[WARN] Brak hooka myszy - pulpit moze reagowac na rysowanie", file=sys.stderr)
    print("[LOG] " + ("Blokuje klikniecia (rysowanie) - pulpit nie reaguje"
                      if capture else "Klik-through - pulpit znowu dziala"),
          file=sys.stderr)


# ==================== Ikona w zasobniku (tray) ====================
_tray = {"added": False, "hwnd": None, "nid": None, "icon": None}


def tray_create_window(app):
    """
    Male, nieuzywane okno-uchwyt dla ikony w zasobniku. Jest zwyklym oknem
    (bez LAYERED/NOACTIVATE), wiec mozna je aktywowac - dzieki temu menu
    kontekstowe poprawnie sie zamyka. Trzymane POZA ekranem, bez paska zadan.
    """
    hinst = kernel32.GetModuleHandleW(None)
    wc = WNDCLASSW()
    wc.style = 0
    wc.lpfnWndProc = ctypes_mod.cast(app._wndproc, ctypes_mod.c_void_p)
    wc.cbClsExtra = 0
    wc.cbWndExtra = 0
    wc.hInstance = hinst
    wc.hIcon = None
    wc.hCursor = None
    wc.hbrBackground = None
    wc.lpszMenuName = None
    wc.lpszClassName = TRAY_CLASS_NAME
    if not user32.RegisterClassW(byref(wc)):
        print(f"[ERROR] RegisterClassW (tray): {kernel32.GetLastError()}", file=sys.stderr)
        return None
    hwnd = user32.CreateWindowExW(
        WS_EX_TOOLWINDOW, TRAY_CLASS_NAME, "ScreenDrawerTray", WS_POPUP,
        -2000, -2000, 1, 1, None, None, hinst, None)
    if not hwnd:
        print(f"[ERROR] CreateWindowExW (tray): {kernel32.GetLastError()}", file=sys.stderr)
    return hwnd


def _icon_path():
    """
    Sciezka do icon.ico. Szukamy obok .exe, obok skryptu, potem w _MEIPASS
    (PyInstaller onefile). Brak pliku -> None (uzyjemy ikony systemowej).
    Dodatkowo sprawdzamy podaną ikonę generowaną przez Gemini.
    """
    # 1. Sprawdź ikonę wygenerowaną przez Gemini
    gemini_icon = r"C:\\Users\\adamg\\AppData\\Roaming\\Hermes\\composer-images\\Gemini_Generated_Image_gdlmb4gdlmb4gdlm_bb2e60.ico"
    if os.path.isfile(gemini_icon):
        return gemini_icon
    # 2. Reszta logiczna (icon.ico)
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(
            os.path.dirname(os.path.abspath(sys.executable)), "icon.ico"))
    candidates.append(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "icon.ico"))
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "icon.ico"))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _load_tray_icon():
    """Ikona z pliku icon.ico; gdy brak lub blad - standardowa ikona systemowa."""
    path = _icon_path()
    if path:
        hicon = user32.LoadImageW(None, path, IMAGE_ICON, 0, 0,
                                  LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if hicon:
            print(f"[OK] Ikona tray z pliku: {path}", file=sys.stderr)
            return hicon
        print(f"[WARN] LoadImageW nie wczytal {path} "
              f"(err={kernel32.GetLastError()}) - uzywam ikony systemowej",
              file=sys.stderr)
    else:
        print("[WARN] Brak pliku icon.ico - uzywam ikony systemowej", file=sys.stderr)
    return user32.LoadIconW(None, ctypes_mod.c_void_p(IDI_APPLICATION))


def tray_add(app):
    """Dodaje ikone aplikacji do zasobnika (kolo zegara)."""
    if _tray["added"]:
        return True
    hwnd = tray_create_window(app)
    if not hwnd:
        return False
    _tray["icon"] = _load_tray_icon()

    nid = NOTIFYICONDATAW()
    nid.cbSize = ctypes_mod.sizeof(NOTIFYICONDATAW)
    nid.hWnd = hwnd
    nid.uID = TRAY_ICON_ID
    nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
    nid.uCallbackMessage = TRAY_CALLBACK_MSG
    nid.hIcon = _tray["icon"]
    nid.szTip = "Draw: CTRL+ALT+LMB | Clear: Release CTRL/ALT | Close: Right-Click"

    ok = bool(shell32.Shell_NotifyIconW(NIM_ADD, byref(nid)))
    _tray["added"] = ok
    _tray["hwnd"] = hwnd
    _tray["nid"] = nid
    if ok:
        print("[OK] Ikona w zasobniku dodana (prawy przycisk = menu z 'Zamknij')",
              file=sys.stderr)
    else:
        print(f"[WARN] Nie udalo sie dodac ikony w zasobniku: "
              f"{kernel32.GetLastError()}", file=sys.stderr)
    return ok


def tray_remove():
    """Usuwa ikone z zasobnika (przy zamykaniu aplikacji)."""
    if not _tray["added"]:
        return
    nid = _tray["nid"]
    nid.uFlags = 0
    shell32.Shell_NotifyIconW(NIM_DELETE, byref(nid))
    if _tray["hwnd"]:
        user32.DestroyWindow(_tray["hwnd"])
    _tray.update(added=False, hwnd=None, nid=None)
    print("[LOG] Ikona w zasobniku usunieta", file=sys.stderr)


def tray_show_menu(app):
    """Menu pod prawym przyciskiem na ikonie (na razie: Zamknij)."""
    hwnd = _tray["hwnd"]
    if not hwnd:
        return
    pt = POINT()
    user32.GetCursorPos(byref(pt))
    menu = user32.CreatePopupMenu()
    user32.AppendMenuW(menu, MF_STRING, ctypes_mod.c_void_p(ID_MENU_CLOSE), "Close")
    # sztuczka Microsoftu: bez SetForegroundWindow menu nie zamyka sie po kliknieciu obok
    user32.SetForegroundWindow(hwnd)
    user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_BOTTOMALIGN,
                          pt.x, pt.y, 0, hwnd, None)
    user32.PostMessageW(hwnd, WM_NULL, 0, 0)
    user32.DestroyMenu(menu)


def set_dpi_awareness():
    """Per-monitor v2 jesli dostepne. MUSI byc wywolane przed utworzeniem okien."""
    try:
        if user32.SetProcessDpiAwarenessContext(
                ctypes_mod.c_void_p(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)):
            return "per-monitor-v2"
    except Exception:
        pass
    try:
        if shcore and shcore.SetProcessDpiAwareness(2) == 0:
            return "per-monitor"
    except Exception:
        pass
    try:
        user32.SetProcessDPIAware()
        return "system"
    except Exception:
        return "unaware"


def enumerate_monitors():
    """Lista monitorow: {'hmon','device','rect','primary','dpi',...}."""
    mons = []

    def cb(hmon, hdc, lprc, data):
        mi = MONITORINFOEXW()
        mi.cbSize = ctypes_mod.sizeof(MONITORINFOEXW)
        if user32.GetMonitorInfoW(hmon, byref(mi)):
            dpi = 96
            if shcore:
                try:
                    dx, dy = c_uint(), c_uint()
                    if shcore.GetDpiForMonitor(hmon, MDT_EFFECTIVE_DPI,
                                               byref(dx), byref(dy)) == 0:
                        dpi = int(dx.value)
                except Exception:
                    pass
            r = mi.rcMonitor
            mons.append({"hmon": hmon,
                         "device": mi.szDevice,
                         "rect": (r.left, r.top, r.right, r.bottom),
                         "primary": bool(mi.dwFlags & 1),
                         "dpi": dpi,
                         "hwnd": None, "mem_dc": None, "mem_bmp": None,
                         "paint_count": 0})
        return True

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
    return mons


class DrawOverlayWindow:
    """Overlay: jedno okno na monitor, wspolna lista kresek w ukladzie ekranu."""

    def __init__(self):
        self.monitors = []
        self.hwnd = None
        self.segments = []
        self.drawing = False
        self._last_pt = None
        self._ctrl_prev = False
        self._lmb_prev = False
        self._quit = False
        self._class_registered = False
        self._rebuild_request = None
        self._capturing = False
        self._phys_lmb = False          # PRAWdziwy stan przycisku (z hooka)
        self.paint_calls = 0
        self.paint_counts = []
        self.rebuild_count = 0
        self._wndproc = WNDPROC(self._on_message)

    # ---------- wejscie (nadpisywalne w testach) ----------
    def _is_ctrl_down(self):
        """
        Klawisz rysowania = CTRL + ALT (nazwa metody zostaje dla zgodnosci z testami,
        ktore podstawiaja wlasne, skryptowane wejscie).

        Samo CTRL nic nie robi: nie rysuje i nie blokuje klikniec, wiec zwykle
        Ctrl+klik w innych programach dziala bez zmian. Dopiero CTRL+ALT+LMB rysuje
        i na czas trzymania kombinacji blokuje klikniecia (pulpit nie reaguje).
        """
        ctrl = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
        alt = bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000)
        return ctrl and alt

    def _is_lmb_down(self):
        # Podczas blokowania zdarzenia myszy nie trafiaja do kolejki, wiec
        # GetAsyncKeyState(VK_LBUTTON) ich nie widzi - bierzemy stan z hooka.
        if self._capturing:
            return bool(self._phys_lmb)
        return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

    def _is_esc_down(self):
        return bool(user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000)

    def _cursor_pos(self):
        pt = POINT()
        if user32.GetCursorPos(byref(pt)):
            return (pt.x, pt.y)
        return None

    # ---------- procedura okna ----------
    def _on_message(self, hwnd, message, wparam, lparam):
        if message == TRAY_CALLBACK_MSG:
            # zdarzenia na ikonie w zasobniku
            if lparam in (WM_RBUTTONUP, WM_CONTEXTMENU):
                tray_show_menu(self)
            return 0
        if message == WM_COMMAND:
            if (wparam & 0xFFFF) == ID_MENU_CLOSE:
                print("[INFO] Menu ikony: Zamknij -> koncze", file=sys.stderr)
                self._quit = True
            return 0
        if message == WM_CLOSE:
            print("[INFO] Zamkniecie okna -> koncze", file=sys.stderr)
            self._quit = True
            return 0
        if message == WM_DESTROY:
            return 0
        if message == WM_DISPLAYCHANGE:
            self._rebuild_request = "WM_DISPLAYCHANGE"
            return 0
        if message == WM_DPICHANGED:
            self._rebuild_request = "WM_DPICHANGED"
            return 0
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    # ---------- okna ----------
    def _log_monitors(self):
        for m in self.monitors:
            left, top, right, bottom = m["rect"]
            print(f"[INFO] Monitor {m['device']} rect=({left},{top},{right},{bottom}) "
                  f"rozmiar={right-left}x{bottom-top} primary={m['primary']} dpi={m['dpi']}",
                  file=sys.stderr)

    def _register_class(self):
        if self._class_registered:
            return True
        hinst = kernel32.GetModuleHandleW(None)
        wc = WNDCLASSW()
        wc.style = 0
        wc.lpfnWndProc = ctypes_mod.cast(self._wndproc, ctypes_mod.c_void_p)
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = hinst
        wc.hIcon = None
        wc.hCursor = None
        wc.hbrBackground = None
        wc.lpszMenuName = None
        wc.lpszClassName = CLASS_NAME
        if not user32.RegisterClassW(byref(wc)):
            print(f"[ERROR] RegisterClassW: {kernel32.GetLastError()}", file=sys.stderr)
            return False
        self._class_registered = True
        return True

    def _create_windows(self):
        hinst = kernel32.GetModuleHandleW(None)
        for m in self.monitors:
            left, top, right, bottom = m["rect"]
            w, h = right - left, bottom - top
            hwnd = user32.CreateWindowExW(
                EX_STYLE, CLASS_NAME, "", WS_POPUP | WS_VISIBLE,
                left, top, w, h, None, None, hinst, None)
            if not hwnd:
                print(f"[ERROR] CreateWindowExW {m['device']}: "
                      f"{kernel32.GetLastError()}", file=sys.stderr)
                return False
            user32.SetLayeredWindowAttributes(hwnd, KEY_COLOR, 0, LWA_COLORKEY)
            screen_dc = user32.GetDC(hwnd)
            m["mem_dc"] = gdi32.CreateCompatibleDC(screen_dc)
            m["mem_bmp"] = gdi32.CreateCompatibleBitmap(screen_dc, w, h)
            gdi32.SelectObject(m["mem_dc"], m["mem_bmp"])
            user32.ReleaseDC(hwnd, screen_dc)
            m["hwnd"] = hwnd
            m["paint_count"] = 0

        self.hwnd = self.monitors[0]["hwnd"]
        self.paint_counts = [0] * len(self.monitors)
        user32.SetTimer(self.hwnd, TIMER_ID, TIMER_MS, None)
        print(f"[OK] Okna overlay: {len(self.monitors)} (po jednym na monitor, "
              f"ukryte z paska zadan)", file=sys.stderr)
        self._paint()
        set_input_capture(self, self._is_ctrl_down())
        tray_add(self)
        return True

    def _destroy_windows(self):
        for mon in self.monitors:
            try:
                if mon.get("hwnd"):
                    user32.KillTimer(mon["hwnd"], TIMER_ID)
                    user32.DestroyWindow(mon["hwnd"])
                    mon["hwnd"] = None
                if mon.get("mem_dc"):
                    gdi32.DeleteDC(mon["mem_dc"])
                    mon["mem_dc"] = None
                if mon.get("mem_bmp"):
                    gdi32.DeleteObject(mon["mem_bmp"])
                    mon["mem_bmp"] = None
            except Exception as e:
                print(f"[WARN] Blad niszczenia okna: {e}", file=sys.stderr)

    def _rebuild(self, reason):
        print(f"[INFO] {reason} -> odtwarzam okna overlay", file=sys.stderr)
        self._destroy_windows()
        self.monitors = enumerate_monitors()
        if not self.monitors:
            print("[ERROR] Po zmianie ekranow brak monitorow -> koncze", file=sys.stderr)
            self._quit = True
            return False
        self._log_monitors()
        if not self._register_class() or not self._create_windows():
            self._quit = True
            return False
        self.rebuild_count += 1
        return True

    def create(self):
        self.monitors = enumerate_monitors()
        if not self.monitors:
            print("[ERROR] Nie znaleziono zadnego monitora", file=sys.stderr)
            return False
        self._log_monitors()
        if not self._register_class():
            return False
        start_mouse_hook(self)
        return self._create_windows()

    # ---------- rysowanie ----------
    def _monitor_client_segments(self, mon):
        left, top, right, bottom = mon["rect"]
        out = []
        for x1, y1, x2, y2 in self.segments:
            if (max(x1, x2) < left or min(x1, x2) > right
                    or max(y1, y2) < top or min(y1, y2) > bottom):
                continue
            out.append((x1 - left, y1 - top, x2 - left, y2 - top))
        return out

    def _paint_monitor(self, mon, index):
        if not mon["mem_dc"] or not mon["hwnd"]:
            return
        left, top, right, bottom = mon["rect"]
        w, h = right - left, bottom - top

        brush = gdi32.CreateSolidBrush(KEY_COLOR)
        user32.FillRect(mon["mem_dc"], byref(RECT(0, 0, w, h)), brush)
        gdi32.DeleteObject(brush)

        segs = self._monitor_client_segments(mon)
        if segs:
            width = max(1, round(PEN_WIDTH_BASE * mon["dpi"] / 96.0))
            pen = gdi32.CreatePen(PS_SOLID, width, PEN_COLOR)
            old = gdi32.SelectObject(mon["mem_dc"], pen)
            for x1, y1, x2, y2 in segs:
                gdi32.MoveToEx(mon["mem_dc"], int(x1), int(y1), None)
                gdi32.LineTo(mon["mem_dc"], int(x2), int(y2))
            gdi32.SelectObject(mon["mem_dc"], old)
            gdi32.DeleteObject(pen)

        hdc = user32.GetDC(mon["hwnd"])
        gdi32.BitBlt(hdc, 0, 0, w, h, mon["mem_dc"], 0, 0, SRCCOPY)
        user32.ReleaseDC(mon["hwnd"], hdc)

        mon["paint_count"] += 1
        if index < len(self.paint_counts):
            self.paint_counts[index] = mon["paint_count"]
        self.paint_calls += 1

    def _paint(self):
        for i, mon in enumerate(self.monitors):
            self._paint_monitor(mon, i)

    # ---------- logika ----------
    def _on_timer(self):
        if self._is_esc_down():
            print("[INFO] ESC -> koncze", file=sys.stderr)
            self._quit = True
            return False

        ctrl = self._is_ctrl_down()
        lmb = self._is_lmb_down()
        changed = False

        set_input_capture(self, ctrl)

        if self._ctrl_prev and not ctrl:
            if self.segments or self.drawing:
                changed = True
            self.segments.clear()
            self.drawing = False
            self._last_pt = None
            print("[LOG] CTRL/ALT puszczony -> reset", file=sys.stderr)

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
                    print(f"[LOG] Drag: {self.segments[-1]}", file=sys.stderr)
        elif self.drawing:
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
        while True:
            if not any(user32.IsWindow(m["hwnd"]) for m in self.monitors if m["hwnd"]):
                print("[INFO] Brak okien overlay -> koncze", file=sys.stderr)
                break

            if user32.PeekMessageW(byref(msg), None, 0, 0, PM_REMOVE):
                if msg.message == WM_QUIT:
                    break
                user32.TranslateMessage(byref(msg))
                user32.DispatchMessageW(byref(msg))
                if self._quit:
                    break
                if self._rebuild_request:
                    reason = self._rebuild_request
                    self._rebuild_request = None
                    if not self._rebuild(reason):
                        break
                    continue
                if msg.message == WM_TIMER and msg.hwnd == self.hwnd:
                    if self._on_timer():
                        self._paint()
            else:
                time.sleep(0.002)

        self._cleanup()
        print("[INFO] Zamknieto", file=sys.stderr)
        return 0

    def _cleanup(self):
        try:
            tray_remove()
            self._destroy_windows()
        except Exception as e:
            print(f"[WARN] Blad sprzatania: {e}", file=sys.stderr)


def acquire_single_instance():
    kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return kernel32.GetLastError() != ERROR_ALREADY_EXISTS


BANNER = """
=========================================================
  Screen Drawer - rysowanie po ekranie
---------------------------------------------------------
  CTRL + ALT + LMB (przytrzymaj wszystkie)  ->  rysujesz
  pusc CTRL lub ALT                         ->  rysunek znika
  prawy przycisk na ikonie kolo zegara      ->  menu (Zamknij)
  ESC                                       ->  zamknij aplikacje

  Samo CTRL nic nie robi - normalny Ctrl+klik dziala jak zawsze.
  Podczas trzymania CTRL+ALT klikniecia nie docieraja na pulpit.
=========================================================
"""


def main():
    aware = set_dpi_awareness()
    print(BANNER, file=sys.stderr)
    print(f"[INFO] DPI awareness: {aware}", file=sys.stderr)
    print(f"[INFO] Log: {_LOG_PATH}", file=sys.stderr)
    if not acquire_single_instance():
        print("[ERROR] Screen Drawer juz dziala (jedna instancja).", file=sys.stderr)
        # Bez konsoli komunikat musi byc okienkiem - inaczej wyglada to jak awaria.
        user32.MessageBoxW(
            None,
            "Screen Drawer juz dziala.\n\n"
            "Poszukaj ikony kolo zegara (zasobnik systemowy).\n"
            "Prawy przycisk na ikonie -> Zamknij.",
            "Screen Drawer", MB_OK | MB_ICONINFORMATION | MB_SETFOREGROUND)
        return 1
    return DrawOverlayWindow().run()


if __name__ == "__main__":
    sys.exit(main())
