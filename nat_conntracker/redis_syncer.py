import json
import time

import redis


__all__ = ['RedisSyncer']


class RedisSyncer(object):

    def __init__(self, logger, channel, conn_url='redis://localhost:6379/0'):
        self._logger = logger
        self._channel = channel
        self._conn = redis.from_url(conn_url)

    def pub(self, threshold, src, dst, count):
        return self._conn.publish(
            self._channel,
            json.dumps({
                'threshold': threshold,
                'src': src,
                'dst': dst,
                'count': count
            })
        )

    def sub(self, interval=0.01, is_done=None):
        is_done = is_done if is_done is not None else lambda: False
        psconn = self._conn.pubsub(ignore_subscribe_messages=True)
        psconn.subscribe(**{self._channel: self._handle_message})
        while True:
            psconn.get_message()
            if is_done():
                break
            time.sleep(interval)

    def _handle_message(self, message):
        if message['type'] != 'message':
            return

        try:
            msg = json.loads(message['data'].decode('utf-8'))
            self._logger.warn(
                ('over threshold={threshold} src={src} dst={dst} '
                 'count={count} source=sync').format(**msg)
            )
        except Exception:
            self._logger.exception('failed to handle message')

    def ping(self):
        self._conn.ping()
