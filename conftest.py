import os
import socket
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture(autouse=True)
def no_socket_gethostbyaddr(monkeypatch):
    monkeypatch.setattr(socket, 'gethostbyaddr', lambda a: 'somehost')
