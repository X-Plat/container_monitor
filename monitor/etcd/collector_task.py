# -*- coding: iso-8859-1 -*-
import time
import re
import os, sys
import urllib
from itertools import count
from functools import wraps
import requests, json
#from monitor.collector.collector_protocol import *
#from monitor.collector.collector_register import EtcdRegister
from monitor.collector.dea_data import DeaData
from monitor.common.common import local_ip
import traceback

#The valid etcd direcotries;
COLLECTOR_DIR = '/collector'

#This dict given the relationship between snapshot data
#and etcd data keys;
REQUEST_METHOD = {
    'state_update'    : 'post',
    'state_query'     : 'get',
    'all_containers'  : 'post'
}

Logger = None

def parse_server(addr):
    """
    Parse etcd server address;
    Params
    =====
    addr: etcd address

    Return
    =====
    (host, port) : etcd host and port ;
    """
    if not addr:
       return '127.0.0.1', "8003"
    try:
        _, str1 = urllib.splittype(addr)
        host, _ = urllib.splithost(str1)
        host, port = urllib.splitport(host)
    except BaseException:
        host, port = "127.0.0.1", "8003"
    return host, int(port)

def timecost(func):
    'record the time cost'
    @wraps(func)
    def wrapper(*args, **kwargs):
        'this decorator used to timing the performance of each collector request.'
        global Logger
        start = time.time()
        ret = func(*args, **kwargs)
        spent_time = time.time() - start
        Logger.debug("%s time cost: %.3f."%(func.__name__, spent_time))
        return ret
    return wrapper

class CollectorTask(object):
    'collector register task'

    TASK_NAME = "collector-task"
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
            self._snapshot_path = config['snapshot_path']
            self._base_data_path = config['base_data_path']
            self._backup_dir = config['backup_dir']
            self._white_list = config['white_list']

            self.collector_ip, self.collector_port = parse_server(config['collector'])
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
        """ Refresh the dataset of an collector_task object."""

        self.logger.debug("refreshing dataset.")
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

    @timecost
    def request_collector(self, action, **args):
        resp, error = None, None
        try:
            headers = {'content-type': 'application/json'}
            api = '/collector/{}'.format(action)
            url = 'http://{}:{}{}'.format(self.collector_ip, self.collector_port, api)
            method = REQUEST_METHOD[action]
            http_method = getattr(requests, method)
            raw_resp = http_method(url, data=json.dumps(args), headers=headers)
            resp = json.loads(raw_resp.text)
            if resp['rescode'] != 0:
               error = resp['msg']
        except BaseException as e:
            error = e
        return resp, error

    @timecost
    def refresh_inactive_containers(self):
        """
        refresh CRASHED/STOPPED containers to collector
        """
        for handle in self._snapshot_dataset_by_warden:
            if handle in self._base_dataset:
                instance_info = self._snapshot_data_by_warden.get(handle)
                state = instance_info['state']
                if state != 'RUNNING':
                    self.update_container_state(handle)

    @timecost
    def update_container(self, handle):
        """
        Update active containers information to collector.
        """
        #check in snapshot
        if handle not in self._base_dataset:
            self.logger.debug("{} not in dataset, unregister it.".format(handle))
            self.unregister_containers_from_collector(handle)
            return

        self.update_container_state(handle)

    def unregister_containers_from_collector(self, handle):
        """
         Delete staled container
        """
        local_state = 'DELETED'
        self.request_collector('state_update', ip=local_ip(), handle=handle, state=local_state)
        self.logger.debug("container {} state change : {} -> {}".format(handle, 'N/A', local_state))

    def update_container_state(self, handle):
        """
        update container state to collector server
        """
        collector_info, error = self.request_collector('state_query', ip=local_ip(), handle=handle)
        self.logger.debug('query state of {}.'.format(handle))
        if error:
            self.logger.debug('query state of {} with error {}.'.format(handle, error))
            return

        instance_info = self._snapshot_data_by_warden.get(handle)
        local_state = None

        if instance_info:
            local_state = instance_info['state']

        collector_state = collector_info.get('state')

        if not collector_state:
            if not local_state:
                self.logger.debug('container {} not recorded in local and collector.'.format(handle))
                return
            self.request_collector('state_update', ip=local_ip(), handle=handle, state=local_state)
            self.logger.debug("container {} state change : {} -> {}".format(handle, 'N/A', local_state))
        elif collector_state != 'CRASHED':
            local_state = 'STOPPED'
            self.request_collector('state_update', ip=local_ip(), handle=handle, state=local_state)
            self.logger.debug("container {} state change : {} -> {}".format(handle, collector_state, local_state))
        else:
            pass

    @timecost
    def push_container_list(self):
        """
        push container list to collector
        """
        self.logger.debug("push container list to collector.")
        local = local_ip()
        resp, error = self.request_collector('all_containers', ip=local, containers=list(self._base_dataset))
        if error:
           self.logger.debug("push container list to collector failed with {}".format(error))

    def start(self, notified_dir, event):
        'start task'
        notify_rule = re.compile(r'([a-z,0-9]+)-fresh')
        notify_check = notify_rule.findall(notified_dir)

        if len(notify_check) > 0:
            self.logger.debug("ignore etcd task trigger event.")
        elif notified_dir == 'snapshot-changed':
            if event == 'create':
                self._refresh_dataset()
                self.refresh_inactive_containers()
                self.logger.debug("refresh inactive containers.")
            else:
                self.logger.debug("ignore snapshot change clean event.")
        elif notified_dir == 'cm-test':
            pass
        elif notified_dir == 'collector-test':
            if event == 'create':
                self._refresh_dataset()
                self.push_container_list()
            else:
                self.logger.debug("ignore cm-test clean event.")
        else:
            self._refresh_dataset()
            self.update_container(notified_dir)

