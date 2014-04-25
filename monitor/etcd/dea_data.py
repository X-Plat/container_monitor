# -*- coding: iso-8859-1 -*-
'''\
dea data
'''
from monitor.etcd.container_data import ContainerData
from monitor.common.common import ensure_read_yaml

class DeaData(object):
    """
    Read and format the snapshot data on DEA;
    """
    _index_kwd = [
        'instance_id',
        'warden_handle'
    ]

    def __init__(self, snapshot_path):
        print snapshot_path
        self._snapshot = ensure_read_yaml(snapshot_path)       

    @property
    def instances(self):
        'the instances of a dea node'
        print self._snapshot
        return self._snapshot.get('instances', [])
       
    def index_by_kwd(self, kwd):
        """
        Index the snapshot data by given keyword, the keyword should 
        only be listed in `_index_kwd`;
        """
        data = {}
   
        if kwd not in self._index_kwd: 
            return data
        data = {ins[kwd]: ContainerData(ins).metadata() 
                     for ins in self.instances if kwd in ins}

        return data 
          
