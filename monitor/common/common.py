'''\
common object
'''
import yaml

from socket import socket, SOCK_DGRAM, AF_INET

def local_ip():
    'return the local ip address'
    try: 
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect(('route.testjpaas.baidu.com', 0))
        return list(sock.getsockname())[0]
    except BaseException:
        return "UNKNOWN"
    finally:
        sock.close()

def ensure_read_yaml(filename):
    'read snapshot'
    try:
        snapfd = yaml.load(file(filename, 'rb').read())
    except BaseException:
        snapfd = {} 
    return snapfd
