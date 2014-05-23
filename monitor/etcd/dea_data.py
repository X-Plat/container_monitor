# -*- coding: iso-8859-1 -*-
'''\
dea data
'''
import copy
from monitor.etcd.container_data import ContainerData
from monitor.common.common import ensure_read_yaml

class DeaData(object):
    """
    Read and format the snapshot data on DEA;
    """
    _index_kwd = [
        'instance_id',
        'warden_container_path'
    ]

    def __init__(self, snapshot_path, cluster='dev'):
        self._snapshot = ensure_read_yaml(snapshot_path)       
        self._cluster = cluster

    @property
    def instances(self):
        'the instances of a dea node'
        return self._snapshot.get('instances', [])
       
    def index_by_kwd(self, kwd):
        """
        Index the snapshot data by given keyword, the keyword should 
        only be listed in `_index_kwd`;
        """
        data = {}
   
        if kwd not in self._index_kwd: 
            return data

        data = {ins[kwd].split('/')[-1]: ContainerData(ins, self._cluster).metadata().copy() 
                     for ins in self.instances if kwd in ins}
        return data 
          
