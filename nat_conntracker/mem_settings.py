from netaddr import IPNetwork


__all__ = ['MemSettings']


class MemSettings(object):

    def __init__(self):
        self._settings = {
            'src_ignore': set(),
            'dst_ignore': set()
        }

    def ping(self):
        pass

    def src_ignore(self):
        return list(self._settings['src_ignore'])

    def dst_ignore(self):
        return list(self._settings['dst_ignore'])

    def add_ignore_src(self, src):
        self._settings['src_ignore'].add(IPNetwork(str(src)))

    def add_ignore_dst(self, dst):
        self._settings['dst_ignore'].add(IPNetwork(str(dst)))
