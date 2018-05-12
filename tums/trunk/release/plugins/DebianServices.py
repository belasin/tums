import config, os
from Core import Utils

class Plugin(object):
    """ Configures everything needed for Debian APT. """
    parameterHook = "--services"
    parameterDescription = "Reconfigure APT on Debian"
    parameterArgs = ""
    autoRun = True
    required = "debian"
    configFiles = []

    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        if config.General.get('services', None):
            for service, status in config.General['services'].items():
                if status:
                    os.system('update-rc.d %s defaults' % service)
                else:
                    os.system('update-rc.d -f %s remove' % service)
        
        if config.ThusaDNSUsername or config.General.get('dyndns', []):
            os.system('update-rc.d ddclient defaults >/dev/null 2>&1')
        else:
            os.system('update-rc.d -f ddclient remove >/dev/null 2>&1')
