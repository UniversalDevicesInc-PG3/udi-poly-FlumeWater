#!/usr/bin/env python

from udi_interface import Interface,LOGGER
from nodes import VERSION, Controller
import sys

if __name__ == "__main__":
    try:
        polyglot = Interface([Controller])
        polyglot.start(VERSION)
        control = Controller(polyglot, 'controller', 'controller', 'FlumeWater')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0) 