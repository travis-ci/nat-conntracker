import logging
import os
import sys

from io import BytesIO, StringIO

from nat_conntracker.conntracker import Conntracker
from nat_conntracker.__main__ import build_argument_parser, run_conntracker


ISPY2 = sys.version_info.major == 2
HERE = os.path.abspath(os.path.dirname(__file__))


def test_build_argument_parser():
    env = {'CONN_THRESHOLD': '99'}
    parser = build_argument_parser(env)
    assert parser is not None

    args = parser.parse_args([
        '--top-n=4',
        '-S', '499',
        '--log-file', 'wat.log',
        '-I24',
        '--include-privnets'
    ])

    assert args.top_n == 4
    assert args.conn_threshold == 99
    assert args.max_stats_size == 499
    assert args.log_file == 'wat.log'
    assert args.eval_interval == 24
    assert args.include_privnets is True


class FakeArgs(object):
    def __init__(self):
        self.events = None
        self.conn_threshold = 100
        self.top_n = 10
        self.eval_interval = 1


def test_run_events_sample(capsys):
    tmpio = BytesIO() if ISPY2 else StringIO()

    logger = logging.getLogger(__name__)
    logger.level = logging.DEBUG
    logger.propagate = 0
    stream_handler = logging.StreamHandler(stream=tmpio)
    stream_handler.setFormatter(
        logging.Formatter(
            fmt='time=%(asctime)s level=%(levelname)s %(message)s'
        )
    )
    logger.addHandler(stream_handler)

    args = FakeArgs()
    args.events = open(
        os.path.join(HERE, 'data', 'conntrack-events-sample.xml'), 'r'
    )
    ctr = Conntracker(logger, src_ign=(), dst_ign=())
    run_conntracker(ctr, logger, args)

    stream_handler.flush()
    tmpio.flush()
    tmpio.seek(0)
    captured = tmpio.read()

    assert 'WARNING over threshold=100 src=10.10.0.7' in captured
    assert 'DEBUG adding' in captured
    assert 'INFO begin sample' in captured
    assert 'INFO end sample' in captured
    assert 'INFO cleaning up' in captured
