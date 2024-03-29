import config, os
from Core import Utils

class Plugin(object):
    parameterHook = "--ntp"
    parameterDescription = "Reconfigure OpenNTP"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/openntpd/ntpd.conf"
    ]

    def reloadServices(self):
        os.system('/etc/init.d/openntpd restart')
        os.system('update-rc.d openntpd defaults')
    
    def writeConfig(self, *a):

        ntpdconf = """#NTPD Config generated by TUMS Configurator
listen on *
server 0.debian.pool.ntp.org
server 1.debian.pool.ntp.org
server 2.debian.pool.ntp.org
server 3.debian.pool.ntp.org
        """
        # Check for debianism (goes in /etc/dhcp3)
        f = open('/etc/openntpd/ntpd.conf', 'wt')
        f.write(ntpdconf)
        f.close()
