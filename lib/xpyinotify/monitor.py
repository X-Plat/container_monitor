#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os,sys
import threading

from container_link import ContainerLink
from container_register import ContainerRegister
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
        if config['task'] == 'register':
            self.notifier = Notifier(self.wm, ContainerRegister(logger, config))
        else:
            self.notifier = Notifier(self.wm, ContainerLink(logger, config))
        self.mon_dir = config['monitor_dir']
        self.logger.info("Monitor starting...")

    def check_monitor_dir(self, dir):
        if not os.path.isdir(dir):
            self.logger.error("Config error, monitor dir not exist!")
            sys.exit(1)
        
    def run(self):

        added_flag = False
        self.check_monitor_dir(self.mon_dir)
        self.logger.info("Monitor works with  %s" %self.mon_dir)
        # read and process events
        while True:
            try:
                if not added_flag:
                    # on first iteration, add a watch on path:
                    # watch path for events handled by mask  
                    self.wm.add_watch(self.mon_dir, self.mask)
                    added_flag = True
                self.notifier.process_events()
                if self.notifier.check_events():
                    self.notifier.read_events()
            except KeyboardInterrupt:
                # ...until c^c signal
                self.logger.info('stop monitoring...')
                # stop monitoring
                self.notifier.stop()
                break
            except Exception, err:
                # otherwise keep on watching
                self.logger.error("Error occured with %s" %err)
