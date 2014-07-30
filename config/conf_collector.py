'''\
CONFIG_COLLECTOR:
    - collector register configures;

Configs:
    - task: the monitor task type;
    - monitor_dir: the directory to monitor;
    - base_data_path : the directory to monitor;
    - backup_dir : the containers backup dir ;
    - snapshot_path: the instance snapshot file;
    - etcd_address: the etcd server address;
    - white_list: the white list no need to monitor;
    - collector: the collector address
'''

CONFIG_COLLECTOR = {
   'task'                      : 'collector',
   'monitor_dir'               : '/home/work/warden/containers',
   'base_data_path'            : '/home/work/warden/containers',
   'backup_dir'                : '/home/work/warden/containers_backup',
   'snapshot_path'             : '/home/work/dea_ng/tmp/dea_ng/db/instances.json',
   'etcd_address'              : 'http://127.0.0.1:4001',
   'white_list'                :  [ 'tmp' ],
   'collector'                 : 'http://127.0.0.1:8003'
}
