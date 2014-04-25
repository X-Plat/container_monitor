# -*- coding: iso-8859-1 -*-
'''\
container data struct
'''
from monitor.common import local_ip

class ContainerData(object):
    "The container data"

    _container_props = {
      'application_name'   : None,
      'instance_id'        : None,
      'instance_index'     : None,
      'warden_handle'      : None,
      'warden_host_ip'     : None,
      'state'              : None,
      'tags'               : {}
    }

    _timestamp_adapter = {
      'CRASHED' : 'state_crashed_timestamp',
      'RUNNING' : 'state_running_timestamp'
    }

    def __init__(self, metadata, cluster='dev'):
        self._dataset = self._container_props
        for (key, default) in self._dataset.items():
            if key in metadata:
                self._dataset[key] = metadata[key]
            else:
                self._dataset[key] = default        

        self._cluster = cluster
        self._dataset['state_timestamp'] = metadata.get(
            self._convert_timestamp(self._dataset['state']))
        bns_node = self._dataset['tags'].get('bns_node', 
            self._dataset['application_name'])
        self._dataset['app_id'] = self._cluster + '-' + bns_node
        self._dataset['ip'] = local_ip()

    def _convert_timestamp(self, state=None):
        'convert the timestamp by state '
        if state not in self._timestamp_adapter: 
            return None
        return self._timestamp_adapter[state]
    

    def metadata(self):
        'return the metadata of a container'
        return self._dataset

    def cluster(self):
        'return the cluster tag'
        return self._cluster

    def __str__(self):
        return "%s"%self._dataset['app_id']




