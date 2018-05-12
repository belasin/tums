import config, os
from Core import Utils

class Plugin(object):
    """ Configures Debian mail system permissions. """
    parameterHook = "--debmail"
    parameterDescription = "Reconfigure mailpermissions"
    parameterArgs = ""
    autoRun = True
    required = "debian"
    configFiles = [ 
    ]

    def reloadServices(self):
        os.system('/etc/init.d/clamav-daemon restart')

    def writeFile(self, file, content):
        f = open(file,'wt')
        f.write(content)
        f.close()

    def writeConfig(self, *a):
        os.system('chown -R Debian-exim:Debian-exim /var/run/clamav')
        os.system('chown -R Debian-exim:Debian-exim /var/log/clamav')
        os.system('chown -R Debian-exim:Debian-exim /var/lib/clamav')
        # Fix vacation...
        os.system('mkdir -p /var/spool/mail/vacation/ >/dev/null 2>&1')
        os.system('chown www-data:root /var/spool/mail/vacation; chmod a+r /var/spool/mail/vacation')
