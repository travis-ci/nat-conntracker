#!/usr/bin/env python
import argparse
import logging
import os
import signal
import sys
import time

from threading import Thread

from netaddr import IPNetwork

from .conntracker import Conntracker
from .null_syncer import NullSyncer


__all__ = ['main']


def main(sysargs=sys.argv[:]):
    parser = build_argument_parser(os.environ)
    args = parser.parse_args(sysargs[1:])

    logging_level = logging.INFO
    if args.debug:
        logging_level = logging.DEBUG

    logging_args = dict(
        level=logging_level,
        format='time=%(asctime)s level=%(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z'
    )

    if args.log_file:
        logging_args['filename'] = args.log_file

    logging.basicConfig(**logging_args)
    logger = logging.getLogger(__name__)

    syncer = NullSyncer()
    if args.redis_url != '':
        from .redis_syncer import RedisSyncer
        syncer = RedisSyncer(
            logger, args.sync_channel, conn_url=args.redis_url
        )

    src_ign = None
    dst_ign = None
    if args.include_privnets:
        src_ign = ()
        dst_ign = ()

    for src_item in args.src_ignore_cidrs:
        if src_item == 'private':
            src_ign = (src_ign or ()) + Conntracker.PRIVATE_NETS
            continue
        src_ign = (src_ign or ()) + (IPNetwork(src_item),)

    for dst_item in args.dst_ignore_cidrs:
        if dst_item == 'private':
            dst_ign = (dst_ign or ()) + Conntracker.PRIVATE_NETS
            continue
        dst_ign = (dst_ign or ()) + (IPNetwork(dst_item),)

    syncer.ping()
    conntracker = Conntracker(
        logger, syncer,
        max_size=args.max_stats_size, src_ign=src_ign, dst_ign=dst_ign
    )

    RunState(conntracker, syncer, logger, args).run()
    return 0


def build_argument_parser(env):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'events', nargs='?', type=argparse.FileType('r'),
        default=sys.stdin,
        help='input event XML stream or filename'
    )
    parser.add_argument(
        '-T', '--conn-threshold',
        type=int, default=int(
            env.get(
                'NAT_CONNTRACKER_CONN_THRESHOLD',
                env.get('CONN_THRESHOLD', 100)
            )
        ),
        help='connection count threshold for message logging'
    )
    parser.add_argument(
        '-n', '--top-n',
        default=int(
            env.get(
                'NAT_CONNTRACKER_TOP_N',
                env.get('TOP_N', 10)
            )
        ),
        type=int, help='periodically sample the top n counted connections'
    )
    parser.add_argument(
        '-S', '--max-stats-size',
        type=int, default=int(
            env.get(
                'NAT_CONNTRACKER_MAX_STATS_SIZE',
                env.get('MAX_STATS_SIZE', 1000)
            )
        ),
        help='max number of src=>dst:dport counters to track'
    )
    parser.add_argument(
        '-l', '--log-file',
        default=env.get(
            'NAT_CONNTRACKER_LOG_FILE',
            env.get('LOG_FILE', '')
        ),
        help='optional separate file for logging'
    )
    parser.add_argument(
        '-R', '--redis-url',
        default=env.get(
            'NAT_CONNTRACKER_REDIS_URL',
            env.get('REDIS_URL', '')
        ),
        help='redis URL for syncing conntracker'
    )
    parser.add_argument(
        '-C', '--sync-channel',
        default=env.get(
            'NAT_CONNTRACKER_SYNC_CHANNEL',
            env.get('SYNC_CHANNEL', 'nat-conntracker:sync')
        ),
        help='redis channel name to use for syncing'
    )
    parser.add_argument(
        '-I', '--eval-interval',
        type=int, default=int(
            env.get(
                'NAT_CONNTRACKER_EVAL_INTERVAL',
                env.get('EVAL_INTERVAL', 60)
            )
        ),
        help='interval at which stats will be evaluated'
    )
    parser.add_argument(
        '-s', '--src-ignore-cidrs',
        action='append', default=list(
            filter(lambda s: s.strip() != '', [
                s.strip() for s in env.get(
                    'NAT_CONNTRACKER_SRC_IGNORE_CIDRS',
                    env.get('SRC_IGNORE_CIDRS', '127.0.0.1/32')
                ).split(',')
            ])
        ),
        help='CIDR notation of source addrs/nets to ignore'
    )
    parser.add_argument(
        '-d', '--dst-ignore-cidrs',
        action='append', default=list(
            filter(lambda s: s.strip() != '', [
                s.strip() for s in env.get(
                    'NAT_CONNTRACKER_DST_IGNORE_CIDRS',
                    env.get('DST_IGNORE_CIDRS', '127.0.0.1/32')
                ).split(',')
            ])
        ),
        help='CIDR notation of destination addrs/nets to ignore'
    )
    parser.add_argument(
        '-P', '--include-privnets',
        action='store_true', default=_asbool(
            env.get(
                'NAT_CONNTRACKER_INCLUDE_PRIVNETS',
                env.get('INCLUDE_PRIVNETS', False)
            )
        ),
        help='include private networks when handling flows'
    )
    parser.add_argument(
        '-D', '--debug',
        action='store_true', default=_asbool(
            env.get(
                'NAT_CONNTRACKER_DEBUG',
                env.get('DEBUG', False)
            )
        ),
        help='enable debug logging'
    )

    return parser


def _asbool(value):
    return str(value).lower().strip() in ('1', 'yes', 'on', 'true')


class RunState(object):

    def __init__(self, conntracker, syncer, logger, args):
        self._conntracker = conntracker
        self._syncer = syncer
        self._logger = logger
        self._args = args
        self._done = False
        self._handle_thread = None
        self._sub_thread = None

    def run(self):
        self._start_threads()

        try:
            signal.signal(signal.SIGUSR1, self._conntracker.dump_state)
            self._logger.info(
                'entering sample loop '
                'threshold={} top_n={} eval_interval={}'.format(
                    self._args.conn_threshold, self._args.top_n,
                    self._args.eval_interval
                )
            )
            self._run_sample_loop()
        except KeyboardInterrupt:
            self._logger.warn('interrupt')
        finally:
            signal.signal(signal.SIGUSR1, signal.SIG_IGN)
            self._logger.info('cleaning up')
            self._done = True
            self._conntracker.sample(
                self._args.conn_threshold, self._args.top_n
            )
            self._join()

    def _run_sample_loop(self):
        while True:
            self._conntracker.sample(
                self._args.conn_threshold, self._args.top_n
            )
            nextloop = time.time() + self._args.eval_interval
            while time.time() < nextloop:
                self._join()
                if not self._is_alive():
                    self._done = True
                    return
                if self._is_done():
                    return
                time.sleep(0.1)

    def _start_threads(self):
        self._handle_thread = Thread(target=self._handle)
        self._handle_thread.start()

        self._sub_thread = Thread(target=self._sub)
        self._sub_thread.daemon = True
        self._sub_thread.start()

    def _join(self):
        self._handle_thread.join(0.1)

    def _is_alive(self):
        return self._handle_thread.is_alive()

    def _is_done(self):
        return self._done

    def _handle(self):
        try:
            self._conntracker.handle(self._args.events, is_done=self._is_done)
        except Exception:
            self._logger.exception('breaking out of handle wrap')
        finally:
            self._done = True

    def _sub(self):
        try:
            self._syncer.sub(is_done=self._is_done)
        except Exception:
            self._logger.exception('breaking out of sub wrap')
            self._done = True


if __name__ == '__main__':
    sys.exit(main())
