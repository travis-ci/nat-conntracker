from collections import Counter, OrderedDict
from threading import Lock

__all__ = ['Stats']


class Stats(object):
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.counter = Counter()
        self.index = OrderedDict()
        self._lock = Lock()

    def __repr__(self):
        return '<{} max_size={!r}>'.format(self.__class__.__name__,
                                           self.max_size)

    def top(self, n=10):
        try:
            self._lock.acquire()
            ret = []
            for key, count in self.counter.most_common(n):
                (src, dst) = self.index[key]
                ret.append(((src.host, self._daddr(dst)), count))
            return ret
        finally:
            self._lock.release()

    def reset(self):
        try:
            self._lock.acquire()
            self.counter = Counter()
            self.index = OrderedDict()
        finally:
            self._lock.release()

    def add(self, src, dst):
        try:
            self._lock.acquire()
            while len(self.index) > self.max_size:
                item_key, _ = self.index.popitem(last=False)
                del self.counter[item_key]
            key = self._key(src, dst)
            self.counter[key] += 1
            self.index[key] = (src, dst)
        finally:
            self._lock.release()

    def _key(self, src, dst):
        return '{}_{}'.format(src.host, self._daddr(dst))

    def _daddr(self, dst):
        dport = dst.port
        if dport == '':
            dport = '?'
        return '{}:{}'.format(dst.host, dport)
