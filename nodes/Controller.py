

"""
Get the polyinterface objects we need.  Currently Polyglot Cloud uses
a different Python module which doesn't have the new LOG_HANDLER functionality
"""
from udi_interface import Node,LOGGER,Custom,LOG_HANDLER
import logging,os,markdown2
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
        self.Params          = Custom(poly, 'customparams')
        self.Notices         = Custom(poly, 'notices')
        self.TypedParameters = Custom(poly, 'customtypedparams')
        self.TypedData       = Custom(poly, 'customtypeddata')
        poly.subscribe(poly.START,                  self.handler_start, address) 
        poly.subscribe(poly.POLL,                   self.handler_poll)
        poly.subscribe(poly.CUSTOMPARAMS,           self.handler_custom_params)
        poly.subscribe(poly.LOGLEVEL,               self.handler_log_level)
        poly.subscribe(poly.CONFIGDONE,             self.handler_config_done)
        poly.subscribe(poly.ADDNODEDONE,            self.handler_add_node_done)
        self.Notices.clear()
        self.handler_custom_params_st = None
        self.handler_add_node_done_st = False
        self.connect_st = 0
        poly.ready()
        self.poly.addNode(self, conn_status='ST')

    def handler_start(self):
        #serverdata = self.poly._get_server_data()
        LOGGER.info(f"Started FlumeWater NodeServer {self.poly.serverdata['version']}")
        # Force for now since PG3 is not doing it?
        self.poly.updateProfile()
        #LOGGER.debug('ST=%s',self.getDriver('ST'))
        self.setDriver('ST', 1)
        configurationHelp = './configdoc.md';
        if os.path.isfile(configurationHelp):
	        cfgdoc = markdown2.markdown_path(configurationHelp)
	        self.poly.setCustomParamsDoc(cfgdoc)
        else:
            LOGGER.error(f'config doc not found? {configurationHelp}')
        self.heartbeat(0)
        #self.handler_custom_params()

    def handler_add_node_done(self,data):
        LOGGER.debug(f'enter: {data}')
        if (data['address'] == self.address):
            self.handler_add_node_done_st = True
            # Connect and discover if all good
            if self.connect():
                self.discover()

    def handler_config_done(self):
        LOGGER.debug(f'enter')
        self.poly.addLogLevel('DEBUG_MODULES',9,'Debug + Modules')
        LOGGER.debug(f'exit')

    def handler_poll(self, polltype):
        if polltype == 'longPoll':
            self.heartbeat()
        self.check_config_st()
        if self.connect_st == 3:
            LOGGER.error("Authorization previously failed, will try to reconnect now")
            self.reconnect()

    def query(self,command=None):
         self.reportDrivers()

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

    def handler_log_level(self,level):
        LOGGER.info(f'level={level}')
        if level['level'] < 10:
            LOGGER.info("Setting basic config to DEBUG...")
            LOG_HANDLER.set_basic_config(True,logging.DEBUG)
        else:
            LOGGER.info("Setting basic config to WARNING...")
            LOG_HANDLER.set_basic_config(True,logging.WARNING)

    def handler_custom_params(self,data):
        LOGGER.debug("Enter data={}".format(data))
        # Our defaults, make sure the exist in case user deletes one
        params = {
            'username': 'YourUserName',
            'password': "YourPassword",
            'client_id': 'YourClientId',
            'client_secret': 'YourClientSecret',
            'current_interval_minutes': 5
        }
        if data is None:
            # Add one.
            self.Params['username'] = params['username']
        # Load what we have
        self.Params.load(data)

        # Assume we are good unless something bad is found
        st = True

        # Make sure all the params exist.
        for param in params:
            if not param in data:
                LOGGER.error(f'Add back missing param {param}')
                self.Params[param] = params[param]
                # Can't do anything else because we will be called again due to param change
                return

        # Make sure they all have a value that is not the default
        for param in params:
            if data[param] == "" or (data[param] == params[param] and param != "current_interval_minutes"):
                msg = f'Please define {param}'
                LOGGER.error(msg)
                self.Notices[param] = msg
                st = False
            else:
                self.Notices.delete(param)

        self.handler_custom_params_st = st

        # If add node is done, then our values were edited, so do discover
        if st:
            # Connect and discover if all good
            if self.connect():
                self.discover()

        LOGGER.debug(f'exit: {self.handler_custom_params_st}')

    def set_connect_st(self,value):
        LOGGER.debug(f'{value}')
        self.connect_st = value
        self.setDriver('GV1',value)

    # Force due to race condition on startup
    def check_config_st(self):
        try:
            if int(self.getDriver('GV1')) != self.connect_st:
                self.set_connect_st(self.connect_st)
        except:
            LOGGER.error("Weird driver value? Will force to zero",exc_info=True)
            self.set_connect_st(0)

    def connect(self):
        if self.handler_custom_params_st is not True:
            LOGGER.error(f"Can not connect to Flume until configuration errors are fixed st={self.handler_custom_params_st}")
            return False
        self.session = Session()
        LOGGER.info("Connecting to Flume...")
        self.set_connect_st(1)
        try:
            self.auth = pyflume.FlumeAuth(
                self.Params['username'], self.Params['password'], self.Params['client_id'], self.Params['client_secret'], http_session=self.session
            )
            self.set_connect_st(2)
            LOGGER.info("Flume Auth={}".format(self.auth))
        except Exception as ex:
            self.set_connect_st(3)
            msg = 'Error from PyFlume: {}'.format(ex)
            LOGGER.error(msg)
            self.Notices['auth'] = msg
            return False
        except:
            self.set_connect_st(3)
            msg = 'Unknown Error from PyFlume'
            LOGGER.error(msg)
            self.Notices['auth'] = msg
            LOGGER.error(msg,exc_info=True)
            return False
        self.flume_devices = pyflume.FlumeDeviceList(self.auth)
        devices = self.flume_devices.get_devices()
        LOGGER.info("Connecting complete...")
        return True

    def reconnect(self, *args, **kwargs):
        LOGGER.warning("Closing and reconnecting PyFlume connection...")
        self.session.close()
        return self.connect()
        
    def set_failed(self, *args, **kwargs):
        LOGGER.error("Setting Authorization to Failed, will retry on next poll")
        self.set_connect_st(3)

    def discover(self, *args, **kwargs):
        cst = self.connect_st
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
        'SETFAILED': set_failed,
    }
    drivers = [
        {'driver': 'ST',  'value': 1, 'uom':  25},
        {'driver': 'GV1', 'value':  0, 'uom': 25}, # Authorization status
    ]
