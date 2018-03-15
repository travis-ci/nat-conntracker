import json
import logging

from nat_conntracker.redis_syncer import RedisSyncer

import pytest


@pytest.fixture
def syncer():
    return RedisSyncer(
        logging.getLogger(__name__),
        'nat-conntracker-tests:sync'
    )


def test_redis_syncer_init(syncer):
    assert syncer is not None


def test_redis_syncer_pub(syncer, monkeypatch):
    published = []

    def mock_publish(*args):
        published.append(args)

    monkeypatch.setattr(syncer._conn, 'publish', mock_publish)
    syncer.pub(99, '127.0.0.1', '169.254.169.254', 14)

    assert len(published) > 0
    assert published[0][1] is not None

    msg = json.loads(published[0][1])

    assert msg == {
        'threshold': 99,
        'src': '127.0.0.1',
        'dst': '169.254.169.254',
        'count': 14
    }


class MockPubSubConn(object):

    def __init__(self):
        self.subscriptions = None

    def subscribe(self, **kwargs):
        self.subscriptions = kwargs

    def get_message(self):
        pass


def test_redis_syncer_sub(syncer, monkeypatch):
    mpsconn = MockPubSubConn()

    def mock_pubsub(*args, **kwargs):
        return mpsconn

    monkeypatch.setattr(syncer._conn, 'pubsub', mock_pubsub)
    syncer.sub(is_done=(lambda: True))

    assert mpsconn.subscriptions is not None
    assert mpsconn.subscriptions[syncer._channel] is not None


def test_redis_syncer_ping(syncer):
    assert syncer.ping() == b'PONG'


def test_redis_syncer_handle_message(syncer):
    assert syncer._handle_message({'type': 'not-a-message'}) is None
    bogus = syncer._handle_message(
        {'type': 'message', 'data': '{"bogus":true}'}
    )
    assert bogus is None

    ok = syncer._handle_message({
        'type': 'message',
        'data': b'{"threshold":5,"src":"10.9.8.7","dst":"1.3.3.7","count":40}'
    })
    assert ok is None
