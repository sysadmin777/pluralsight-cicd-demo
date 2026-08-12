"""Minimal test suite — exists so the build gate has a real test step."""
import app


def test_mask_hides_middle():
    assert app.mask("supersecretkey123") == "su*************23"


def test_mask_short_values_fully_hidden():
    assert app.mask("abc") == "********"


def test_release_notes_present():
    assert len(app.RELEASE_NOTES) >= 1
    assert all("version" in n for n in app.RELEASE_NOTES)
