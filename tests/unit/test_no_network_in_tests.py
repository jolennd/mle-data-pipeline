import socket

import pytest
import requests


def test_no_network_in_tests():
    """R22: a test that reaches an outside host fails instead of downloading."""
    with pytest.raises(OSError, match="test tried to"):
        socket.create_connection(("93.184.216.34", 80), timeout=1)
    with pytest.raises(OSError, match="test tried to"):
        requests.get("https://example.test/trip-data/file.parquet", timeout=1)
