# -*- coding: iso-8859-1 -*-
'''\
Class Monitor4ETCD:
    - register container information to remote server;

Attributes:
    - _logger: logging
    - _config: configure parameters;
    - _task: etcd task object;
    - _collector_task: collector task object;
'''
import json
from pyinotify import ProcessEvent
from monitor.etcd.etcd_task import EtcdTask
from monitor.etcd.collector_task import CollectorTask

class Monitor4ETCD(ProcessEvent):
    'register worker for register container information'

    def my_init(self, logger, config):
        self._logger = logger
        self._config = config
        self._collector_enabled = config['collector_enabled']
        self._task = EtcdTask(self._logger, self._config)
        self._collector_task = CollectorTask(self._logger, self._config)

    def dir_to_process(self, event):

        if event.name and event.dir:
            self._logger.debug('[Monitor4ETCD]: get event of container {}.'.format(event.name))
            return event.name
        else:
            self._logger.debug('[Monitor4ETCD]: ignore useless event.')
            return None

    def process_default(self, event):
        """
        override default processing method
        """
        self._logger.debug('[Monitor4ETCD]: process_DEFAULT')
        # call base method
        super(Monitor4ETCD, self).process_default(event)

    def process_IN_DELETE(self, event):
        """
        process 'IN_DELETE' events
        """
        self._logger.debug('[Monitor4ETCD]: process_IN_DELETE')
        super(Monitor4ETCD, self).process_default(event)
        container = self.dir_to_process(event)
        if not container:
            return
        self._task.start(container, 'delete')
        if self._collector_enabled:
            self._collector_task.start(container, 'delete')

    def process_IN_MOVED_TO(self, event):
        """
        process 'IN_MOVED_TO' events
        """
        self._logger.debug('[Monitor4ETCD]: process_IN_MOVED_TO')
        super(Monitor4ETCD, self).process_default(event)
        container = self.dir_to_process(event)
        if not container:
            return
        self._task.start(container, 'move')
        if self._collector_enabled:
            self._collector_task.start(container, 'move')

    def process_IN_CREATE(self, event):
        """
        process 'IN_CREATE' events
        """
        self._logger.debug('[Monitor4ETCD]: process_IN_CREATE')
        super(Monitor4ETCD, self).process_default(event)
        container = self.dir_to_process(event)
        if not container:
            return
        self._task.start(container, 'create')
        if self._collector_enabled:
            self._collector_task.start(container, 'create')

