# Screen Drawer 🎨

Rysowanie bezpośrednio po ekranie: przezroczysty overlay (jedno okno na każdy monitor),
przez który widać i normalnie używa się pulpitu. Rysujesz tylko wtedy, gdy chcesz.

## 🎮 Sterowanie

| Akcja | Efekt |
|---|---|
| **CTRL + ALT + LMB** (przytrzymaj wszystkie trzy) | rysujesz czerwoną kreskę pod kursorem |
| puść **CTRL** albo **ALT** | cały rysunek znika |
| **ESC** | zamyka aplikację |
| X na oknie konsoli | zamyka aplikację |

**Samo CTRL nic nie robi** — nie rysuje i nie blokuje kliknięć, więc zwykły Ctrl+klik
(np. wielokrotne zaznaczanie plików) działa normalnie, także gdy aplikacja chodzi.

Dopóki trzymasz CTRL+ALT, kliknięcia **nie docierają** do pulpitu (nie zaznaczają się ikony,
nie robi się ramka zaznaczenia) — czyli rysowanie nie zmienia stanu tego, co pod spodem.

## ✨ Cechy

- **Jeden overlay na każdy monitor** (`EnumDisplayMonitors`) — działa też na drugim ekranie
- **DPI per-monitor v2** — poprawne piksele także przy skalowaniu 150 %/200 %
- **Blokada kliknięć** tylko na czas trzymania CTRL+ALT (`WH_MOUSE_LL` na własnym wątku,
  więc kursor nie zwalnia)
- **Auto-odtwarzanie okien** po zmianie konfiguracji ekranów (`WM_DISPLAYCHANGE`, `WM_DPICHANGED`)
- Okna overlay są poza paskiem zadań i poza Alt-Tab (`WS_EX_TOOLWINDOW`)
- **Jedna instancja** (nazwany mutex) — drugie uruchomienie tylko się zgłasza i wychodzi
- **Czyste zamykanie** — brak „zombi” (procesu bez okien); okno konsoli jest jedynym widocznym
- Zero dodatkowych bibliotek: tylko `ctypes` ze standardowej biblioteki Pythona

## 📋 Wymagania

- **Windows 10/11**
- **Python 3.8+** (rozwojowo testowane na 3.12) — `pywin32` nie jest potrzebny

## 🚀 Uruchomienie

```bash
# wersja spakowana (zalecana) - dwuklik też działa
dist\screen_drawer_window.exe

# albo ze źródeł
python screen_drawer_window.py
```

Przy starcie otwiera się okno konsoli z logami i instrukcją (to jedyne widoczne okno).

## 🔨 Budowa .exe

```bash
pyinstaller --noconfirm --clean screen_drawer_window.spec
# wynik: dist\screen_drawer_window.exe
```

Po **każdej** zmianie w kodzie trzeba przebudować `.exe` — binarka w `dist/` nie aktualizuje się sama.

## 🧪 Testy

```bash
python tests/selftest_multi_monitor.py   # okna per monitor, DPI, geometria, rebuild okien
python tests/selftest_input_capture.py   # style okien: przechwytywanie włącz/wyłącz
python tests/selftest_click_blocking.py  # czy klik REALNIE nie przechodzi na pulpit (okno-sonda)
python tests/selftest_real_drawing.py    # czy rysuje przy PRAWDZIWYM wejściu (CTRL+ALT+LMB)
```

Wszystkie testy uruchamiają prawdziwe okna i prawdziwe rysowanie GDI; wejście jest syntetyczne,
więc nie ruszają myszy ani klawiatury użytkownika. Test na `.exe`:

```bash
python tests/selftest_real_drawing.py dist\screen_drawer_window.exe
```

`tests/probe_click_routing.py` to diagnostyka (pokazuje, że okno z color key przepuszcza kliknięcia
— to był powód, dla którego sama flaga `WS_EX_TRANSPARENT` nie wystarczała).

## 🏗 Jak to działa (skrót)

- Okna overlay: `WS_POPUP | WS_VISIBLE`, ex-style `TOPMOST | TOOLWINDOW | LAYERED | TRANSPARENT | NOACTIVATE`,
  tło malowane kolorem klucza (`LWA_COLORKEY`) → przezroczyste, widać tylko kreski
- Rysowanie: bufor offscreen na każdy monitor (`CreateCompatibleDC` + `BitBlt`), przerysowanie po zmianie
- Wejście: `GetAsyncKeyState` (kombinacja) + `GetCursorPos`, timer ~16 ms
- Blokada kliknięć: hook `WH_MOUSE_LL` na osobnym wątku z ciasną pętlą komunikatów; stan przycisku
  czytany z hooka (zjedzone `WM_LBUTTONDOWN` nie trafia do kolejki, więc `GetAsyncKeyState` go nie widzi)
- Odporność: `WM_CLOSE` kończy aplikację, `WM_DISPLAYCHANGE`/`WM_DPICHANGED` odtwarzają okna,
  brak okien overlay → aplikacja kończy się sama (koniec „zombi”)

## ⚠️ Znane ograniczenia

- Podczas trzymania CTRL+ALT kliknięcia są zablokowane **globalnie** (nie tylko na pulpicie)
- Zmiana koloru/grubości kreski, zapis rysunku do pliku — jeszcze nie ma
- Autostart z Windows trzeba dodać samodzielnie (skrót w `shell:startup`)

## 📁 Pliki projektu

```
.screenshootapp/
├── screen_drawer_window.py     # cały program (jedno źródło)
├── screen_drawer_window.spec   # definicja builda PyInstaller
├── build_exe.bat               # pomocniczy skrypt budowania
├── requirements.txt            # nic nie jest wymagane poza Pythonem
├── README.md                   # ten plik
├── tests/                      # testy (patrz wyżej)
├── dist/screen_drawer_window.exe
└── _archive/                   # snapshoty wcześniejszych wersji (ZIP z .exe)
```

## 📄 Licencja

N/A

## 👨‍💻 Autor

Adam Gałęza
