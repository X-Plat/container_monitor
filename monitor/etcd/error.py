'''
exceptions
'''
class EtcdException(Exception):
    'monitor exception'
    def __init__(self, desc):
        self.value = desc

class MonitorException(Exception):
    'monitor exception'
    def __init__(self, desc):
        self.value = desc
