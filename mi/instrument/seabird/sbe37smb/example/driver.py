#!/usr/bin/env python

"""
@package mi.instrument.seabird.sbe37smb.example.driver
@file /Users/wfrench/Workspace/code/marine-integrations/mi/instrument/seabird/sbe37smb/example/driver.py
@author Bill French
@brief Driver for the example
Release notes:

test driver
"""

__author__ = 'Bill French'
__license__ = 'Apache 2.0'


import logging
import time
import re
import datetime

from mi.core.common import BaseEnum
from mi.core.instrument.instrument_driver import DriverParameter

from mi.core.instrument.instrument_protocol import CommandResponseInstrumentProtocol
from mi.core.instrument.instrument_driver import InstrumentDriver

#from mi.instrument_connection import SerialInstrumentConnection
#from mi.instrument_protocol import CommandResponseInstrumentProtocol
#from mi.instrument_driver import InstrumentDriver
#from mi.instrument_driver import DriverChannel
#from mi.instrument_driver import DriverCommand
#from mi.instrument_driver import DriverState
#from mi.instrument_driver import DriverEvent
#from mi.instrument_driver import DriverParameter
#from mi.exceptions import InstrumentProtocolException
#from mi.exceptions import InstrumentTimeoutException
#from mi.exceptions import InstrumentStateException
#from mi.exceptions import InstrumentConnectionException
#from mi.common import InstErrorCode
#from mi.common import BaseEnum
#from mi.instrument_fsm import InstrumentFSM

###
#   Module wide values
###
log = logging.getLogger('mi_logger')
INSTRUMENT_NEWLINE = '\n'

PACKET_CONFIG = {
        'ctd_parsed' : ('prototype.sci_data.stream_defs', 'ctd_stream_packet'),
        'ctd_raw' : None
}

###
#   Static Enumerations
###
class State(BaseEnum):
    """
    Enumerated driver states.  Your driver will likly only support a subset of these.
    """
    #UNCONFIGURED = DriverState.UNCONFIGURED
    #DISCONNECTED =  DriverState.DISCONNECTED
    #CONNECTING =  DriverState.CONNECTING
    #DISCONNECTING =  DriverState.DISCONNECTING
    #CONNECTED =  DriverState.CONNECTED
    #ACQUIRE_SAMPLE =  DriverState.ACQUIRE_SAMPLE
    #UPDATE_PARAMS =  DriverState.UPDATE_PARAMS
    #SET =  DriverState.SET
    #AUTOSAMPLE =  DriverState.AUTOSAMPLE
    #TEST =  DriverState.TEST
    #CALIBRATE =  DriverState.CALIBRATE
    #DETACHED =  DriverState.DETACHED
    #COMMAND =  DriverState.COMMAND

class Event(BaseEnum):
    """
    Enumerated driver events.  Your driver will likly only support a subset of these.
    """
    #CONFIGURE = DriverEvent.CONFIGURE
    #INITIALIZE = DriverEvent.INITIALIZE
    #CONNECT = DriverEvent.CONNECT
    #CONNECTION_COMPLETE = DriverEvent.CONNECTION_COMPLETE
    #CONNECTION_FAILED = DriverEvent.CONNECTION_FAILED
    #CONNECTION_LOST = DriverEvent.CONNECTION_LOST
    #DISCONNECT = DriverEvent.DISCONNECT
    #DISCONNECT_COMPLETE = DriverEvent.DISCONNECT_COMPLETE
    #DISCONNECT_FAILED = DriverEvent.DISCONNECT_FAILED
    #PROMPTED = DriverEvent.PROMPTED
    #DATA_RECEIVED = DriverEvent.DATA_RECEIVED
    #COMMAND_RECEIVED = DriverEvent.COMMAND_RECEIVED
    #RESPONSE_TIMEOUT = DriverEvent.RESPONSE_TIMEOUT
    #SET = DriverEvent.SET
    #GET = DriverEvent.GET
    #EXECUTE = DriverEvent.EXECUTE
    #ACQUIRE_SAMPLE = DriverEvent.ACQUIRE_SAMPLE
    #START_AUTOSAMPLE = DriverEvent.START_AUTOSAMPLE
    #STOP_AUTOSAMPLE = DriverEvent.STOP_AUTOSAMPLE
    #TEST = DriverEvent.TEST
    #STOP_TEST = DriverEvent.STOP_TEST
    #CALIBRATE = DriverEvent.CALIBRATE
    #RESET = DriverEvent.RESET
    #ENTER = DriverEvent.ENTER
    #EXIT = DriverEvent.EXIT
    #ATTACH = DriverEvent.ATTACH
    #DETACH = DriverEvent.DETACH
    #UPDATE_PARAMS = DriverEvent.UPDATE_PARAMS

class Channel(BaseEnum):
    """
    Enumerated driver channels.  Your driver will likly only support a subset of these.
    """
    #CTD = DriverChannel.CTD
    #ALL = DriverChannel.ALL

#class Command(DriverCommand):
#    pass

class Prompt(BaseEnum):
    pass

class Parameter(DriverParameter):
    pass

class MetadataParameter(BaseEnum):
    pass

class Error(BaseEnum):
    pass

class Capability(BaseEnum):
    pass

class Status(BaseEnum):
    pass

class exampleParameter():
    """
    """

###
#   Protocol for example
###
class exampleInstrumentProtocol(CommandResponseInstrumentProtocol):
    """
    The protocol is a very simple command/response protocol with a few show
    commands and a few set commands.
    """
    
    def __init__(self, callback=None, prompt=Prompt(), newline=INSTRUMENT_NEWLINE):
        """
        """
        #CommandResponseInstrumentProtocol.__init__(self, callback, prompt, newline)
        
        #self._fsm = InstrumentFSM(State, Event, Event.ENTER,
        #                          Event.EXIT,
        #                          InstErrorCode.UNHANDLED_EVENT)

###
#   Driver for example
###
class exampleInstrumentDriver(InstrumentDriver):
    """
    """
    def __init__(self, evt_callback):
        InstrumentDriver.__init__(self, evt_callback)
        self.protocol = exampleInstrumentProtocol(evt_callback)
    
    def driver_echo(self, msg):
        """
        @brief Sample driver command. 
        """
        echo = 'driver_echo: %s' % msg
        return echo





