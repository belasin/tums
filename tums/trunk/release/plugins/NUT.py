import config, os, urllib2
from Core import Utils

class Plugin(object):
    """ Configures NUT. """
    parameterHook = "--nut"
    parameterDescription = "Reconfigure NUT"
    parameterArgs = ""
    autoRun = True
    configFiles = [
        "/etc/nut/upsd.conf",
        "/etc/nut/upsd.users",
        "/etc/nut/ups.conf",
        "/etc/nut/upsmon.conf"
    ]

    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        n = open('/etc/nut/upsd.conf', 'wt')
        n.write("""ACL all 0.0.0.0/0
ACL localhost 127.0.0.0/16
ACCEPT localhost
REJECT all\n""")
        n.close()

        n = open("/etc/nut/ups.conf", 'wt')

        for name,conf in config.General.get('ups', {}).items():
            n.write('[%s]\n' % name)

            for k,v in conf.items():
                if " " in v:
                    val = repr(v).replace("'", '"')
                else:
                    val = v

                n.write('   %s = %s\n' % (k, val) )
            
            n.write('\n')

        n = open('/etc/nut/upsd.users', 'wt') 

        n.write("""[admin]
    password = admin
    allowfrom = localhost THUSA
    actions = set
    instcmds = all

[monmaster]
    password = monmaster
    allowfrom = localhost
    upsmon master\n""")
        n.close()

        n = open('/etc/nut/upsmon.conf', 'wt')

        mons = ""
        for name in config.General.get('ups', []):
            mons += "MONITOR %s@localhost 1 monmaster monmaster master\n" % name
        
        n.write("""DEADTIME 30
FINALDELAY 20
HOSTSYNC 240
%s
NOCOMMWARNTIME 30
NOTIFYMSG ONLINE "Power has returned(OL)"
NOTIFYMSG ONBATT "On Battery(OB)"
NOTIFYMSG LOWBAT "LOW Battery. Sending shutdowns to Slaves"
NOTIFYMSG FSD    "UPS is being shutdown"
NOTIFYMSG SHUTDOWN "System is shutting down"
NOTIFYFLAG ONBATT SYSLOG+WALL+EXEC
NOTIFYFLAG ONLINE SYSLOG+WALL+EXEC
NOTIFYFLAG FSD    SYSLOG+WALL+EXEC
NOTIFYFLAG LOWBAT SYSLOG+WALL+EXEC
NOTIFYFLAG SHUTDOWN SYSLOG+WALL+EXEC
POWERDOWNFLAG /etc/killpower
SHUTDOWNCMD "/sbin/shutdown -h +0"\n""" % mons)

        n.close()

        n = open('/etc/default/nut', 'wt')
        n.write("""# start upsd
START_UPSD=yes

# set upsd specific options. use "man upsd" for more info
UPSD_OPTIONS=""

# start upsmon
START_UPSMON=yes

# set upsmon specific options. use "man upsmon" for more info
UPSMON_OPTIONS=""

#POWEROFF_WAIT=15m\n""")
        n.close()

