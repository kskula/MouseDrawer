# Screen Drawer Window 🎨

Aplikacja rysująca bezpośrednio na ekranie użytkownika. Przytrzymaj CTRL + kliknij LMB, aby rysować. Puść CTRL, aby resetować canvas.

## ✨ Cechy
- Rysowanie natychmiastowe po ekranie (bez okna)
- Minimalne, przezroczyste okno sterujące na górze ekranu
- Reset canvas przy puszczeniu CTRL
- Tryb usługi opcjonalny (dla automatyzacji)

## 📋 Wymagania
- **OS**: Windows 10/11
- **Python**: 3.8+
- **Zależności**: pywin32, numpy

## 🛠 Instalacja

### Opcja 1: Ręczna instalacja
```bash
pip install -r requirements.txt
```

### Opcja 2: Użycie venv (zalecane)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 🚀 Uruchomienie

### Jako aplikacja (okienkowa)
```bash
python screen_drawer_window.py
```

### Jako usługa
```bash
start_service.bat
```

## 🔨 Build .exe

### Użycie build_exe.bat:
```bash
build_exe.bat
```

Plik `.exe` znajduje się w `dist/ScreenDrawerWindow.exe`

### Ręczny build (pip + pyinstaller):
```bash
pip install pyinstaller
pyinstaller --onefile screen_drawer_window.py
# .exe będzie w dist/ScreenDrawerWindow.exe
```

## 📖 Użycie aplikacji

1. **Uruchom aplikację** - wyskakuje minimalne, przezroczyste okno sterujące na górze ekranu
2. **Przytrzymaj CTRL** i kliknij lewym przyciskiem myszy (LMB)
3. **Rysuj** pociągając kursorem (dopóki trzymasz CTRL) - linie pojawią się natychmiast po ekranie
4. **Puść CTRL** - wszystkie rysowane linie znikają, canvas jest resetowany

### Szybkie uruchomienie .exe
```bash
dist/ScreenDrawerWindow.exe
# lub dwukrotny klik w plik .exe
```

## 🛠️ Tryb Usługi (opcjonalny)

Aplikacja może działać jako usługa Windows dla automatyzacji:

### Instalacja usługi:
```bash
install_service.bat
```

### Uruchomienie/Stopowanie usługi:
- `start_service.bat` - uruchamia usługę
- `stop_service.bat` - zatrzymuje usługę

## 📁 Pliki projektu

```
.screenshootapp/
├── .gitignore              # Lista pomijanych plików
├── README.md               # Dokumentacja (ten plik)
├── requirements.txt        # Zależności Pythona
├── build_exe.bat          # Skrypt budowania .exe
├── install_service.bat    # Instalacja usługi Windows
├── start_service.bat      # Uruchomienie usługi
├── stop_service.bat       # Zatrzymanie usługi
├── screen_drawer_window.py # Główny kod aplikacji (okienkowej)
├── screen_drawer_service.py # Kod usługi (opcjonalny)
└── tests/
    └── test_screen_drawer_window.py  # Testy jednostkowe
```

## 🧪 Testy

```bash
python -m pytest tests/ -v
```

## ⚠️ Uwagi
- Aplikacja wymaga uprawnień administratora do rysowania na ekranie
- Rysowanie pojawia się natychmiast na głównym monitorze
- Należy uważać - linie mogą być trwałe w zależności od ustawień systemu

## 📄 Licencja

N/A

## 👨‍💻 Autor

Adam Gałęza
