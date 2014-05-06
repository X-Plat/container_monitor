'''\
CONFIG_ETCD:
    - etcd register configures;

Configs:
    - task: the monitor task type;
    - monitor_dir: the directory to monitor;
    - snapshot_path: the instance snapshot file;
    - etcd_address: the etcd server address;
    - etcd_cluster: the cluster suff
'''

CONFIG_ETCD = {
   'task'                      : 'register',
   'monitor_dir'               : '/tmp/warden/containers',
   'base_data_path'            : '/tmp/warden/containers',
   'snapshot_path'             : '/tmp/dea_ng/tmp/dea_ng/db/instances.json',
   'etcd_address'              : 'http://127.0.0.1:4001',
   'white_list'                :  [ 'tmp' ],
   'etcd_cluster'              : 'test'
}
