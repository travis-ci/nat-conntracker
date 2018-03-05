import logging
import os
import sys

from nat_conntracker.__main__ import build_argument_parser, build_runner


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


def test_run_events_sample(caplog):
    events = open(
        os.path.join(HERE, 'data', 'conntrack-events-sample.xml'), 'r'
    )
    runner = build_runner(events=events, conn_threshold=100, debug=True)
    with caplog.at_level(logging.DEBUG):
        runner.run()

    assert ' over threshold=100 src=10.10.0.7' in caplog.text
    assert ' adding' in caplog.text
    assert ' begin sample' in caplog.text
    assert ' end sample' in caplog.text
    assert ' cleaning up' in caplog.text
