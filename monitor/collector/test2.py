#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: gaopenghigh<gaopenghigh@gmail.com>

import requests, json
payload = {'key1': 'value1', 'key2': 'value2'}

url="http://10.36.166.46:9000/collector/state_update"

headers = {'content-type': 'application/json'}
def func(**args):
    print args


func(ip=1, host=2, test=3)

mtd = getattr(requests, 'post')

r = mtd(url, data=json.dumps(payload), headers=headers)

print r.text

