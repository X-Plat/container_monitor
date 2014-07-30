"""
The protocol for etcd operation;
"""
#The valid etcd direcotries;
COLLECTOR_DIR = '/collector'

#This dict given the relationship between snapshot data
#and etcd data keys;
REQUEST_METHOD = {
    'state_update'    : 'post',
    'state_query'     : 'get',
    'all_containers'  : 'post'
}


