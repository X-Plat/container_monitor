# -*- coding: iso-8859-1 -*-
import etcd
import urllib
from error import *
from etcd_protocol import *

DEFAULT_ETCD_ADDR = "http://127.0.0.1:4001"

class EtcdRegister(object):

    def __init__(self, addr):
        """
        Add error process to methods of `python-etcd` library.
        """
        remote_host, remote_port = self._parse_server(addr)
        self._etcd = etcd.Client(host=remote_host, port=remote_port)  
        
    def _parse_server(self, addr):
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
            addr = DEFAULT_ETCD_ADDR
        try: 
            _, str1 = urllib.splittype(addr)
            host, _ = urllib.splithost(str1)
            host, port = urllib.splitport(host)
        except BaseException:
            host, port = "127.0.0.1", "4001"

        return host, int(port)

    def check_existence(self, key, recursive='false'):
        """
        check the key on etcd server;
        
        Params
        =====
        key:  the specified key to query;
        recursive:  recursive query or not;

        Return
        =====
        resp:  query result;
        err:    error desc if occured;
        """
        res, error = None, None
        try:
            if recursive == 'true':
                res = self._etcd.read(key, recursive='true')
            else:
                res = self._etcd.get(key)
        except BaseException:
            error = '%s not exist'%key
        return res, error

    def set_key(self, key, value):
        """
        Set the key-value on etcd server;
        
        Params
        =====
        key:  the specified key to write;
        value:  the value to write;

        Return
        =====
        status:  operation status, True => Success, False => Failed;
        err:    error desc if occured;
        """
        error = None
        try:
            self._etcd.set(key, value)
            status = True
        except BaseException, err:
            status = False
            error = 'Set %s from etcd failed, %s.'%(key, err)
        return status, error

    def delete_key(self, key):
        """
        Delete the key on etcd server;
        
        Params
        =====
        key:  the specified key to delete;

        Return
        =====
        status:  operation status, True => Success, False => Failed;
        err: error desc if occured;
        """
        try:
            self._etcd.delete(key, 'true')
            status = True
        except BaseException:
            status = False
            error = 'Delete %s from etcd failed.'%key
        return status, error
 
    def check_and_delete(self, key):
        """
        Check the key on etcd server, and delete if exists;
        
        Params
        =====
        key:  the specified key for operation;

        Return
        =====
        status:  operation status, True => Success, False => Failed;
        err:  error desc if occured;
        """
        error = None

        if self.check_existence(key):
            status, error = self.delete_key(key)
        else:
            status = False
            error = '%s not exist, skip deleting.' %key
        return status, error

    def query_in_nodes(self, given_key, nodes):
        """
        Query in given nodes data;
        
        Params
        =====
        given_key:  the specified key for operation;
        nodes:        the nodes data for query;

        Return
        =====
        response: the value paired with given key;
        err:  error desc if occured;
        """
        response, error = None, None

        for node in nodes:
            key = node['key'].split('/')[3]
            if key == given_key:
                response = node['value']
                return response, error
            else:
                pass
        return response, KEY_NOT_EXISTS
               