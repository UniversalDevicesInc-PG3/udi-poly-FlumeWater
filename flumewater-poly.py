#!/usr/bin/env python

from udi_interface import Interface,LOGGER
from nodes import Controller

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('Flume Water Controller')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Received interrupt or exit...")
        polyglot.stop()
    except Exception as err:
        LOGGER.error('Excption: {0}'.format(err), exc_info=True)
    sys.exit(0)
