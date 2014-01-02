# -*- coding: iso-8859-1 -*-
import yaml, codecs, sys, os.path, optparse

from pyinotify import ProcessEvent
import etcd
from socket import socket, SOCK_DGRAM, AF_INET




myetcd = etcd.Client('10.36.63.68', 4001)

resp = myetcd.read('/containers', recursive = 'true')


print resp[1]['nodes']
