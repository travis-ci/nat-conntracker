#!/usr/bin/env python
import argparse
import logging
import os
import sys
import time

from threading import Thread

from .conntracker import Conntracker, PRIVATE_NETS
from .logger import get_logger


def main(sysargs=sys.argv[:]):
    parser = build_argument_parser(os.environ)
    args = parser.parse_args(sysargs[1:])

    logging_args = dict(
        level=logging.INFO,
        format='time=%(asctime)s level=%(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z'
    )

    if args.log_file:
        logging_args['filename'] = args.log_file

    logging.basicConfig(**logging_args)
    logger = get_logger()

    ignore = PRIVATE_NETS
    if args.include_privnets:
        ignore = ()

    ctr = Conntracker(logger, max_size=args.max_stats_size, ignore=ignore)
    run_conntracker(ctr, logger, args)
    return 0


def run_conntracker(ctr, logger, args):
    handle_thread = Thread(
        target=ctr.handle,
        args=(args.events,)
    )
    handle_thread.start()

    try:
        while True:
            ctr.sample(args.conn_threshold, args.top_n)
            handle_thread.join(0.1)
            if not handle_thread.is_alive():
                break
            time.sleep(args.eval_interval)
    except KeyboardInterrupt:
        logger.warn('interrupt')
    finally:
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
        '-P', '--include-privnets',
        action='store_true', default=asbool(
            env.get(
                'NAT_CONNTRACKER_INCLUDE_PRIVNETS',
                env.get('INCLUDE_PRIVNETS', False)
            )
        ),
        help='include private networks when handling flows'
    )

    return parser


def asbool(value):
    return str(value).lower().strip() in ('1', 'yes', 'on', 'true')


if __name__ == '__main__':
    sys.exit(main())
