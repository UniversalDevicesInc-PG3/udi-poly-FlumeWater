
from udi_interface import Node,LOGGER
import sys
import time
import urllib3
import pyflume
from datetime import timedelta
from requests import Session

def myfloat(value, prec=4):
    """ round and return float """
    if value is None:
        return 0
    return round(float(value), prec)

class Flume2Node(Node):

    def __init__(self, controller, primary, address, name, device):
        super(Flume2Node, self).__init__(controller.poly, primary, address, name)
        self.controller = controller
        self.device = device
        self.device_id = device['id']
        self.lpfx = '%s:%s' % (address,name)
        controller.poly.subscribe(controller.poly.START,                  self.handler_start, address) 
        controller.poly.subscribe(controller.poly.POLL,                   self.handler_poll)

    def handler_start(self):
        self.setDriver('ST', 1)
        self.session = Session()
        try:
            self.scan_interval = timedelta(minutes=int(self.controller.Params['current_interval_minutes']))
        except:
            LOGGER.error("current_interval_minutes configuration parameter {} is not an integer? Using 1.".format(self.controller.Params['current_interval_minutes']))
            self.scan_interval = timedelta(minutes=int(1))
        LOGGER.info("Using scan interval: {}".format(self.scan_interval))
        self.flume = pyflume.FlumeData(
            self.controller.auth,
            self.device_id,
            self.device['location']['tz'],
            self.scan_interval,
            http_session=self.session,
        )
        self.update()

    def handler_poll(self, polltype):
        if polltype == 'longPoll':
            self.update()

    def update(self):
        try:
            st = self.flume.update()
            LOGGER.debug(f'Flume st={st}')
            self.set_st(1)
            LOGGER.debug("Values={}".format(self.flume.values))
        except (ConnectionResetError) as err:
            LOGGER.debug(f'Flume st={st}')
            LOGGER.error('ConnectionReset Error updating device, will try again later: %s', err)
            self.set_st(0)
        except (TimeoutError) as err:
            LOGGER.debug(f'Flume st={st}')
            LOGGER.error('Timeout Error updating device, will try again later: %s', err)
            self.set_st(0)
        except (Exception) as err:
            # PyFlume sends this when it has any issues...
            LOGGER.debug(f'Flume st={st}')
            LOGGER.error('Error updating device, will try again later: %s', err)
            msg = re.search('invalid_token',msg)
            if msg is None:
                LOGGER.error('Not an invalid token error, please let developer know about the previous error')
            else:
                LOGGER.error('It is an invalid_token error')
                self.controller.set_failed()
            self.set_st(0)
            LOGGER.debug("Values={}".format(self.flume.values))
            return
        self.setDriver('GV1',myfloat(self.flume.values['current_interval']))
        self.setDriver('GV2',myfloat(self.flume.values['last_60_min']))
        self.setDriver('GV3',myfloat(self.flume.values['last_24_hrs']))
        self.setDriver('GV4',myfloat(self.flume.values['today']))
        self.setDriver('GV5',myfloat(self.flume.values['last_30_days']))
        self.setDriver('GV6',myfloat(self.flume.values['week_to_date']))
        self.setDriver('GV7',myfloat(self.flume.values['month_to_date']))

    def query(self,command=None):
        self.update()
        self.reportDrivers()

    def set_st(self,value):
        if int(self.getDriver('ST')) != value:
            self.setDriver('ST',value) 

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    id = 'flume2'
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV1', 'value': 0, 'uom': 69}, # Current current_interval
        {'driver': 'GV2', 'value': 0, 'uom': 69}, # Last 60 Min last_60_min
        {'driver': 'GV3', 'value': 0, 'uom': 69}, # Last 24 Hours last_24_hrs
        {'driver': 'GV4', 'value': 0, 'uom': 69}, # Today today
        {'driver': 'GV5', 'value': 0, 'uom': 69}, # Last 30 Days last_30_days
        {'driver': 'GV6', 'value': 0, 'uom': 69}, # Week To Date week_to_date
        {'driver': 'GV7', 'value': 0, 'uom': 69}, # Month To Date month_to_date
    ]
    commands = {
         'QUERY': query,
    }
