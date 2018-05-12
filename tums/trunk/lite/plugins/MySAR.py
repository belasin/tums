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
        os.system('cd packages; tar -jxf mysar.tar.bz2; mv mysar /usr/local/')
        if os.path.exists('/etc/debian_version'):
            os.system('mysqladmin create mysar')
            os.system('mysql mysar < /usr/local/mysar/mysar.sql')
        else:
            os.system('mysqladmin create mysar --password="rossi"')
        os.system('cd /usr/local/tcs/tums/')

