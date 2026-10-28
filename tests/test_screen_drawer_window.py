import pytest
from screen_drawer_window import DrawOverlayWindow


def test_window_creates_successfully():
    """Okno powinno się utworzyć bez błędów."""
    from screen_drawer_window import DrawOverlayWindow
    
    # Sprawdź że klasa istnieje i ma wymagane metody
    overlay = DrawOverlayWindow()
    assert overlay is not None, "DrawOverlayWindow instance created"
    assert hasattr(overlay, 'create'), "Has create method"
    assert hasattr(overlay, 'run'), "Has run method"
    
    # Mock test - sprawdzamy że metody są callable (nie testujemy rzeczywistego okna w CI)
    import inspect
    assert callable(getattr(overlay, 'create', None)), "create is callable"
    assert callable(getattr(overlay, 'run', None)), "run is callable"
    
    # Sprawdź strukturę klasy zgodnie z specyfikacją
    assert hasattr(overlay, '_ctrl_prev'), "Has _ctrl_prev state for edge detection"
    assert hasattr(overlay, '_lmb_prev'), "Has _lmb_prev state for edge detection"
    assert hasattr(overlay, 'segments'), "Has segments list for drawing"
    assert hasattr(overlay, 'drawing'), "Has drawing state"
