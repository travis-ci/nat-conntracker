from ipaddress import ip_network

import redis
from cachetools.func import ttl_cache

__all__ = ['RedisSettings']


class RedisSettings(object):
    def __init__(self,
                 namespace='nat-conntracker',
                 conn_url='redis://localhost:6379/0'):
        self._namespace = namespace
        self._conn = redis.from_url(conn_url)

    def ping(self):
        return self._conn.ping()

    @ttl_cache(ttl=30)
    def src_ignore(self):
        return self._get_networks('src-ignore')

    @ttl_cache(ttl=30)
    def dst_ignore(self):
        return self._get_networks('dst-ignore')

    def add_ignore_src(self, src):
        return self._add_ignore('src-ignore', src)

    def add_ignore_dst(self, dst):
        return self._add_ignore('dst-ignore', dst)

    @ttl_cache(ttl=30)
    def min_flow(self, default=10):
        return int(self._conn.get(f'{self._namespace}:min-flow') or default)

    def _get_networks(self, key):
        return [
            ip_network(s.decode('utf-8'))
            for s in filter(lambda s: s.strip() != b'',
                            self._conn.smembers(f'{self._namespace}:{key}'))
        ]

    def _add_ignore(self, key, value):
        self._conn.sadd(f'{self._namespace}:{key}', str(value))
