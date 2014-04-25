'''\
CONFIG_ETCD: 
    - etcd register configures;

Configs:
    - task: the monitor task type;
    - monitor_dir: the directory to monitor;
    - instance_file: the instance snapshot file;
    - etcd_address: the etcd server address;
    - etcd_cluster: the cluster suff
'''

CONFIG_ETCD = {
   'task'                      : 'register',
   'monitor_dir'               : '/tmp/containers',
   'instance_file'             : '/tmp/dea_ng/db/instances.json',
   'etcd_address'        : 'http://127.0.0.1:4001',
   'etcd_cluster'          : 'test'
}
