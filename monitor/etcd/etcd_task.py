# -*- coding: iso-8859-1 -*-
import time
import os, sys
from itertools import count
from functools import wraps
from monitor.etcd.etcd_protocol import *
from monitor.etcd.etcd_register import EtcdRegister
from monitor.etcd.dea_data import DeaData
from monitor.common.common import local_ip
import traceback 

Logger = None

def timecost(func):
    'record the time cost'
    @wraps(func)
    def wrapper(*args, **kwargs):
        'this decorator used to timing the performance of each etcd request.'
        global Logger
        start = time.time()
        ret = func(*args, **kwargs)
        spent_time = time.time() - start
        Logger.debug("%s time cost: %.3f."%(func.__name__, spent_time))
        return ret
    return wrapper

class EtcdTask(object):
    'etcd register task'

    TASK_NAME = "etcd-task"
    TASK_ID = count()

    #NOTE:  Etcd task trigered by events of [CONTAINER_PATH].
    #If the suituation changed while the container monitor is upgrading.
    #You could create some fs event in the [CONTAINER_PATH]

    def __init__(self, logger, config, task_name=TASK_NAME):
        """
        Analyze the difference between [self._snapshot_path] and 
        [self._base_data_path] to refresh real time information of con-
        tainers in centralized server.
        """
        global Logger
        Logger = logger
        self._task_name = task_name

        try:
            self._worker = EtcdRegister(config['etcd_address'])
            self._snapshot_path = config['snapshot_path']
            self._base_data_path = config['base_data_path']
            self._white_list = config['white_list']

            self._input = None
            self._base_dataset = None
            self._snapshot_data_by_id = None
            self._snapshot_data_by_warden = None
            self._snapshot_dataset_by_warden = None
            self._snapshot_dataset_by_id = None


        except BaseException, err:
            err = sys.exc_info()
            for filename, lineno, func, text in traceback.extract_tb(err[2]): 
                Logger.error("%s line %s in %s "%(filename, lineno, func))
                Logger.error("=> %s "%(repr(text)))


    def _refresh_dataset(self):
        """ Refresh the dataset of an etcd_task object."""

        self._input = DeaData(self._snapshot_path)
        self._base_dataset = self.base_dataset()
        self._snapshot_data_by_id = self.snapshot_data_by_id()
        self._snapshot_data_by_warden = self.snapshot_data_by_warden()
        self._snapshot_dataset_by_warden = self.snapshot_dataset_by_warden()
        self._snapshot_dataset_by_id = self.snapshot_dataset_by_id()        

    def base_dataset(self):
        """ The base dataset """

        #Check whether the existence of analysis directories.
        if not os.path.exists(self._base_data_path):
            Logger.error("Base data path %s not exists!"%self._base_data_path)
            return set([])
        data_list = os.listdir(self._base_data_path) 
        #Remove the unuseful directory no responding to containers from dataset
        data_list = [dirn for dirn in data_list if dirn not in self._white_list]
        return set(data_list)
    
    def snapshot_data_by_id(self):
        'return the snapshot data by instance id'
        return self._input.index_by_kwd('instance_id')

    def snapshot_data_by_warden(self):
        'return the snapshot data by warden_handle'
        print self._input.index_by_kwd('warden_handle')
        return self._input.index_by_kwd('warden_handle')

    def snapshot_dataset_by_id(self):
        'return the snapshot keys by instance ids'
        return set(self._snapshot_data_by_id.keys())

    def snapshot_dataset_by_warden(self):
        'return the snapshot keys by warden_handle'
        return set(self._snapshot_data_by_warden.keys())

    def register_container_to_app(self, app_id, handle, container):
        """
        Register container attributes to apps directory on the remote server;

        Params
        =====
        app_id:  application id;
        handle:  a container handle managed by warden;
        container:  a container object

        Return
        =====
        None
        """
        for para in CONTAINER_REQ_PARAMS:
            app_key = '{}/{}/{}'.format(APPS_DIR, app_id, handle)
            con_key = '{}/{}'.format(CONTAINERS_DIR, handle)
            para_key = para
            if para in CONTAINERS_REQ_MAPS:
                para_key = CONTAINERS_REQ_MAPS[para]
                prefix = '/' + CONTAINERS_REQ_MAPS[para]
            else:
                prefix = '/' + para

            val = container[para_key]

            #update application directory on etcd.
            self._worker.set_key(app_key + prefix, val)
            #update containers directory on etcd.
            self._worker.set_key(con_key + prefix, val)

        #update agent directory on etcd.
        agent_key = AGENTS_DIR + '/' + container['ip'] + '/' + handle
        self._worker.set_key(agent_key, handle)
 
    def query_by_handle(self, handle, key):
        """
        Query container data from containers directory;;
        
        Params
        =====
        handle:  container handle managed by warden_handle
        key:       the directory key of etcd;

        Return
        =====
        The value of this handle in this directory
        """
        query_key = '{}/{}/{}'.format(CONTAINERS_DIR, handle, key)
        query_resp, _ = self._worker.check_existence(query_key)
        
        if not query_resp: 
            return None
        return query_resp.key.get('value')
        
    def query_by_app(self, app_id, handle, key):
        """
        Query container data from application directory;
        
        Params
        =====
        app_id:   application id;
        handle:  container handle managed by warden_handle
        key:       the directory key of etcd;

        Return
        =====
        The value of this handle in this directory
        """
      
        query_key = '{}/{}/{}/{}'.format(APPS_DIR, str(app_id), handle, key)
        query_resp, _ = self._worker.check_existence(query_key)

        if not query_resp: 
            return None
        return query_resp.key.get('value')

    def query_handles_by_ip(self, addr):
        """
        Query  all containers on the specified agent from agents directory;
        
        Params
        =====
        addr:  the agent ip;

        Return
        =====
        The handle list on this agent;
        """
        query_key = '{}/{}'.format(AGENTS_DIR, addr)
        query_resp, _ = self._worker.check_existence(query_key, 
            recursive='true')
        if not query_resp: 
            return None
        handles = [hdl['key'].split('/')[3] for hdl in query_resp[1]['nodes']]

        return handles

    def delete_by_app(self, app_id, handle):
        """
        Delete container data from  applications directory;
        
        Params
        =====
        app_id:   application id;
        handle:  container handle managed by warden_handle
        key:       the directory key of etcd;

        Return
        =====
        No return.
        """
        query_key = '{}/{}'.format(APPS_DIR, str(app_id), handle)
        self._worker.delete_key(query_key)
        
    def delete_by_handle(self, handle):
        """
        Delete container data from containers directory;
        
        Params
        =====
        handle:  container handle managed by warden_handle
        key:       the directory key of etcd;

        Return
        =====
        No return.
        """

        query_key = '{}/{}'.format(CONTAINERS_DIR, handle)
        self._worker.delete_key(query_key)

    def update_missing(self):
        """
        Update the containers that not recorded on the snapshot file.
        NOTE:  
        1. If container info could be found in snapshot file, update the 
            etcd data by snapshot data;
        2. If container info not in the snapshot file, just update the sta
            tus(generally, it means the container are STOPPED or CRASHED); 
        """

        missing = self._base_dataset - self._snapshot_dataset_by_warden
        print self._base_dataset
        print self._snapshot_dataset_by_warden
        if len(missing): 
            Logger.debug("Found missing containers, writing to etcd.")
        print 'missing '
        print missing
        for handle in missing:
            instance_id = self.query_by_handle(handle, 'instance_id')
            app_id = self.query_by_handle(handle, 'app_id')
            print 'instance_id {}'.format(instance_id)
            print 'app_id {}'.format(app_id)
            if (not instance_id) or (not app_id): 
                continue

            instance_info = self._snapshot_data_by_id.get(instance_id)

            if instance_info:
                #update container data to etcd, if the container is recorded .
                self.register_container_to_app(app_id, handle, instance_info)
            else:
                #update container state, if it couldn't be found in snapshot.
                prev_state = self.query_by_app(app_id, handle, 'state')

                if prev_state != 'CRASHED':
                    current_state_in_apps = '{}/{}/{}/{}'.format(
                        APPS_DIR, str(app_id), handle, 'state')
                    current_state_in_cons = '{}/{}/{}'.format(
                        CONTAINERS_DIR, handle, 'state')
                                                
                    self._worker.set_key(current_state_in_apps, 'STOPPED')
                    self._worker.set_key(current_state_in_cons, 'STOPPED')

    def erease_extra(self):
        """
        Delete extra container information, since they were cleared by warden.
        """
        extra = self._snapshot_dataset_by_warden - self._base_dataset

        if len(extra) > 0: 
            Logger.debug('Found stale containers in dea.')

        for handle in extra:
            data_ins = self._snapshot_data_by_warden.get(handle)
            if not data_ins: 
                continue
            #update application directory of etcd.
            app_dir_key = '{}/{}/{}'.format(APPS_DIR, 
                data_ins['app_id'], handle)

            self._worker.check_and_delete(app_dir_key)

            #update the containers directory  of etcd.   
            con_dir_key = '{}/{}'.format(CONTAINERS_DIR, handle)
            self._worker.check_and_delete(con_dir_key)
  
            #update agent directory of etcd.   
            agent_key = '{}/{}/{}'.format(AGENTS_DIR, 
                data_ins['ip'], handle)
            self._worker.check_and_delete(agent_key)

    def update_active(self):
        """
        Update active containers information to etcd.
        """
        active = self._base_dataset & self._snapshot_dataset_by_warden

        for handle in active:
            instance_info = self._snapshot_data_by_warden.get(handle)
            app_id = instance_info['app_id']
            if not app_id: 
                continue
      
            self.register_container_to_app(app_id, handle, instance_info)
            
    def sync_with_server(self):
        """
        Compare local data with etcd server, to erease expired records.
        """
        handles_in_server = self.query_handles_by_ip(local_ip())

        if not handles_in_server: 
            return

        for hdl in handles_in_server:
            if hdl not in self._base_dataset:
                app_id = self.query_by_handle(hdl, 'app_id')
                self.delete_by_handle(hdl)
                self.delete_by_app(app_id, hdl)        

    def start(self):
        'start task'
        self._refresh_dataset()
        self.erease_extra()
        self.update_missing()
        self.update_active()
        self.sync_with_server()
