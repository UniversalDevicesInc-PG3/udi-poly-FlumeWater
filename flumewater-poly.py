#!/usr/bin/env python

from udi_interface import Interface,LOGGER
from nodes import Controller
import sys

if __name__ == "__main__":
    try:
        polyglot = Interface([Controller])
        polyglot.start()
        control = Controller(polyglot, 'controller', 'controller', 'Airscape')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)