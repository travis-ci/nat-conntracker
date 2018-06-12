import time

__all__ = ['NullSyncer']


class NullSyncer(object):
    def __init__(self, *_, **__):
        pass

    def pub(self, *_):
        return 1

    def sub(self, **__):
        while True:
            time.sleep(10)

    def ping(self):
        pass
