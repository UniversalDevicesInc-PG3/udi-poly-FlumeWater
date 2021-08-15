

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
    """
    The Controller Class is the primary node from an ISY perspective. It is a Superclass
    of polyinterface.Node so all methods from polyinterface.Node are available to this
    class as well.
    """
    def __init__(self, poly, primary, address, name):
        super(Controller, self).__init__(polyglot)
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
        poly.subscribe(poly.ADDNODEDONE,            self.handler_add_node_done)
        poly.subscribe(poly.CUSTOMPARAMS,           self.handler_custom_params)
        poly.subscribe(poly.LOGLEVEL,               self.handler_log_level)
        poly.ready()
        poly.addNode(self)

    def handler_start(self):
        #serverdata = self.poly._get_server_data()
        LOGGER.info(f"Started Airscape NodeServer {self.poly.serverdata['version']}")
        #LOGGER.debug('ST=%s',self.getDriver('ST'))
        self.setDriver('ST', 1)
        self.setDriver('GV2', 0)
        self.heartbeat(0)
        self.params_ok = self.check_params()
        #self.set_debug_level(self.getDriver('GV1'))
        if self.params_ok:
            if self.connect():
                self.discover()

    def handler_poll(self, polltype):
        if polltype == 'longPoll':
            self.heartbeat()

    def query(self,command=None):
        self.check_params()
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

    def handler_custom_params(self):
        self.Notices.clear()

        default_username = "YourUserName"
        default_password = "YourPassword"
        default_client_id = "YourClientId"
        default_client_secret = "YourClientSecret"
        default_current_interval_minutes = 5
        add_param = False

        if self.Parameters['username'] is None:
            self.Parameters['username'] = default_username
            LOGGER.error('check_params: username not defined in customParams, please add it.  Using {}'.format(self.username))
            add_param = True

        if self.Parameters['password'] is None:
            self.Parameters['password'] = default_password
            LOGGER.error('check_params: password not defined in customParams, please add it.  Using {}'.format(self.password))
            add_param = True

        if self.Parameters['client_id'] is None:
            self.Parameters['client_id'] = default_client_id
            LOGGER.error('check_params: client_id not defined in customParams, please add it.  Using {}'.format(self.client_id))
            add_param = True

        if self.Parameters['client_secret'] is None:
            self.Parameters['client_secret'] = default_client_secret
            LOGGER.error('check_params: client_secret not defined in customParams, please add it.  Using {}'.format(self.client_secret))
            add_param = True

        if self.Parameters['current_interval_minutes'] is None:
            self.Parameters['current_interval_minutes'] = default_current_interval_minutes
            add_param = True

        self.username = self.Parameters['username']
        self.password = self.Parameters['password']
        self.client_id = self.Parameters['client_id']
        self.client_secret = self.Parameters['client_secret']
        self.current_interval_minutes = self.Parameters['current_interval_minutes']

        # Add a notice if they need to change the username/password from the default.
        if self.username == default_username or self.password == default_password or self.client_id == default_client_id or self.client_secret == default_client_secret:
            # This doesn't pass a key to test the old way.
            msg = 'Please set your information in configuration page, and restart this nodeserver'
            LOGGER.error(msg)
            self.Notices['config'] = msg
            return False
        else:
            return True

    def connect(self):
        self.session = Session()
        LOGGER.info("Connecting to Flume...")
        self.setDriver('GV2',1)
        try:
            self.auth = pyflume.FlumeAuth(
                self.username, self.password, self.client_id, self.client_secret, http_session=self.session
            )
            self.setDriver('GV2',2)
            LOGGER.info("Flume Auth={}".format(self.auth))
        except Exception as ex:
            self.setDriver('GV2',3)
            msg = 'Error from PyFlue: {}'.format(ex)
            LOGGER.error(msg)
            self.Notices['auth'] = msg
            return False
        except:
            self.setDriver('GV2',3)
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
        cst = int(self.getDriver('GV2'))
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
