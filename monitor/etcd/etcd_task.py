# -*- coding: iso-8859-1 -*-
import time
import re
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
        self.logger = logger

        try:
            self._worker = EtcdRegister(config['etcd_address'])
            self._snapshot_path = config['snapshot_path']
            self._base_data_path = config['base_data_path']
            self._backup_dir = config['backup_dir']
            self._white_list = config['white_list']
            self._cluster = config['etcd_cluster']

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

        self.logger.debug("refreshing dataset.")
        self._input = DeaData(self._snapshot_path, self._cluster)
        self._base_dataset = self.base_dataset()
        self._snapshot_data_by_id = self.snapshot_data_by_id()
        self._snapshot_data_by_warden = self.snapshot_data_by_warden()
        self._snapshot_dataset_by_warden = self.snapshot_dataset_by_warden()
        self._snapshot_dataset_by_id = self.snapshot_dataset_by_id()

    def base_dataset(self):
        """ The base dataset """

        #Check whether the existence of analysis directories.
        if not os.path.exists(self._base_data_path):
            self.logger.error("Base data path %s not exists!"%self._base_data_path)
            return set([])
        backup = []
        if os.path.exists(self._backup_dir):
            self.logger.debug("list the backup directory {}".format(self._backup_dir))
            backup = os.listdir(self._backup_dir)
        data_list = os.listdir(self._base_data_path)
        data_list.extend(backup)
        #Remove the unuseful directory no responding to containers from dataset
        data_list = [dirn for dirn in data_list if dirn not in self._white_list]
        self.logger.debug("fetch base dataset succ.")
        return set(data_list)

    def snapshot_data_by_id(self):
        'return the snapshot data by instance id'
        return self._input.index_by_kwd('instance_id')

    def snapshot_data_by_warden(self):
        'return the snapshot data by warden_container_path'
        return self._input.index_by_kwd('warden_container_path')

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
            self.logger.debug("set {}:{} to etcd".format(app_key + prefix, val))
            self._worker.set_key(app_key + prefix, val)
            #update containers directory on etcd.
            self.logger.debug("set {}:{} to etcd".format(con_key + prefix, val))
            self._worker.set_key(con_key + prefix, val)


        #update agent directory on etcd.
        agent_key = AGENTS_DIR + '/' + container['ip'] + '/' + handle
        self.logger.debug("set {}:{} to etcd".format(agent_key, handle))
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
            self.logger.debug("{} not in etcd".format(query_key))
            return None
        value = query_resp.key.get('value')
        self.logger.debug("query {} succ with {} from etcd".format(query_key, value))
        return value

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
            self.logger.debug("{} not in etcd".format(query_key))
            return None
        value = query_resp.key.get('value')
        self.logger.debug("get value {} of {} succ with etcd".format(query_key, value))
        return value

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
        if not (query_resp and query_resp.key and 'nodes' in query_resp.key):
            self.logger.debug("no handle in {}".format(query_key))
            return set([])

        handles = [hdl['key'].split('/')[3] for hdl in query_resp[1]['nodes']]
        self.logger.debug("get all handles in {}".format(query_key))
        return set(handles)

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
        query_key = '{}/{}/{}'.format(APPS_DIR, str(app_id), handle)
        self.logger.debug("delete {} from etcd".format(query_key))
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
        self.logger.debug("delete {} from etcd.".format(query_key))
        self._worker.delete_key(query_key)

    def delete_by_agent(self, handle, agent):
        """
        Delete container data from containers directory;

        Params
        =====
        handle:  container handle managed by warden_handle
        agent:       the agent key of etcd;

        Return
        =====
        No return.
        """

        query_key = '{}/{}/{}'.format(AGENTS_DIR, agent, handle)
        self.logger.debug("delete {} from etcd.".format(query_key))
        self._worker.delete_key(query_key)

    @timecost
    def update_container(self, handle):
        """
        Update active containers information to etcd.
        """
        #check in snapshot
        if handle in self._snapshot_dataset_by_warden:
            if handle in self._base_dataset:
                instance_info = self._snapshot_data_by_warden.get(handle)
                app_id = instance_info['app_id']
                self.register_container_to_app(app_id, handle, instance_info)
                self.logger.debug("register container {} to etcd".format(handle))
            else:
                app_id = self.query_by_handle(handle, 'app_id')
                if not app_id:
                    self.logger.debug("app_id of {} not found on  etcd, assuming test event.".format(handle))
                    return
                self.delete_by_handle(handle)
                self.delete_by_app(app_id, handle)
                self.delete_by_agent(handle, local_ip())
                self.logger.debug("delete staled container {} from etcd".format(handle))
        else:
            if handle not in self._base_dataset:
                self.unregister_containers_from_etcd(handle)
                return
            instance_id = self.query_by_handle(handle, 'instance_id')
            app_id = self.query_by_handle(handle, 'app_id')
            if (not instance_id) or (not app_id):
                self.logger.debug("Container not in ETCD, assuming {} TEST or STALED.".format(handle))
            else:
                self.update_container_state(handle)

    def unregister_containers_from_etcd(self, handle):
        """
        unregister container info from etcd
        """
        app_id = self.query_by_handle(handle, 'app_id')
        if not app_id:
            self.logger.debug("app_id of {} not found on  etcd, assuming test event.".format(handle))
            return
        self.delete_by_handle(handle)
        self.delete_by_app(app_id, handle)
        self.delete_by_agent(handle, local_ip())
        self.logger.debug("unregister staled container {} from etcd".format(handle))

    def update_container_state(self, handle):
        """
        update container state to etcd server
        """
        instance_info = self._snapshot_data_by_warden.get(handle)
        if not instance_info:
           return
        local_state = instance_info['state']
        app_id = instance_info['app_id']
        etcd_state = self.query_by_app(app_id, handle, 'state')
        if not etcd_state:
            self.register_container_to_app(app_id, handle, instance_info)
            self.logger.debug("register container {} to etcd".format(handle))
        elif etcd_state != local_state:
            current_state_in_apps = '{}/{}/{}/{}'.format(
                APPS_DIR, str(app_id), handle, 'state')
            current_state_in_cons = '{}/{}/{}'.format(
                CONTAINERS_DIR, handle, 'state')
            self._worker.set_key(current_state_in_apps, local_state)
            self._worker.set_key(current_state_in_cons, local_state)
            self.logger.debug("update inactive handle {} to etcd".format(handle))

    @timecost
    def sync_with_server(self):
        """
        Compare local data with etcd server, to erease expired records.
        """
        self.logger.debug("sync with server.")
        local = local_ip()
        handles_in_server = self.query_handles_by_ip(local)
        handles_in_local = self._base_dataset & self._snapshot_dataset_by_warden
        missing = handles_in_local -  handles_in_server
        extra = handles_in_server - handles_in_local

        for handle in handles_in_local:
            self.update_container_state(handle)

        for handle in missing:
            instance_info = self._snapshot_data_by_warden.get(handle)
            app_id = instance_info['app_id']
            self.register_container_to_app(app_id, handle, instance_info)
            self.logger.debug("register container {} info to etcd".format(handle))

        for handle in extra:
            self.logger.debug("{} not exist any more, delete it".format(handle))
            self.unregister_containers_from_etcd(handle)

    def start(self, notified_dir, event):
        'start task'
        self._refresh_dataset()
        notify_rule = re.compile(r'([a-z,1-9]+)-fresh')
        notify_check = notify_rule.findall(notified_dir)
        if len(notify_check) > 0:
            if event != 'delete':
                self.update_container(notify_check[0])
                self.logger.debug("register fresh container {} to etcd".format(notify_check[0]))
            else:
                self.logger.debug("ignore snapshot clean event.")
        elif notified_dir == 'cm-test':
            if event != 'delete':
                self.sync_with_server()
            else:
                self.logger.debug("ignore cm-test clean event.")
        else:
            self.update_container(notified_dir)

