from netaddr import IPNetwork, IPAddress

from .stats import Stats
from .flow_parser import FlowParser


PRIVATE_NETS = (
    IPNetwork('10.0.0.0/8'),
    IPNetwork('127.0.0.0/8'),
    IPNetwork('169.254.0.0/16'),
    IPNetwork('172.16.0.0/12'),
    IPNetwork('192.168.0.0/16'),
)


class Conntracker(object):
    def __init__(self, logger, max_size=1000, ignore=PRIVATE_NETS):
        self._logger = logger
        self.ignore = ignore
        self.stats = Stats(max_size=max_size)

    def handle(self, stream):
        FlowParser(self, self._logger).handle_events(stream)

    def sample(self, threshold, top_n):
        self._logger.info(
            'begin sample threshold={} top_n={}'.format(threshold, top_n)
        )

        for ((src, dst), count) in self.stats.top(n=top_n):
            if count >= threshold:
                self._logger.warn('threshold={} src={} dst={} count={}'.format(
                    threshold, src, dst, count
                ))

        self.stats.reset()
        self._logger.info(
            'end sample threshold={} top_n={}'.format(threshold, top_n)
        )

    def handle_flow(self, flow):
        if flow is None:
            return

        (src, dst) = flow.src_dst()
        if src is None or dst is None:
            return

        src_addr = IPAddress(src.host)
        dst_addr = IPAddress(dst.host)

        for ign in self.ignore:
            if src_addr in ign or dst_addr in ign:
                return

        try:
            self.stats.add(src, dst)
        except Exception as exc:
            self._logger.error(exc)
