"""
Streamlit AppTest smoke test.
Validates that app.py initializes cleanly without unhandled exceptions.
"""

import pytest
from streamlit.testing.v1 import AppTest

def test_app_smoke():
    at = AppTest.from_file("app.py", default_timeout=15)
    at.run()
    assert not at.exception, f"App crashed with exception: {at.exception}"
    # Verify title or header is present
    assert len(at.header) > 0
