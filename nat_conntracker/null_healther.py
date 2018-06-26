__all__ = ['NullHealther']


class NullHealther:
    def ping(self):
        pass

    def cleanup(self):
        pass

    def healthy(self, key, ttl=60):
        pass

    def unhealthy(self, key):
        pass
