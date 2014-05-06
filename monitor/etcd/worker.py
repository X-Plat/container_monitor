# -*- coding: iso-8859-1 -*-
'''\
Class Monitor4ETCD: 
    - register container information to remote server;

Attributes:
    - _logger: logging
    - _config: configure parameters;
    - _task: task object;
'''
from pyinotify import ProcessEvent
from monitor.etcd.etcd_task import EtcdTask

class Monitor4ETCD(ProcessEvent):
    'register worker for register container information'
    
    def __init__(self, logger, config):
        self._logger = logger
        self._config = config
        self._task = EtcdTask(self._logger, self._config)

    def process_default(self, event):
        """
        override default processing method
        """
        self._logger.debug('Monitor4ETCD::process_default')
        # call base method
        super(Monitor4ETCD, self).process_default(event)

    def process_IN_DELETE(self, event):
        """
        process 'IN_DELETE' events 
        """
        self._logger.debug('Monitor4ETCD::process_IN_DELETE')
        super(Monitor4ETCD, self).process_default(event)
        self.start()

    def process_IN_CREATE(self, event):
        """
        process 'IN_CREATE' events
        """
        self._logger.debug('Monitor4ETCD::process_IN_CREATE')
        super(Monitor4ETCD, self).process_default(event)
        self.start()

    def start(self):
        self._task.start()
     
