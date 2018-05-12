import os, config
from Core import Utils, confparse
import socket, struct

class Plugin(object):
    parameterHook = "--upgrade"
    parameterDescription = "Runs upgrade scripts to get vulani configs and alterations"
    parameterArgs = ""
    autoRun = True
    configFiles = []

    installedVersion = None

    currentUpdates = ["17425"]

    def __init__(self):
        self.sysconf = confparse.Config()

    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        ver = self.sysconf.Upgrade.get("CurrentVersion",self.installedVersion)
        Upgrade = self.sysconf.Upgrade
        if ver not in self.currentUpdates:
            startRunning = True
        else:
            startRunning = False
        for nVer in self.currentUpdates:
            if ver == nVer:
                startRunning=True
                continue
            if startRunning:
                Upgrade["CurrentVersion"] = nVer
                os.system("chmod a+x /usr/local/tcs/tums/packages/UpgradeScr/"+nVer+"/upgrade.sh")
                os.system("/usr/local/tcs/tums/packages/UpgradeScr/"+nVer+"/upgrade.sh")
        self.sysconf.Upgrade = Upgrade
