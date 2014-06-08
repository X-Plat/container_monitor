# -*- coding: iso-8859-1 -*-
'''\
worker module for bns symlink;

Class: Monitor4BNS
    - monitor for bns symlink management;
    - it could monitor the fs events in specified dir,
       updates the symlink for containers;
'''
import yaml, os.path
import time
from pyinotify import ProcessEvent
from monitor.common.common import ensure_read_yaml

class Monitor4BNS(ProcessEvent):
    '''\
    Class: Monitor4BNS
        - monitor for bns symlink management;

    Attributes:
        - logger: log object for logging
        - ins_file: instance file about the instance snapshot;
        - bns_base: base directory of bns links;
        - container_relative_path: relative path to container root;
        - clusterid: cluster identificaton id;
        - cluster_suf: cluster name suffix;
    '''
    def __init__(self, logger, config):
        #TODO: validate the configuration errors
        self.logger = logger
        self.ins_file = config['instance_file']
        self.bns_base = config['bns_base']
        self.container_relative_path = config['container_relative_path']
        self.container_base_path = config['container_base_path']
        self.clusterid = config['cluster_id']
        self.clustersuf = config['cluster_suffix']

    def process_default(self, event):
        'override default processing method'
        self.logger.debug('Monitor4BNS::process_default')
        super(Monitor4BNS, self).process_default(event)

    def process_IN_MOVED_TO(self, event):
        'process IN_MOVED_TO events'
        self.logger.debug('Monitor4BNS::process_IN_MOVED_TO')
        super(Monitor4BNS, self).process_default(event)

        snapshot = ensure_read_yaml(self.ins_file)
        self.update_bns_link(snapshot)

    def make_bns_path(self, ins):
        'process make bns_path'
        #TODO : trap exceptions
        bns_offset = 10000*int(ins['application_db_id'])+\
                             int(ins['instance_index'])*10+\
                             int(self.clusterid)
        bns_node = ins['tags']['bns_node']
        bnsset = bns_node.split('-')
        bns_name = '{}-{}-{}'.format(bnsset[0], bnsset[1], bnsset[2])
        bns_path = "{}/{}.{}.{}".format(self.bns_base, bns_offset,
                                                     bns_name, self.clustersuf)
        return bns_path

    def notify_etcd_register(self, test_dir):
        """
        mkdir test dir for register task
        """
        if not test_dir:
            return False
        try:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)
            os.makedirs(test_dir)
            time.sleep(0.5)
            os.rmdir(test_dir)
        except IOError, err:
            self.logger.warn("Notify etcd task failed with {}".format(err))
        except Exception, err:
            self.logger.warn("Notify etcd task failed with {}".format(err))

    def update_bns_link(self, agent_data):
        """
        generate bns link for instances
        """
        #TODO(jacky): trap exceptions
        self.logger.info('Starting checking the links.')
        if not os.path.exists(self.bns_base):
            os.makedirs(self.bns_base)

        raw_links = os.listdir(self.bns_base)
        current_links = set([])
        for lnk in raw_links:
            current_links.add(self.bns_base + '/' + lnk)

        required_links = set([])
        for ins in agent_data['instances']:
            if 'RUNNING' == ins['state']:
                container_path = self.container_base_path + '/' + \
                    ins['warden_handle'] + '/%s' %(self.container_relative_path)
                if  not os.path.exists(container_path):
                    self.logger.error(' {} not exist, snapshot staled.'.format(
                        ins['warden_handle']))
                else:
                    bns_path = self.make_bns_path(ins)
                    required_links.add(bns_path)
                    if not os.path.islink(bns_path):
                        self.logger.info('Create symlink for {}-{}.'.format(
                            ins['application_name'], ins['instance_index']))
                        register_dir = self.container_base_path + '/' + ins['warden_handle'] + '-fresh'
                        self.notify_etcd_register(register_dir)
                        os.symlink(container_path, bns_path)
                    elif not os.access(bns_path, os.W_OK):
                        self.logger.warn('Remove staled link {}'.format(
                            bns_path))
                        os.remove(bns_path)
                        self.logger.info('Recreate symlink for {}-{}.'.format(
                            ins['application_name'], ins['instance_index']))
                        register_dir = self.container_base_path + '/' + ins['warden_handle'] + '-fresh'
                        self.notify_etcd_register(register_dir)
                        os.symlink(container_path, bns_path)
                    else:
                        self.logger.warn('link for {}-{} exist, skip!'.format(
                             ins['application_name'], ins['instance_index']))

        extra_links = current_links - required_links
        self.logger.debug('Extra links %s' %extra_links)

        if extra_links:
            for extra in extra_links:
                self.logger.warn('Deleting extra link for %s' %(extra))
                os.remove(extra)
        register_dir = self.container_base_path + '/' + 'snapshot-changed'
        self.notify_etcd_register(register_dir)
