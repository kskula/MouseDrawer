# Screen Drawer 🎨

Drawing directly on the desktop with a transparent overlay (one window per monitor). You see and use the normal desktop underneath – you only draw when you want to.

## 🎮 Controls

| Action | Effect |
|--------|--------|
| **CTRL + ALT + LMB** (hold all three) | Draw a red line under the cursor |
| Release **CTRL** or **ALT** | All drawings disappear |
| **Close** | Close via tray menu only (no ESC key) |


*Holding just CTRL does nothing – it doesn’t block clicks, so normal Ctrl‑clicks (e.g. multi‑selecting files) still work.*

While **CTRL + ALT** is held, mouse clicks never reach the desktop (no icons selected, no selection rectangles). The drawing does not alter what’s underneath.

## ✨ Features

- One overlay per monitor (`EnumDisplayMonitors`) – works on secondary screens.
- DPI‑per‑monitor v2 – correct pixels even with 150 %/200 % scaling.
- Click blocking only while **CTRL + ALT** is held (`WH_MOUSE_LL` in a dedicated thread).
- Automatic window recreation after display changes (`WM_DISPLAYCHANGE`, `WM_DPICHANGED`).
- Overlay windows are out of Alt‑Tab and the taskbar (`WS_EX_TOOLWINDOW`).
- Single instance (named mutex) – second launch just reports and exits.
- Clean exit – no “zombie” process; only the console window remains visible.
- No external libraries beyond standard `ctypes`.

## 📋 Requirements

- Windows 10/11
- Python 3.8+ (tested on 3.12) – `pywin32` is **not** required.

## 🚀 Running

```bash
# Packed version (recommended) – double‑click works too
dist\screen_drawer_window.exe

# From source
python screen_drawer_window.py
```
On startup a console window appears with logs and instructions (the only visible UI).

## 🔨 Building the .exe

```bash
pyinstaller --noconfirm --clean screen_drawer_window.spec
# Result: dist\screen_drawer_window.exe
```
After every code change you must rebuild – the `dist/` binary does not update automatically.

## 🧪 Tests

```bash
python tests/selftest_multi_monitor.py   # per‑monitor windows, DPI, geometry, window rebuilds
python tests/selftest_input_capture.py   # enable/disable input capture styles
python tests/selftest_click_blocking.py  # verifies clicks don’t reach the desktop (window probe)
python tests/selftest_real_drawing.py    # real drawing with genuine mouse input
```
All tests launch real windows and perform actual GDI drawing; inputs are synthetic, so they don’t disturb your user interface.
To test the built executable:

```bash
python tests/selftest_real_drawing.py dist\screen_drawer_window.exe
```
`tests/probe_click_routing.py` is diagnostic – it shows that a window with `WS_EX_TRANSPARENT` alone isn’t enough; the color‑key layer is required.

## 🏗 How It Works (short)

- Overlay windows: `WS_POPUP | WS_VISIBLE`, extended style `TOPMOST | TOOLWINDOW | LAYERED | TRANSPARENT | NOACTIVATE`; background painted with a color key (`LWA_COLORKEY`) → transparent, only the lines are visible.
- Drawing: off‑screen buffer per monitor (`CreateCompatibleDC` + `BitBlt`), refreshed on timer (~16 ms) and on display changes.
- Input: `GetAsyncKeyState` for **CTRL+ALT** combo; `GetCursorPos` for mouse position.
- Click blocking: low‑level hook `WH_MOUSE_LL` in a dedicated thread that consumes `WM_LBUTTONDOWN` while **CTRL+ALT** is held, so the click never reaches the desktop.
- Window recreation: `WM_DISPLAYCHANGE`/`WM_DPICHANGED` trigger a clean rebuild of all overlay windows; no zombie windows remain after exit.

## ⚠️ Known Limitations

- While holding **CTRL + ALT**, clicks are blocked globally (not just on the desktop).
- Changing line color/thickness and saving drawings to file – not yet implemented.
- Autostart via Windows requires manual shortcut placement in `shell:startup`.

## 📁 Project Structure

```
.screenshootapp/
├── screen_drawer_window.py     # main program
├── screen_drawer_window.spec   # PyInstaller spec
├── build_exe.bat               # helper script for building
├── requirements.txt            # no external dependencies
├── README.md                   # this file
├── tests/                      # automated tests
├── dist/screen_drawer_window.exe
└── _archive/                   # old ZIP snapshots
```

## 📄 License

**Freeware – use, modify, and distribute for free. No warranty is provided.**

---

*Author:* Adam Gałęza
