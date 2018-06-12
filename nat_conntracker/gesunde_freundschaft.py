import redis

__all__ = ['GesundeFreundschaft']


class GesundeFreundschaft:
    def __init__(self,
                 conn_url='redis://localhost:6379/0',
                 redis_namespace='gesund-0'):
        self._conn = redis.from_url(conn_url)
        self._ns = redis_namespace
        self._marked = set()

    def ping(self):
        self._conn.ping()

    def cleanup(self):
        for key in self._marked:
            self._conn.srem(f'{self._ns}:health-checks', key)

    def healthy(self, key, ttl=60):
        self._marked.add(key)
        self._conn.sadd(f'{self._ns}:health-checks', key)
        self._conn.setex(f'{self._ns}:health-check:{key}', 'y', ttl)

    def unhealthy(self, key):
        self._conn.delete(f'{self._ns}:health-check:{key}')
