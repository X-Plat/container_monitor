# -*- coding: iso-8859-1 -*-
import yaml, codecs, sys, os.path, optparse
import re
from pyinotify import ProcessEvent
import etcd
from socket import socket, SOCK_DGRAM, AF_INET

class ContainerRegister(ProcessEvent):
    def __init__(self, logger, config):
       self.logger = logger
       self.handle = None
       self.container_base = config['monitor_dir']
       self.ins_file = config['instance_file']
       self.etcd = etcd.Client(host=config['registry_server_ip'], 
                               port=config['registry_server_port'])

    def process_default(self, event):
        """
        override default processing method
        """
        self.logger.debug('ContainerRegister::process_default')
        # call base method
        super(ContainerRegister, self).process_default(event)

    def local_ip(self):
        """
        Get local ip
        """
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(('www.baidu.com', 0))
        ip = list(s.getsockname())[0]
        return ip

    def process_IN_DELETE(self, event):
        """
        process 'IN_DELETE' events 
        """
        self.logger.debug('ContainerRegister::process_IN_DELETE')
        super(ContainerRegister, self).process_default(event)
        self.container_task()

    def process_IN_CREATE(self, event):
        """
        process 'IN_CREATE' events
        """
        self.logger.debug('ContainerRegister::process_IN_CREATE')
        super(ContainerRegister, self).process_default(event)
        self.container_task()

    def container_task(self):
        try:
            fl = yaml.load(file(self.ins_file,'rb').read())
        except Exception,e:
            self.logger.error('Parse yaml file failed with %s' %e.message)
            fl = {}

        self.register_with_etcd(fl)         

    def right_timestamp(self, state):
        timestamp = {
           'CRASHED' : 'state_crashed_timestamp',
           'RUNNING': 'state_running_timestamp',
        }
        key = timestamp.get(state, 'n/a')
        return key

    def container_dict(self, instances):
        cdict = {}
        try:
            for ins in instances:
                handle = ins.get('warden_handle')
                if not handle: continue
                cdict[handle] = {}
                cdict[handle]['state'] = ins.get('state')
                cdict[handle]['app_id'] = ins.get('tags').get('bns_node')
                cdict[handle]['instance_id'] = ins.get('instance_id')
                cdict[handle]['app_name'] = ins.get('application_name')
                cdict[handle]['state_timestamp'] = ins.get(self.right_timestamp(ins.get('state')), 0)
        except Exception,e:
           self.logger.error('Generate container info from json file failed %s' %e.message)
        return cdict

    def instance_dict(self, instances):
        idict = {}
        try:
            for ins in instances:
                instance_id = ins.get('instance_id')
                if not instance_id: continue
                idict[instance_id] = {}
                idict[instance_id]['state'] = ins.get('state')
                idict[instance_id]['handle'] = ins.get('handle')
                idict[instance_id]['app_id'] = ins.get('tags').get('bns_node')
                idict[instance_id]['app_name'] = ins.get('application_name')
                idict[instance_id]['state_timestamp'] = ins.get(self.right_timestamp(ins.get('state')), 0)
        except Exception,e:
           self.logger.error('Generate instance dict from json file failed %s' %e.message)
        return idict

    def check_existence(self, key):
        """
        check the key with etcd
        """
        if not key: return None

        res = None
        try:
            res = self.etcd.get(key)
        except:
            self.logger.debug('%s not exist'%key)
            pass
        return res

    def check_existence_recursive(self, key):
        """
        check the key with etcd
        """
        if not key: return None

        res = None
        try:
            res = self.etcd.read(key, recursive = 'true')
        except:
            self.logger.debug('%s not exist'%key)
            pass
        return res

    def set_key(self, key, value):
        """
        set key to etcd
        """
        if not key: return False
        try:
            self.etcd.set(key, value)
            self.logger.info('Set %s from etcd succ.'%key)
        except Exception,e:
            self.logger.warn('Set %s from etcd failed.'%key)
        return True

    def delete_key(self, key):
        """
        delete key from etcd
        """
        if not key: return False

        try:
            self.etcd.delete(key, 'true')
            self.logger.debug('Delete %s from etcd succ' %key)
        except:
            self.logger.warn('Delete %s from etcd failed.'%key)
        return True 
 
    def check_and_delete(self, key):
        """
        check the key with etcd, delete if exist
        """
        if self.check_existence(key):
           self.delete_key(key)
        else:
           self.logger.debug('%s not exist, skip deleting.' %key)

    def update_container_status(self, metadata, handle_key):

        state_key = handle_key + '/' + 'state'
        state_value = metadata.get('state')

        ip_key = handle_key + '/' + 'ip'
        ip_value = self.local_ip()

        timestamp_key = handle_key + '/' + 'timestamp'
        timestamp_value = metadata.get('state_timestamp')
        self.set_key(state_key, state_value)
        self.set_key(ip_key, ip_value)
        self.set_key(timestamp_key, timestamp_value)

    def get_appid_from_nodes(self, nodes):
        for node in nodes:
            key = node['key'].split('/')[3]
            if key == 'app_id':
               return node['value']
            else:
               pass      

    def check_local_from_nodes(self, nodes):
        """
        get ip info from nodes
        """
        ip_pattern = re.compile('\/containers\/[\w]+\/ip')
        for n in nodes:
           if ip_pattern.match(n['key']) and n['value'] == self.local_ip():
               return True
           else:
               pass
        return False

    def register_with_etcd(self, agent_data):
        """
        check the container information
        """
        if not agent_data.get('instances'): return False

        self.logger.info('Starting checking the containers.')
        #get the container list in container base path
        containers_list = os.listdir(self.container_base)
        containers_list.remove('tmp')
        containers = set(containers_list)
     
        #get the containers managed by dea
        containers_in_dea = self.container_dict(agent_data['instances'])
        instances_in_dea = self.instance_dict(agent_data['instances'])

        handles_in_dea = set(containers_in_dea.keys())
       
        extra = handles_in_dea - containers

        if len(extra) > 0: self.logger.debug('Found stale containers in dea.')

        #delete handles that in dea while not in container base path
        for handle in extra:
            app_key = '/apps/' + str(containers_in_dea[handle]['app_id']) + '/' + handle
            container_key = '/containers/' + handle
            self.logger.debug('deleting %s ' % container_key)
            self.logger.debug('deleting %s ' % app_key)
            self.check_and_delete(app_key)
            self.check_and_delete(container_key)
        #Remove containers in warden
        missing = containers - handles_in_dea
        for handle in missing:
            container_ins = '/containers/' + handle + '/instance'
            res = self.check_existence(container_ins)
            if not res: continue
            ins_id = res.key.get('value')
            info = instances_in_dea.get(ins_id)
           
            app_id_key = '/containers/' + handle + '/app_id'
            app_id_res = self.check_existence(app_id_key)
            if not app_id_res: continue
            app_id = app_id_res.key.get('value')

            if info:

                handle_key = '/apps/' + str(app_id) + '/' + handle
                self.logger.debug('update container %s of %s' %(handle, str(app_id)))
                self.update_container_status(info, handle_key)

            else:    
                state_key = '/apps/' + str(app_id) + '/' + handle + '/state'
                self.logger.debug('update state of container %s of %s' %(handle, str(app_id)))
                self.set_key(state_key, 'STOPPED')

        #Update container in dea
        active_containers = containers & handles_in_dea

        for handle in active_containers:
            container = containers_in_dea[handle]
            app_id  = container.get('app_id')
            if not app_id: continue

            handle_key = '/apps/' + str(app_id) + '/' + handle
            self.logger.debug('update info of container %s of %s' %(handle, str(app_id)))
            self.update_container_status(container, handle_key)

            con_ins_key = '/containers/' + handle + '/instance'
            con_id_key = '/containers/' + handle + '/app_id'
            con_ip_key = '/containers/' + handle + '/ip'
            self.set_key(con_id_key, str(app_id))
            self.set_key(con_ins_key, container['instance_id'])
            self.set_key(con_ip_key, self.local_ip())

        containers_keys = '/containers'

        containers_in_etcd = self.check_existence_recursive(containers_keys)
        if not containers_in_etcd: return False
        resp = containers_in_etcd[1]['nodes']
        for c in resp:
            handle = c['key'].split('/')[2]
            self.logger.debug('checking container %s' %handle)
            if not self.check_local_from_nodes(c['nodes']): continue
            self.logger.debug('Checking local containers %s' %handle
)
            if handle not in containers:
                con_key_to_del = '/containers/' + handle
                app_id = self.get_appid_from_nodes(c['nodes'])
                con_app_key = '/apps/' + str(app_id) + '/' + handle
                self.logger.debug('deleting stale container %s in containers' % handle)
                self.logger.debug('deleting stale container %s in apps' %handle)
                self.delete_key(con_key_to_del)
                self.delete_key(con_app_key)

