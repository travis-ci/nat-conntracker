from ipaddress import ip_network

__all__ = ['MemSettings']


class MemSettings(object):
    def __init__(self):
        self._settings = {
            'src_ignore': set(),
            'dst_ignore': set(),
            'min_flow': 10
        }

    def ping(self):
        pass

    def src_ignore(self):
        return list(self._settings['src_ignore'])

    def dst_ignore(self):
        return list(self._settings['dst_ignore'])

    def add_ignore_src(self, src):
        self._settings['src_ignore'].add(ip_network(str(src)))

    def add_ignore_dst(self, dst):
        self._settings['dst_ignore'].add(ip_network(str(dst)))

    def min_flow(self):
        return self._settings['min_flow']
