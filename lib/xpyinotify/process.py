# -*- coding: iso-8859-1 -*-

import yaml, codecs, sys, os.path, optparse

from pyinotify import ProcessEvent

class Process(ProcessEvent):
    def __init__(self, logger, config):
       self.logger = logger
       self.ins_file = config['instance_file']
       self.bns_base = config['bns_base']
       self.container_relative_path = config['container_relative_path']
       self.container_base_path = config['container_base_path']
       self.clusterid = config['cluster_id']
       self.clustersuf = config['cluster_suffix']

    def process_default(self, event):
        """
        override default processing method
        """
        self.logger.debug('Process::process_default')
        # call base method
        super(Process, self).process_default(event)
    
    def process_IN_MOVED_TO(self, event):
        """
        process 'IN_MOVED_TO' events 
        """
        self.logger.debug('Process::process_IN_MOVED_TO')
        super(Process, self).process_default(event)
        fl = yaml.load(file(self.ins_file,'rb').read())
        self.update_bns_link(fl)

    def make_bns_path(self, ins):
        """
        process make bns_path 
        """
        bns_offset = 10000*int(ins['application_db_id'])+int(ins['instance_index'])*10+int(self.clusterid)
        bns_node = ins['tags']['bns_node']
        bnsset = bns_node.split('-')
        bns_name = '%s-%s-%s'%(bnsset[0],bnsset[1],bnsset[2])
        bns_path = "%s/%s.%s.%s" %(self.bns_base, bns_offset,bns_name,self.clustersuf)
        return bns_path

    def update_bns_link(self, agent_data):
        """
        generate bns link for instances
        """
        self.logger.info('Starting checking the links.')
        raw_links = os.listdir(self.bns_base)
        current_links = set([])
        for lk in raw_links:
           current_links.add(self.bns_base + '/' + lk)

        required_links = set([])

        for ins in agent_data['instances']:
            if 'RUNNING' == ins['state']:
                 container_path = self.container_base_path + '/' + \
                     ins['warden_handle'] + '/%s' %(self.container_relative_path)
                 if  not os.path.exists(container_path):
                     self.logger.error('Container %s not exist, the data file is staled.' %(\
                     ins['warden_handle']))
                 else:
                     bns_path = self.make_bns_path(ins)
                     required_links.add(bns_path)
                     if not os.path.islink(bns_path):
                         self.logger.info('Ready to create symlink for #%s instance of %s.'
                         %(ins['instance_index'], ins['application_name']))
                         os.symlink(container_path, bns_path)
                     elif not os.access(bns_path, os.W_OK):
                         self.logger.warn('Remove staled bns path %s!'%(bns_path))
                         os.remove(bns_path)

                         self.logger.info('Recreating symlink for #%s instance of %s.'
                         %(ins['instance_index'], ins['application_name']))
                         os.symlink(container_path, bns_path)
                     else:
                         self.logger.warn('Ignored LINK-OP since the link for #%s of %s exists!')
 
        extra_links = current_links - required_links
        self.logger.debug('Extra links %s' %extra_links)

        if extra_links:
            for extra in extra_links:
                 self.logger.warn('Deleting extra link for %s' %(extra))
                 os.remove(extra)
        
