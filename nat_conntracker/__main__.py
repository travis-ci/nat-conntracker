#!/usr/bin/env python
import argparse
import logging
import os
import sys

from netaddr import IPNetwork

from .conntracker import Conntracker
from .null_syncer import NullSyncer
from .runner import Runner

try:
    from .__version__ import VERSION
except ImportError:
    VERSION = 'unknown'


__all__ = ['main']


ARG_DEFAULTS = (
    ('conn_threshold', 100),
    ('debug', False),
    ('dst_ignore_cidrs', ('127.0.0.1/32',)),
    ('eval_interval', 60),
    ('events', sys.stdin),
    ('include_privnets', False),
    ('log_file', ''),
    ('max_stats_size', 1000),
    ('redis_url', ''),
    ('src_ignore_cidrs', ('127.0.0.1/32',)),
    ('sync_channel', 'nat-conntracker:sync'),
    ('top_n', 10),
)


def main(sysargs=sys.argv[:]):
    parser = build_argument_parser(os.environ)
    args = parser.parse_args(sysargs[1:])

    runner = build_runner(**args.__dict__)
    runner.run()
    return 0


def build_runner(**kwargs):
    args = dict(ARG_DEFAULTS)
    args.update(kwargs)

    logging_level = logging.INFO
    if args['debug']:
        logging_level = logging.DEBUG

    log_format = 'time=%(asctime)s level=%(levelname)s %(message)s'
    if VERSION != 'unknown':
        log_format = 'v={} {}'.format(VERSION, log_format)

    logging_args = dict(
        level=logging_level,
        format=log_format,
        datefmt='%Y-%m-%dT%H:%M:%S%z'
    )

    if args['log_file']:
        logging_args['filename'] = args['log_file']

    logging.basicConfig(**logging_args)
    logger = logging.getLogger(__name__)

    syncer = NullSyncer()
    if args.get('redis_url', ''):
        from .redis_syncer import RedisSyncer
        syncer = RedisSyncer(
            logger, args['sync_channel'], conn_url=args['redis_url']
        )

    src_ign = None
    dst_ign = None
    if args['include_privnets']:
        src_ign = ()
        dst_ign = ()

    for src_item in args['src_ignore_cidrs']:
        if src_item == 'private':
            src_ign = (src_ign or ()) + Conntracker.PRIVATE_NETS
            continue
        src_ign = (src_ign or ()) + (IPNetwork(src_item),)

    for dst_item in args['dst_ignore_cidrs']:
        if dst_item == 'private':
            dst_ign = (dst_ign or ()) + Conntracker.PRIVATE_NETS
            continue
        dst_ign = (dst_ign or ()) + (IPNetwork(dst_item),)

    syncer.ping()
    conntracker = Conntracker(
        logger, syncer,
        max_size=args['max_stats_size'], src_ign=src_ign, dst_ign=dst_ign
    )

    return Runner(conntracker, syncer, logger, **dict(args))


def build_argument_parser(env, defaults=None):
    defaults = defaults if defaults is not None else dict(ARG_DEFAULTS)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(VERSION)
    )
    parser.add_argument(
        'events', nargs='?', type=argparse.FileType('r'),
        default=defaults['events'],
        help='input event XML stream or filename'
    )
    parser.add_argument(
        '-T', '--conn-threshold',
        type=int, default=int(
            env.get(
                'NAT_CONNTRACKER_CONN_THRESHOLD',
                env.get('CONN_THRESHOLD', defaults['conn_threshold'])
            )
        ),
        help='connection count threshold for message logging'
    )
    parser.add_argument(
        '-n', '--top-n',
        default=int(
            env.get(
                'NAT_CONNTRACKER_TOP_N',
                env.get('TOP_N', defaults['top_n'])
            )
        ),
        type=int, help='periodically sample the top n counted connections'
    )
    parser.add_argument(
        '-S', '--max-stats-size',
        type=int, default=int(
            env.get(
                'NAT_CONNTRACKER_MAX_STATS_SIZE',
                env.get('MAX_STATS_SIZE', defaults['max_stats_size'])
            )
        ),
        help='max number of src=>dst:dport counters to track'
    )
    parser.add_argument(
        '-l', '--log-file',
        default=env.get(
            'NAT_CONNTRACKER_LOG_FILE',
            env.get('LOG_FILE', defaults['log_file'])
        ),
        help='optional separate file for logging'
    )
    parser.add_argument(
        '-R', '--redis-url',
        default=env.get(
            'NAT_CONNTRACKER_REDIS_URL',
            env.get('REDIS_URL', defaults['redis_url'])
        ),
        help='redis URL for syncing conntracker'
    )
    parser.add_argument(
        '-C', '--sync-channel',
        default=env.get(
            'NAT_CONNTRACKER_SYNC_CHANNEL',
            env.get('SYNC_CHANNEL', defaults['sync_channel'])
        ),
        help='redis channel name to use for syncing'
    )
    parser.add_argument(
        '-I', '--eval-interval',
        type=int, default=int(
            env.get(
                'NAT_CONNTRACKER_EVAL_INTERVAL',
                env.get('EVAL_INTERVAL', defaults['eval_interval'])
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
                    env.get(
                        'SRC_IGNORE_CIDRS', defaults['src_ignore_cidrs'][0]
                    )
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
                    env.get(
                        'DST_IGNORE_CIDRS', defaults['dst_ignore_cidrs'][0]
                    )
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
                env.get('INCLUDE_PRIVNETS', defaults['include_privnets'])
            )
        ),
        help='include private networks when handling flows'
    )
    parser.add_argument(
        '-D', '--debug',
        action='store_true', default=_asbool(
            env.get(
                'NAT_CONNTRACKER_DEBUG',
                env.get('DEBUG', defaults['debug'])
            )
        ),
        help='enable debug logging'
    )

    return parser


def _asbool(value):
    return str(value).lower().strip() in ('1', 'yes', 'on', 'true')


if __name__ == '__main__':
    sys.exit(main())
