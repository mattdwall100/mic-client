from __future__ import annotations

import sys
from pathlib import Path

import pytest


CLIENT_ROOT = Path(__file__).resolve().parents[1]
CLIENT_SRC = CLIENT_ROOT / "src"

if str(CLIENT_SRC) not in sys.path:
    sys.path.insert(0, str(CLIENT_SRC))


# cache clearing context manager fixture
@pytest.fixture(autouse=True)
def clear_settings_cache():
    from windows_mic_client.core.config import get_client_settings

    get_client_settings.cache_clear()
    yield
    get_client_settings.cache_clear()
