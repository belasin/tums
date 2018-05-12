import config, os
from Core import Utils
import socket, struct

class Plugin(object):
    parameterHook = "--mysar"
    parameterDescription = "Configure MySAR Squid reporting"
    parameterArgs = ""
    autoRun = True
    configFiles = []

    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        os.system('cd packages; tar -jxf mysar.tar.bz2; mv mysar /usr/local/ > /dev/null 2>&1')
        os.system('mysqladmin create mysar > /dev/null 2>&1')
        os.system('mysql mysar < /usr/local/mysar/mysar.sql > /dev/null 2>&1')
        os.system('cd /usr/local/tcs/tums/')

