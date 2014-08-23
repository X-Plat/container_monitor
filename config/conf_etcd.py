'''\
CONFIG_ETCD:
    - etcd register configures;

Configs:
    - task: the monitor task type;
    - monitor_dir: the directory to monitor;
    - base_data_path : the directory to monitor;
    - backup_dir : the containers backup dir ;
    - snapshot_path: the instance snapshot file;
    - etcd_address: the etcd server address;
    - white_list: the white list no need to monitor;
    - etcd_cluster: the cluster suff
'''

CONFIG_ETCD = {
   'task'                      : 'register',
   'monitor_dir'               : '/tmp/warden/containers',
   'base_data_path'            : '/tmp/warden/containers',
   'backup_dir'                : '/tmp/warden/containers_backup',
   'snapshot_path'             : '/tmp/dea_ng/tmp/dea_ng/db/instances.json',
   'etcd_address'              : 'http://127.0.0.1:4001',
   'collector'                 : 'http://127.0.0.1:4001',
   'white_list'                :  [ 'tmp' ],
   'etcd_cluster'              : 'test',
   'enable_collector'          : True
}
