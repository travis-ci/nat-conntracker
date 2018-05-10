from ipaddress import ip_network

import pytest

from nat_conntracker.redis_settings import RedisSettings


@pytest.fixture
def settings():
    return RedisSettings()


def test_redis_settings_init(settings):
    assert settings._conn is not None


def test_redis_settings_ping(settings):
    assert settings.ping() == b'PONG'


def test_redis_settings_src_ignore(settings):
    settings.add_ignore_src('123.145.0.0/16')
    assert ip_network('123.145.0.0/16') in settings.src_ignore()


def test_redis_settings_dst_ignore(settings):
    settings.add_ignore_dst('167.189.0.0/16')
    assert ip_network('167.189.0.0/16') in settings.dst_ignore()
