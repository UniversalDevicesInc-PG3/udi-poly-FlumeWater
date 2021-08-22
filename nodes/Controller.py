

"""
Get the polyinterface objects we need.  Currently Polyglot Cloud uses
a different Python module which doesn't have the new LOG_HANDLER functionality
"""
from udi_interface import Node,LOGGER,Custom,LOG_HANDLER
import logging
from requests import Session
import pyflume
# My Nodes
from nodes import Flume1Node,Flume2Node
from node_funcs import id_to_address,get_valid_node_name,get_valid_node_address
KEY_DEVICE_TYPE = "type"
KEY_DEVICE_ID = "id"
TYPE_TO_NAME = {1: 'Hub', 2: 'Sensor'}

# IF you want a different log format than the current default
#LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')

class Controller(Node):
    def __init__(self, poly, primary, address, name):
        super(Controller, self).__init__(poly, primary, address, name)
        self.hb = 0
        self._mydrivers = {}
        self.Notices         = Custom(poly, 'notices')
        self.Data            = Custom(poly, 'customdata')
        self.Parameters      = Custom(poly, 'customparams')
        self.Notices         = Custom(poly, 'notices')
        self.TypedParameters = Custom(poly, 'customtypedparams')
        self.TypedData       = Custom(poly, 'customtypeddata')
        poly.subscribe(poly.START,                  self.handler_start, address) 
        poly.subscribe(poly.POLL,                   self.handler_poll)
        poly.subscribe(poly.CUSTOMPARAMS,           self.handler_custom_params)
        poly.subscribe(poly.LOGLEVEL,               self.handler_log_level)
        poly.ready()
        poly.addNode(self)

    def handler_start(self):
        #serverdata = self.poly._get_server_data()
        LOGGER.info(f"Started Airscape NodeServer {self.poly.serverdata['version']}")
        #LOGGER.debug('ST=%s',self.getDriver('ST'))
        self.Notices.clear()
        self.setDriver('ST', 1)
        self.setDriver('GV1', 0)
        self.heartbeat(0)
        #self.handler_custom_params()

    def handler_poll(self, polltype):
        if polltype == 'longPoll':
            self.heartbeat()

    def query(self,command=None):
        nodes = self.poly.getNodes()
        for node in nodes:
            self.nodes[node].reportDrivers()

    def delete(self):
        LOGGER.info('I\'m being deleted.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def heartbeat(self,init=False):
        LOGGER.debug('heartbeat: init={}'.format(init))
        if init is not False:
            self.hb = init
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def handler_log_level(self,level_name):
        LOGGER.info(f'level={level_name}')
        rh = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR}
        level=rh[level_name]
        if level < 10:
            LOGGER.info("Setting basic config to DEBUG...")
            LOG_HANDLER.set_basic_config(True,logging.DEBUG)
        else:
            LOGGER.info("Setting basic config to WARNING...")
            LOG_HANDLER.set_basic_config(True,logging.WARNING)

    def handler_custom_params(self,params):
        LOGGER.info(f'params={params}')
        self.Notices.clear()
        self.Parameters.load(params)

        default_username = "YourUserName"
        default_password = "YourPassword"
        default_client_id = "YourClientId"
        default_client_secret = "YourClientSecret"
        default_current_interval_minutes = 5
        add_param = False

        if self.Parameters['username'] is None:
            self.Parameters['username'] = default_username

        if self.Parameters['password'] is None:
            self.Parameters['password'] = default_password

        if self.Parameters['client_id'] is None:
            self.Parameters['client_id'] = default_client_id

        if self.Parameters['client_secret'] is None:
            self.Parameters['client_secret'] = default_client_secret

        if self.Parameters['current_interval_minutes'] is None:
            self.Parameters['current_interval_minutes'] = default_current_interval_minutes

        params_ok = True
        if self.Parameters['username'] == default_username:
            LOGGER.error(f"check_params: username not defined in customParams, please add it.  Using {self.Parameters['username']}")
            params_ok = False
        if self.Parameters['password'] == default_password:
            LOGGER.error(f"check_params: password not defined in customParams, please add it.  Using {self.Parameters['password']}")
            params_ok = False
        if self.Parameters['client_id'] == default_client_id:
            LOGGER.error(f"check_params: client_id not defined in customParams, please add it.  Using {self.Parameters['client_id']}")
            params_ok = False
        if self.Parameters['client_secret'] == default_client_secret:
            LOGGER.error(f"check_params: client_secret not defined in customParams, please add it.  Using {self.Parameters['client_secret']}")
            params_ok = False

        # Connect or send a message
        if params_ok:
            if self.connect():
                self.discover()            
            return True
        else:
            # This doesn't pass a key to test the old way.
            msg = 'Please set your information in configuration page'
            LOGGER.error(msg)
            self.Notices['config'] = msg
            return False

    def connect(self):
        self.session = Session()
        LOGGER.info("Connecting to Flume...")
        self.setDriver('GV1',1)
        try:
            self.auth = pyflume.FlumeAuth(
                self.Parameters['username'], self.Parameters['password'], self.Parameters['client_id'], self.Parameters['client_secret'], http_session=self.session
            )
            self.setDriver('GV1',2)
            LOGGER.info("Flume Auth={}".format(self.auth))
        except Exception as ex:
            self.setDriver('GV1',3)
            msg = 'Error from PyFlue: {}'.format(ex)
            LOGGER.error(msg)
            self.Notices['auth'] = msg
            return False
        except:
            self.setDriver('GV1',3)
            msg = 'Unknown Error from PyFlue: {}'.format(ex)
            LOGGER.error(msg)
            self.Notices['auth'] = msg
            LOGGER.error(msg,exc_info=True)
            return False
        self.flume_devices = pyflume.FlumeDeviceList(self.auth)
        devices = self.flume_devices.get_devices()
        LOGGER.info("Connecting complete...")
        return True

    def discover(self, *args, **kwargs):
        cst = int(self.getDriver('GV1'))
        if cst == 2:
            for device in self.flume_devices.device_list:
                if device[KEY_DEVICE_TYPE] <= 2:
                    ntype   = 'Flume{}Node'.format(device[KEY_DEVICE_TYPE])
                    address = id_to_address(device[KEY_DEVICE_ID])
                    name    = 'Flume {} {}'.format(TYPE_TO_NAME[device[KEY_DEVICE_TYPE]],device[KEY_DEVICE_ID])
                    # TODO: How to use ntype as the function to call?
                    if (device[KEY_DEVICE_TYPE] == 1):
                        self.poly.addNode(Flume1Node(self, self.address, address, name, device))
                    else:
                        self.poly.addNode(Flume2Node(self, self.address, address, name, device))
        else:
            if cst == 0:
                LOGGER.error("Can not discover, Connection has not started")
            elif cst == 1:
                LOGGER.error("Can not discover, Connection is started but not complete")
            elif cst == 3:
                LOGGER.error("Can not discover, Connection Failed")
            else:
                LOGGER.error("Can not discover, Unknown error")


    """
    """
    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
    }
    drivers = [
        {'driver': 'ST',  'value': 1, 'uom':  2},
        {'driver': 'GV1', 'value':  0, 'uom': 25}, # Authorization status
    ]
