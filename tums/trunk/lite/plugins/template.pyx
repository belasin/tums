# 
# Template for Configurator plugin
#
import config, os

class Plugin(object):
    parameterHook = "--blah"                    # Name the configurator parameter 
                                                #   for explicitly calling this plugin

    parameterDescription = "Reconfigure blah"   # Describe what this plugin is for

    parameterArgs = ""                          # Describe what arguments this 
                                                #   plugin requres

    autoRun = False                             # Should this plugin be run with a Boxprep?
    configFiles = [ 
        "/etc/...",                             # List of config files this plugin effects
    ]

    def reloadServices(self):
        os.system('/etc/init.d/myservice reload')
        return 

    def writeConfig(self, *a):
        #do stuff here
        return

