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
        self.configFiles = ["/etc/ddclient.conf"]
    
    def reloadServices(self):
        os.system('/etc/init.d/ddclient restart')

    def writeConfig(self, *a):
        # ddclient
        iface = config.WANPrimary
        ddclient = """daemon=300
mail-failure=root
syslog=yes
pid=/var/run/ddclient.pid
use=if, if=%s\n""" % (iface)
        if config.ThusaDNSUsername:
            ddclient+="""protocol=dyndns2
server=update.thusadns.com
login=%s
password=%s
%s\n""" % (config.ThusaDNSUsername, config.ThusaDNSPassword, config.ThusaDNSAddress)

        for entry in config.General.get('dyndns', []):
            protocol = entry[0].replace('thusadns', 'dyndns2')
            ddclient += """\nprotocol=%s
server=%s
login=%s
password=%s
%s\n"""     % (
                protocol, 
                entry[1], 
                entry[3], 
                entry[4], 
                entry[2]
            )
        Utils.writeConf('/etc/ddclient.conf', ddclient, '#')
