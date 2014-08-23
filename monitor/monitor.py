#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os,sys
import threading
from bns.worker import Monitor4BNS
from etcd.worker import Monitor4ETCD
from collector.worker import Monitor4COLLECTOR
from etcd.sync_timer import SyncTimer
from pyinotify import WatchManager, Notifier, EventsCodes, Stats

class Monitor(threading.Thread):
    def __init__(self, logger, config):
        threading.Thread.__init__(self)
        self.logger = logger
        self.config = config
        self.mask = EventsCodes.IN_DELETE | \
                    EventsCodes.IN_CREATE | EventsCodes.IN_MOVED_TO

        self.wm = WatchManager()
        self.mon_dir = []
        if config['task'] == 'register':
            register_stats = Stats()
            self.notifier = Notifier(self.wm, Monitor4ETCD(
                register_stats,
                logger=logger,
                config=config))
            self.mon_dir.append(config['monitor_dir'])
            self.mon_dir.append(config['backup_dir'])
            self.sync_times = []
            test_dir = config['monitor_dir'] + '/' + 'cm-test'
            etcd_timer = SyncTimer(self.logger, test_dir, 300)
            self.sync_times.append(etcd_timer)
            if config['collector_enabled']:
                test_dir_col = config['monitor_dir'] + '/' + 'collector-test'
                collector_timer = SyncTimer(self.logger, test_dir, 20)
                self.sync_times.append(collector_timer)
            for timer in self.sync_times:
                timer.start()
        else:
            bns_stats = Stats()
            self.notifier = Notifier(self.wm,
                    Monitor4BNS(
                        bns_stats,
                        logger=logger,
                        config=config))
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
