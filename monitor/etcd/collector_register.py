# -*- coding: iso-8859-1 -*-
import time
import re
import os, sys
import urllib
from itertools import count
from functools import wraps
import requests, json

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
    Parse collector server address;
    Params
    =====
    addr: collector address

    Return
    =====
    (host, port) : collector host and port ;
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
        Logger.debug("[COLLECTOR]: %s time cost: %.3f."%(func.__name__, spent_time))
        return ret
    return wrapper

class CollectorRegister(object):
    'collector register worker'

    def __init__(self, logger, collector='127.0.0.1:8003', collector_timeout=3):
        """
        Analyze the difference between [self._snapshot_path] and
        [self._base_data_path] to refresh real time information of con-
        tainers in centralized server.
        """
        global Logger
        Logger = logger
        self.logger = logger

        try:
            self.collector_ip, self.collector_port = parse_server(collector)
            self._collector_timeout = collector_timeout

        except BaseException, err:
            err = sys.exc_info()
            for filename, lineno, func, text in traceback.extract_tb(err[2]):
                Logger.error("%s line %s in %s "%(filename, lineno, func))
                Logger.error("=> %s "%(repr(text)))


    @timecost
    def request_collector(self, action, **args):
        resp, error = None, None
        try:
            headers = {'content-type': 'application/json'}
            api = '/collector/{}'.format(action)
            url = 'http://{}:{}{}'.format(self.collector_ip, self.collector_port, api)
            method = REQUEST_METHOD[action]
            http_method = getattr(requests, method)
            raw_resp = http_method(url, data=json.dumps(args), headers=headers, timeout=self._collector_timeout)
            resp = json.loads(raw_resp.text)
            if resp['rescode'] != 0:
               error = resp['msg']
        except requests.exceptions.Timeout as ex:
            error = ex
        except Exception as ex:
            error = ex
        return resp, error

