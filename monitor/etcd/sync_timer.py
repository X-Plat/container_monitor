'''\
Class SyncTimer:
    - Periodically create test dir for ETCD task to sync with server.

Attributes:
    - self.__test_dir: the test directory;
    - self.__period: the period for sync with etcd;
'''

import threading
import time
import os

class SyncTimer(object):
    "heartbeat between client and server"

    def __init__(self, logger, test_dir='cm-test', period=30):
        self.__test_dir = test_dir
        self.__period = period
        self.logger = logger
        self.worker = self.create()

    def create_test_dir(self):
        "create test dir"
        if not self.__test_dir:
            return False
        try:
            if not os.path.exists(self.__test_dir):
                os.makedirs(self.__test_dir)
            time.sleep(1)
            os.rmdir(self.__test_dir)
        except IOError, err:
            self.logger.warn("Create test dir failed with {}".format(err))
        except Exception, err:
            self.logger.warn("Create test dir failed with {}".format(err))

    def create(self):
        "create looping call to send ping request"
        thr = threading.Thread(target=self.periodic_ping_timer)
        thr.setDaemon(True)
        return thr

    def periodic_ping_timer(self):
        'periodically send ping request to nats server'
        while True:
            self.create_test_dir()
            time.sleep(self.__period)

    def start(self):
        'start ping timer'
        self.worker.start()

    def cancel(self):
        'cancel heartbeat'
        self.worker.join(1)
