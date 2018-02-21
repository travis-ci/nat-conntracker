from netaddr import IPNetwork, IPAddress

from .stats import Stats
from .flow_parser import FlowParser


__all__ = ['Conntracker']


class Conntracker(object):
    PRIVATE_NETS = (
        IPNetwork('10.0.0.0/8'),
        IPNetwork('127.0.0.0/8'),
        IPNetwork('169.254.0.0/16'),
        IPNetwork('172.16.0.0/12'),
        IPNetwork('192.168.0.0/16'),
    )

    def __init__(self, logger, max_size=1000, src_ign=None, dst_ign=None):
        self._logger = logger
        self.src_ign = src_ign if src_ign is not None else self.PRIVATE_NETS
        self.dst_ign = dst_ign if dst_ign is not None else self.PRIVATE_NETS
        self.stats = Stats(max_size=max_size)

    def handle(self, stream):
        FlowParser(self, self._logger).handle_events(stream)

    def sample(self, threshold, top_n):
        self._logger.info(
            'begin sample threshold={} top_n={}'.format(threshold, top_n)
        )

        for ((src, dst), count) in self.stats.top(n=top_n):
            if count >= threshold:
                self._logger.warn(
                    'over threshold={} src={} dst={} count={}'.format(
                        threshold, src, dst, count
                    )
                )

        self.stats.reset()
        self._logger.info(
            'end sample threshold={} top_n={}'.format(threshold, top_n)
        )

    def handle_flow(self, flow):
        if flow is None:
            return

        if flow.flowtype != 'new':
            self._logger.debug('skipping flowtype={}'.format(flow.flowtype))
            # Only "new" flows are currently handled, meaning that any flows
            # of type "update" or "destroy" are ignored along with any of the
            # state changes they may describe.
            return

        (src, dst) = flow.src_dst()
        if src is None or dst is None:
            self._logger.debug('skipping flow without src dst')
            return

        src_addr = IPAddress(src.host)
        dst_addr = IPAddress(dst.host)

        for ign in self.dst_ign:
            if dst_addr in ign:
                self._logger.debug(
                    'ignoring dst match src={} dst={}'.format(
                        src_addr, dst_addr
                    )
                )
                return

        for ign in self.src_ign:
            if src_addr in ign:
                self._logger.debug(
                    'ignoring src match src={} dst={}'.format(
                        src_addr, dst_addr
                    )
                )
                return

        try:
            self._logger.debug(
                'adding src={} dst={}'.format(src_addr, dst_addr)
            )
            self.stats.add(src, dst)
        except Exception as exc:
            self._logger.error(exc)
