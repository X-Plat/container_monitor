#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os,sys
import threading
from bns.worker import Monitor4BNS
from etcd.worker import Monitor4ETCD
from etcd.sync_timer import SyncTimer
from pyinotify import WatchManager, Notifier, EventsCodes

class Monitor(threading.Thread):
    def __init__(self, logger, config):
        threading.Thread.__init__(self)
        self.logger = logger
        self.config = config
        self.mask = EventsCodes.IN_MODIFY | EventsCodes.IN_DELETE | \
                    EventsCodes.IN_OPEN | EventsCodes.IN_ATTRIB | \
                    EventsCodes.IN_CREATE | EventsCodes.IN_MOVED_TO

        self.wm = WatchManager()
        self.mon_dir = []
        if config['task'] == 'register':
            self.notifier = Notifier(self.wm, Monitor4ETCD(logger, config))
            self.mon_dir.append(config['monitor_dir'])
            self.mon_dir.append(config['backup_dir'])
            test_dir = config['monitor_dir'] + '/' + 'cm-test'
            self.sync_timer = SyncTimer(self.logger, test_dir, 300)
            self.sync_timer.start()
        else:
            self.notifier = Notifier(self.wm, Monitor4BNS(logger, config))
            self.mon_dir.append(config['monitor_dir'])
        self.logger.info("Monitor starting...")

    def run(self):
        added_flag = False
        for mdir in self.mon_dir:
            if not os.path.isdir(mdir):
                self.logger.warn("Monitor dir not exist, create it.")
                os.makedirs(mdir)
            self.logger.info("Monitor works with  %s" %mdir)
        while True:
            try:
                if not added_flag:
                    for mdir in self.mon_dir:
                        self.wm.add_watch(mdir, self.mask)
                    added_flag = True
                self.notifier.process_events()
                if self.notifier.check_events():
                    self.notifier.read_events()
            except KeyboardInterrupt:
                self.logger.info('stop monitoring...')
                self.notifier.stop()
                self.sync_timer.cancel()
                break
            #except Exception, err:
                # otherwise keep on watching
                #self.logger.error("Error occured with %s" %err)
