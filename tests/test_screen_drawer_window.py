import pytest
from screen_drawer_window import DrawOverlayWindow


def test_window_creates_successfully():
    """Okno powinno się utworzyć bez błędów."""
    from screen_drawer_window import DrawOverlayWindow
    
    # Sprawdź że klasa istnieje i ma wymagane metody
    overlay = DrawOverlayWindow()
    assert overlay is not None
    assert hasattr(overlay, 'create')
    assert hasattr(overlay, 'run')
    
    # Mock test - sprawdzamy że metody mają poprawny typ (nie testujemy rzeczywistego okna w CI)
    import inspect
    assert callable(getattr(overlay, 'create', None))
