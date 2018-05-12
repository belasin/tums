# Root cause analysis

from rcamodules import exim, dns

import time

modules = (exim, dns)

class Logger(object):
    def __init__(self):
        self.fi = open('/var/log/tums-rca.log', 'wt')
        self.items = []

    def log(self, message):
        dtime = time.ctime()
        tmsg = "%s - %s" % (dtime, message)
        self.fi.write(tmsg + '\n')
        self.items.append((dtime, message))

def runRCAs(logger):
    # Clear the items at each cycle...
    logger.items = []
    for i in modules:
        

