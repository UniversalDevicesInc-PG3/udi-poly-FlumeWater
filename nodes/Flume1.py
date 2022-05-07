
from udi_interface import Node,LOGGER

class Flume1Node(Node):

    def __init__(self, controller, primary, address, name, device):
        super(Flume1Node, self).__init__(controller.poly, primary, address, name)
        self.device = device
        self.lpfx = '%s:%s' % (address,name)
        controller.poly.subscribe(controller.poly.START,                  self.handler_start, address) 

    def handler_start(self):
        LOGGER.debug('enter')
        self.setDriver('ST', 1)
        LOGGER.debug('exit')

    def query(self,command=None):
        self.reportDrivers()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
    ]
    id = 'flume1'
    commands = {
                }
