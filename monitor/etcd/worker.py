# -*- coding: iso-8859-1 -*-
'''\
Class Monitor4ETCD:
    - register container information to remote server;

Attributes:
    - _logger: logging
    - _config: configure parameters;
    - _task: task object;
'''
import json
from pyinotify import ProcessEvent
from monitor.etcd.etcd_task import EtcdTask
from monitor.etcd.collector_task import CollectorTask

class Monitor4ETCD(ProcessEvent):
    'register worker for register container information'

    def __init__(self, logger, config):
        self._logger = logger
        self._config = config
        self._collector_enabled = config['collector_enabled']
        self._task = EtcdTask(self._logger, self._config)
        self._collector_task = CollectorTask(self._logger, self._config)

    def dir_to_process(self, event):
        event_info = {}
        try:
            info = event.__str__().rstrip().replace(': ', '": "').replace('   ', '","')
            info_str = '{"' + info + '"}'
            event_info = json.loads(info_str)
        except Exception, e:
            self._logger.warn('parse event info failed {}'.format(e))

        if 'name' in event_info and 'is_dir' in event_info and event_info['is_dir'] == 'True':
            self._logger.debug('get event of container {}.'.format(event_info['name']))
            return event_info['name']
        else:
            self._logger.debug('ignore useless event.')
            return None

    def process_default(self, event):
        """
        override default processing method
        """
        self._logger.debug('Monitor4ETCD::process_DEFAULT')
        # call base method
        super(Monitor4ETCD, self).process_default(event)

    def process_IN_DELETE(self, event):
        """
        process 'IN_DELETE' events
        """
        self._logger.debug('Monitor4ETCD::process_IN_DELETE')
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
        self._logger.debug('Monitor4ETCD::process_IN_MOVED_TO')
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
        self._logger.debug('Monitor4ETCD::process_IN_CREATE')
        super(Monitor4ETCD, self).process_default(event)
        container = self.dir_to_process(event)
        if not container:
            return
        self._task.start(container, 'create')
        if self._collector_enabled:
            self._collector_task.start(container, 'create')

