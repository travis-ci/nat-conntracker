import operator


import redis
from cachetools import TTLCache, cachedmethod
from netaddr import IPNetwork


__all__ = ['RedisSettings']


class RedisSettings(object):

    def __init__(self, namespace='nat-conntracker',
                 conn_url='redis://localhost:6379/0', local_ttl=5):
        self._namespace = namespace
        self._conn = redis.from_url(conn_url)
        self._cache = TTLCache(len(dir(self)), local_ttl)

    def ping(self):
        return self._conn.ping()

    @cachedmethod(operator.attrgetter('_cache'))
    def src_ignore(self):
        return self._get_networks('src-ignore')

    @cachedmethod(operator.attrgetter('_cache'))
    def dst_ignore(self):
        return self._get_networks('dst-ignore')

    def add_ignore_src(self, src):
        return self._add_ignore('src-ignore', src)

    def add_ignore_dst(self, dst):
        return self._add_ignore('dst-ignore', dst)

    def _get_networks(self, key):
        return [
            IPNetwork(s.decode('utf-8')) for s in
            filter(
                lambda s: s.strip() != b'',
                self._conn.smembers('{}:{}'.format(self._namespace, key))
            )
        ]

    def _add_ignore(self, key, value):
        self._conn.sadd('{}:{}'.format(self._namespace, key), str(value))
