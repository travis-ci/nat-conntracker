import signal
import time

from threading import Thread


__all__ = ['Runner']


class Runner(object):

    def __init__(self, conntracker, syncer, logger, **args):
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
                    self._args['conn_threshold'], self._args['top_n'],
                    self._args['eval_interval']
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
                self._args['conn_threshold'], self._args['top_n']
            )
            self._join()

    def _run_sample_loop(self):
        while True:
            self._conntracker.sample(
                self._args['conn_threshold'], self._args['top_n']
            )
            nextloop = time.time() + self._args['eval_interval']
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
            self._conntracker.handle(self._args['events'], is_done=self._is_done)
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
