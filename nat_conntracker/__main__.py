#!/usr/bin/env python
import argparse
import logging
import os
import sys
import time

from threading import Thread

from netaddr import IPNetwork

from .conntracker import Conntracker


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

    src_ign = None
    dst_ign = None
    if args.include_privnets:
        src_ign = ()
        dst_ign = ()

    for src_item in args.src_ignore_cidrs:
        if src_item == 'private':
            src_ign = src_ign + Conntracker.PRIVATE_NETS
            continue
        src_ign = src_ign + (IPNetwork(src_item),)

    for dst_item in args.dst_ignore_cidrs:
        if dst_item == 'private':
            dst_ign = dst_ign + Conntracker.PRIVATE_NETS
            continue
        dst_ign = dst_ign + (IPNetwork(dst_item),)

    ctr = Conntracker(
        logger, max_size=args.max_stats_size, src_ign=src_ign, dst_ign=dst_ign
    )
    run_conntracker(ctr, logger, args)
    return 0


def run_conntracker(ctr, logger, args):
    handle_thread = Thread(
        target=ctr.handle,
        args=(args.events,)
    )
    handle_thread.start()

    try:
        logger.info(
            'entering sample loop '
            'threshold={} top_n={} eval_interval={}'.format(
                args.conn_threshold, args.top_n, args.eval_interval
            )
        )
        while True:
            ctr.sample(args.conn_threshold, args.top_n)
            handle_thread.join(0.1)
            if not handle_thread.is_alive():
                break
            time.sleep(args.eval_interval)
    except KeyboardInterrupt:
        logger.warn('interrupt')
    finally:
        logger.info('cleaning up')
        ctr.sample(args.conn_threshold, args.top_n)
        handle_thread.join()


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


if __name__ == '__main__':
    sys.exit(main())
