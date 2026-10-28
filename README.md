# Screen Drawer Window

Aplikacja rysująca po ekranie: przytrzymaj CTRL + kliknij LMB = rysuj; puść CTRL = reset.

## Wymagania
- Windows 10/11
- Python 3.8+
- pywin32

## Instalacja

1. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

2. Uruchom jako normalna aplikacja:
```bash
python screen_drawer_window.py
```

## Build .exe
```bash
build_exe.bat
```

Plik `.exe` znajduje się w `dist/ScreenDrawerWindow.exe`

## Użycie
1. Uruchom aplikację - wyskakuje minimalne, przezroczyste okno na górze ekranu
2. Przytrzymaj **CTRL** i kliknij lewym przyciskiem myszy
3. Rysuj pociągając kursorem (dopóki trzymasz CTRL)
4. Puść **CTRL** - wszystkie linie znikają

## Uruchomienie .exe
```bash
dist\ScreenDrawerWindow.exe
```
