import pytest
from screen_drawer_window import DrawOverlayWindow


def test_window_creates_successfully():
    """Okno powinno się utworzyć bez błędów."""
    # Test only that the class exists - window creation requires display and is complex
    overlay = DrawOverlayWindow()
    assert overlay is not None
