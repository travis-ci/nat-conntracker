import socket

from ipaddress import ip_address
from threading import Thread

from .flow_parser import FlowParser

__all__ = ['Conntracker']


class Conntracker(object):
    def __init__(self, logger, syncer, settings, healther, stats):
        self._logger = logger
        self._syncer = syncer
        self._settings = settings
        self._healther = healther
        self._stats = stats

    def handle(self, stream, is_done=None):
        FlowParser(self, self._logger).handle_events(stream, is_done=is_done)

    def cleanup(self):
        self._healther.cleanup()

    def sample(self, threshold, top_n):
        self._logger.info(f'begin sample threshold={threshold} top_n={top_n}')

        flow_count = 0
        for ((src, dst), count) in self._stats.top(n=top_n):
            flow_count += count
            if count >= threshold:
                self._logger.warn(f'over threshold={threshold} src={src} '
                                  f'dst={dst} count={count} '
                                  f'hostname={self._lookup_hostname(src)}')
                self._syncer.pub(threshold, src, dst, count)

        if flow_count >= self._settings.min_flow():
            self._healther.healthy('flow-count', ttl=300)
        else:
            self._healther.unhealthy('flow-count')

        self._stats.reset()
        self._logger.info(f'end sample threshold={threshold} top_n={top_n}')

    def handle_flow(self, flow):
        if flow is None:
            return

        if flow.flowtype != 'new':
            self._logger.debug(f'skipping flowtype={flow.flowtype}')
            # Only "new" flows are currently handled, meaning that any flows
            # of type "update" or "destroy" are ignored along with any of the
            # state changes they may describe.
            return

        (src, dst) = flow.src_dst()
        if src is None or dst is None:
            self._logger.debug('skipping flow without src dst')
            return

        src_addr = ip_address(src.host)
        dst_addr = ip_address(dst.host)

        for ign in self._settings.dst_ignore():
            if dst_addr in ign:
                self._logger.debug(
                    f'ignoring dst match src={src_addr} dst={dst_addr}')
                return

        for ign in self._settings.src_ignore():
            if src_addr in ign:
                self._logger.debug(
                    f'ignoring src match src={src_addr} dst={dst_addr}')
                return

        try:
            self._logger.debug(f'adding src={src_addr} dst={dst_addr}')
            self._stats.add(src, dst)
        except Exception as exc:
            self._logger.error(exc)

    def dump_state(self, *_):
        src_ign = self._settings.src_ignore()
        for i, ign in enumerate(sorted(src_ign)):
            self._logger.info(f'src_ign dump {i + 1}/{len(src_ign)} net={ign}')

        dst_ign = self._settings.dst_ignore()
        for i, ign in enumerate(sorted(dst_ign)):
            self._logger.info(f'dst_ign dump {i + 1}/{len(dst_ign)} net={ign}')

        self._logger.info(f'stats max_size={self._stats.max_size}')
        for i, ((src, dst), count) in enumerate(self._stats.top(10)):
            self._logger.info(
                f'stats dump {i + 1}/10 src={src} dst={dst} count={count}')

    def _lookup_hostname(self, ipv4, timeout=0.1):
        ret = {'hostname': 'notset'}
        fetch = Thread(target=self._build_hostname_fetch(ret, ipv4))
        fetch.start()
        fetch.join(timeout)
        return ret['hostname']

    def _build_hostname_fetch(self, ret, ipv4):
        def fetch():
            try:
                ret['hostname'] = socket.gethostbyaddr(ipv4)[0]
            except socket.herror:
                ret['hostname'] = 'unknown'
                self._logger.exception('failed to get hostname')

        return fetch
