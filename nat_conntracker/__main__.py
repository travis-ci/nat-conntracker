#!/usr/bin/env python
import argparse
import logging
import sys
import time

from threading import Thread

from .conntracker import Conntracker, PRIVATE_NETS
from .logger import LOGGER


def main(sysargs=sys.argv[:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'events', nargs='?', type=argparse.FileType('r'),
        default=sys.stdin,
        help='input event XML stream or filename'
    )
    parser.add_argument(
        '-T', '--conn-threshold',
        type=int, default=500,
        help='connection count threshold for message logging'
    )
    parser.add_argument(
        '-n', '--top-n',
        type=int, help='periodically sample the top n counted connections'
    )
    parser.add_argument(
        '-S', '--max-stats-size',
        type=int, default=1000,
        help='max number of src=>dst:dport counters to track'
    )
    parser.add_argument(
        '-l', '--log-file',
        default='', help='optional separate file for logging'
    )
    parser.add_argument(
        '-I', '--eval-interval',
        type=int, default=5,
        help='interval at which stats will be evaluated'
    )
    parser.add_argument(
        '-P', '--include-privnets',
        action='store_true', default=False,
        help='include private networks when handling flows'
    )
    args = parser.parse_args(sysargs[1:])

    logging_args = dict(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

    if args.log_file:
        logging_args['filename'] = args.log_file

    logging.basicConfig(**logging_args)

    ignore = PRIVATE_NETS
    if args.include_privnets:
        ignore = ()

    ctr = Conntracker(max_size=args.max_stats_size, ignore=ignore)
    handle_thread = Thread(
        target=ctr.handle,
        args=(args.events,)
    )
    handle_thread.start()

    try:
        while True:
            ctr.log_over_threshold(args.conn_threshold, args.top_n)
            handle_thread.join(1)
            if not handle_thread.is_alive():
                break
            time.sleep(args.eval_interval)
    except KeyboardInterrupt:
        LOGGER.warn('interrupt')
    finally:
        ctr.log_over_threshold(args.conn_threshold, args.top_n)
        handle_thread.join()

    return 0


if __name__ == '__main__':
    sys.exit(main())
