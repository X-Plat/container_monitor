'''
CONFIG_BNS:
    - configure for bns symlink of containers;

Configs:
    - task: the monitor task type;
    - monitor_dir: the directory for monitor;
    - instance_file: the instnace snapshot file;
    - bns_base: the directory bns symlinks placed;
    - container_base_path: the containers directory;
    - container_relative_path: the relative path to instance workspace;
    - cluster_id: the cluster id;
    - bns_cluster: the cluster suffex for bns identification;
    '''

CONFIG_BNS = {
   'task'                         : 'link',
   'monitor_dir'                  : '/tmp/dea_ng/tmp/dea_ng/db',
   'instance_file'                : '/tmp/dea_ng/tmp/dea_ng/db/instances.json',
   'bns_base'                     : '/tmp/bns',
   'container_base_path'          : '/tmp/warden/containers',
   'container_relative_path'      : '/tmp/rootfs/',
   'cluster_id'                   : '2',
   'cluster_suffix'               : 'cluster',
}
