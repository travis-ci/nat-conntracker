import os
import socket
import sys

import pytest
import redis

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture(autouse=True)
def no_socket_gethostbyaddr(monkeypatch):
    monkeypatch.setattr(socket, 'gethostbyaddr', lambda a: 'somehost')


@pytest.fixture(autouse=True)
def no_redis_from_url(monkeypatch):
    monkeypatch.setattr(redis, 'from_url', lambda u: FakeRedisConn(u))


class FakeRedisConn(object):

    def __init__(self, url):
        self.url = url
        self._sets = {}

    def publish(self, *args):
        pass

    def pubsub(self, **kwargs):
        pass

    def ping(self):
        return 'PONG'

    def smembers(self, key):
        return self._sets.get(key, [])

    def sadd(self, key, value):
        if not key in self._sets:
            self._sets[key] = set()
        self._sets[key].add(value)
        return len(self._sets[key])
