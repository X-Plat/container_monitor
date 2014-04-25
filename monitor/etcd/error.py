'''
exceptions
'''
class EtcdException(Exception):
    'monitor exception'
    def __init__(self, desc):
        Exception.__init__()
        self.description = "[{}] {}".format(
        	self.__class__.__name__.split('.')[1], desc)

class MonitorException(Exception):
    'monitor exception'
    def __init__(self, desc):
        Exception.__init__()
        self.description = "[{}] {}".format(
        	self.__class__.__name__.split('.')[1], desc)
