import config, os
from Core import Utils


class Plugin(object):
    parameterHook = "--ddclient"
    parameterDescription = "Reconfigure ddclient"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/ddclient/ddclient.conf",
    ]

    def __init__(self):
        if os.path.exists('/etc/debian_version'):
            self.configFiles = ["/etc/ddclient.conf"]
    
    def reloadServices(self):
        os.system('/etc/init.d/ddclient restart')

    def writeConfig(self, *a):
        # ddclient
        iface = config.WANPrimary
        ddclient = """daemon=300
syslog=yes
pid=/var/run/ddclient.pid
server=update.thusadns.com
use=if, if=%s
protocol=dyndns2
login=%s
password=%s
%s
""" % (iface, config.ThusaDNSUsername, config.ThusaDNSPassword, config.ThusaDNSAddress)
        if os.path.exists('/etc/debian_version'): # some form of Debian
            Utils.writeConf('/etc/ddclient.conf', ddclient, '#')
        else:
            Utils.writeConf('/etc/ddclient/ddclient.conf', ddclient, '#')


