import config, os
from Core import Utils

class Plugin(object):
    """ Configures everything needed for Debian L2TP. """
    parameterHook = "--l2tp"
    parameterDescription = "Reconfigure L2TP on Debian"
    parameterArgs = ""
    autoRun = True
    required = "debian"
    configFiles = [ 
        "/etc/l2tpns/startup-config",
        "/etc/l2tpns/ip_pool",
    ]

    def reloadServices(self):
        os.system('/etc/init.d/l2tpns restart')

    def writeConfig(self, *a):
        ippool = "10.10.10.0/24\n"

        l = open('/etc/l2tpns/ip_pool', 'wt')
        l.write(ippool)
        l.close()

        sysconf = """# Debugging level
set debug 2

# Log file: comment out to use stderr, use "syslog:facility" for syslog
set log_file "/var/log/l2tpns"

# Write pid to this file
set pid_file "/var/run/l2tpns.pid"

# Shared secret with LAC
set l2tp_secret "secret"

# MTU of interface for L2TP traffic
set l2tp_mtu 1350

# Only 2 DNS server entries are allowed
set primary_dns 10.10.10.1
#set secondary_dns 172.31.0.1

set primary_radius 127.0.0.1
set primary_radius_port 1812
set radius_secret "2saraddb"

# Acceptable authentication types (pap, chap) in order of preference
set radius_authtypes "pap"

# Write usage accounting files into specified directory
set accounting_dir "/var/run/l2tpns/acct"

# Listen address for L2TP
#set bind_address 1.1.1.1

# Gateway address given to clients
set peer_address 10.10.10.1

# Drop/kill sessions
load plugin "sessionctl"

# Throttle/snoop based on RADIUS
load plugin "autothrottle"
#load plugin "autosnoop"

# Control throttle/snoop with nsctl
load plugin "throttlectl"
load plugin "snoopctl"

"""

        l = open('/etc/l2tpns/startup-config', 'wt')
        l.write(sysconf)
        l.close()
