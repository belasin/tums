#!/usr/bin/python
import sys
sys.path.append('.')
sys.path.append('/usr/lib/python2.5/site-packages')
sys.path.append('/usr/lib/python2.5')

# Import hack for freeze
import encodings
from encodings import ascii, utf_8, latin_1
a = u"a"
b = a.encode()

try:
    import Settings
    sys.path.append(Settings.BaseDir)
except:
    # The usual place 
    sys.path.append('/usr/local/tcs/tums')

# Nevow imports
from twisted.application import service, internet, strports, app
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import reactor

from Core import Utils, FlowCollector

application = service.Application('TUMSFC')

flowcollector = internet.UDPServer(9685, FlowCollector.flowCollector())
flowcollector.setServiceParent(application)

## TwistD bootstrap code
nodaemon = 0
log = '/var/log/tums-fc.log'
if len(sys.argv) > 1:
    if sys.argv[1] == "-n":
        nodaemon = 1
        log = None

if __name__ == '__main__':
    Utils.startTwisted(application, Settings.BaseDir, nodaemon, log, Settings.BaseDir, pidfile='/var/run/tums-fc.pid', appname="tumsfc")
