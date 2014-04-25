"""
The protocol for etcd operation;
"""
#The valid etcd direcotries;
CONTAINERS_DIR = '/containers'
APPS_DIR = '/apps'
AGENTS_DIR = '/agents'

#This dict given the relationship between snapshot data
#and etcd data keys;
CONTAINERS_REQ_MAPS = {
    'inner_ip' : 'warden_host_ip',
    'timestamp' : 'state_timestamp',
    'ins_index' : 'instance_index'
}

#Container attributes write to etcd.
CONTAINER_REQ_PARAMS = [
    'app_id',
    'ip',
    'inner_ip',
    'instance_id',
    'ins_index',
    'state',
    'timestamp'
]
