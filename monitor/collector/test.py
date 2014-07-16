#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,cookielib,socket

url = "http://10.36.166.46:9000/collector/state_update"
params = {'ip':"1.1.1.1", 'handle':'aaaaa', 'state': 'STOPPED'}
req = urllib2.Request(url, headers={})
req.add_header('Accept','application/json')
req.get_method = lambda: 'POST'
page = urllib2.urlopen(req)
print len(page.read())
url_params = urllib.urlencode(params)
#final_url = url + "?" + url_params
final_url = url
data = urllib2.urlopen(final_url).read()
print "Method:get ", len(data)

def get_request():
    socket.setdefaulttimeout(5)
    params = {"wd":"a","b":"2"}
    req = urllib2.Request(url, headers=i_headers)
    request.add_header('Accept','application/json')
    request.get_method = lambda: 'PUT'
    try:
        page = urllib2.urlopen(req)
        print len(page.read())
        url_params = urllib.urlencode({"a":"1", "b":"2"})
        final_url = url + "?" + url_params
        print final_url
        data = urllib2.urlopen(final_url).read()
        print "Method:get ", len(data)
    except urllib2.HTTPError, e:
        print "Error Code:", e.code
    except urllib2.URLError, e:
        print "Error Reason:", e.reason
