#!/usr/bin/env python3
"""
Test rysowania PRAWDZIWYM wejsciem: syntetyczne CTRL + LMB + ruch kursora.

To jest ta sciezka, ktora naprawde zawodzi: aplikacja czyta stan klawiszy przez
GetAsyncKeyState i pozycje przez GetCursorPos. Testy skryptowane (podmieniajace te
metody) NIE sprawdzaja tego i dlatego przepuscily blad: hook myszy zjadal
WM_LBUTTONDOWN, przez co GetAsyncKeyState(VK_LBUTTON) nie widzial wcisnietego
przycisku i nic sie nie rysowalo.

Uruchamia aplikacje (domyslnie dist/screen_drawer_window.exe, mozna podac .py),
wykonuje CTRL+LMB drag i sprawdza w logu aplikacji czy powstal ruch rysowania.

Uruchom:
  python tests/selftest_real_drawing.py                  (testuje .exe)
  python tests/selftest_real_drawing.py screen_drawer_window.py   (testuje .py)
"""

import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes, byref, POINTER, c_int, c_void_p

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

user32 = ctypes.windll.user32
user32.SetCursorPos.argtypes = [c_int, c_int]
user32.GetCursorPos.argtypes = [POINTER(wintypes.POINT)]
user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                               wintypes.DWORD, c_void_p]
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, c_void_p]

VK_CONTROL = 0x11
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

LOG_PATH = os.path.join(os.environ.get("TEMP", ROOT), "sd_real_drawing.log")
STROKE = [(300, 300), (420, 340), (540, 300), (660, 380), (780, 420), (900, 460)]


def kill_project_processes():
    # WAZNE: nie zabijamy siebie - nasza wlasna linia polecen zawiera nazwe pliku aplikacji
    mypid = os.getpid()
    ps = (f'Get-CimInstance Win32_Process | Where-Object {{ $_.ProcessId -ne {mypid} -and '
          '($_.Name -like "screen_drawer*" -or '
          '($_.Name -eq "python.exe" -and $_.CommandLine -like "*screen_drawer_window*")) }} | '
          'ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }')
    subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps],
                   capture_output=True, text=True, timeout=60)
    time.sleep(1.0)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "dist", "screen_drawer_window.exe")
    if not os.path.isabs(target):
        target = os.path.join(ROOT, target)
    if not os.path.exists(target):
        print(f"[REAL] brak pliku: {target}")
        return 2

    kill_project_processes()

    if target.lower().endswith(".py"):
        cmd = [sys.executable, target]
    else:
        cmd = [target]

    log = open(LOG_PATH, "w", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    print(f"[REAL] uruchomiono: {os.path.basename(target)} (pid={proc.pid})")
    try:
        time.sleep(6)

        pt = wintypes.POINT()
        user32.GetCursorPos(byref(pt))
        saved = (pt.x, pt.y)

        user32.SetCursorPos(*STROKE[0])
        time.sleep(0.3)
        user32.keybd_event(VK_CONTROL, 0, 0, None)          # CTRL w dol
        time.sleep(0.5)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, None)   # LMB w dol
        time.sleep(0.25)
        for p in STROKE[1:]:
            user32.SetCursorPos(*p)
            time.sleep(0.15)
        time.sleep(0.2)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, None)
        time.sleep(0.3)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, None)
        time.sleep(0.6)
        user32.SetCursorPos(*saved)

        log.flush()
        text = open(LOG_PATH, encoding="utf-8", errors="replace").read()

        started = "Start rysowania" in text
        drags = text.count("Drag:")
        capture_log = "Blokuje klikniecia" in text or "Przechwytuje mysz" in text

        print(f"[REAL] log: start_rysowania={started}  ruchow(Drag)={drags}  "
              f"blokowanie={capture_log}")
        print("[REAL] --- zdarzenia z logu aplikacji ---")
        for line in text.splitlines():
            if "[LOG]" in line or "[WARN]" in line or "[ERROR]" in line:
                print("        " + line.strip())
        ok = started and drags >= 2
        print("[REAL] RESULT=" + ("PASS" if ok else "FAIL - prawdziwe wejscie nie rysuje"))
        return 0 if ok else 1
    finally:
        log.close()
        kill_project_processes()


if __name__ == "__main__":
    sys.exit(main())
