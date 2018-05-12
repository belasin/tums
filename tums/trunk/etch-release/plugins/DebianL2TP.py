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
        
        ippool = config.General.get('l2tp_pool', '10.10.10.0')
        
        tunip = '.'.join(ippool.split('.')[:3] + ['1'])

        l = open('/etc/l2tpns/ip_pool', 'wt')
        l.write(ippool+'/24\n')
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
set primary_dns %(tunip)s
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
set peer_address %(tunip)s

# Drop/kill sessions
load plugin "sessionctl"

# Throttle/snoop based on RADIUS
load plugin "autothrottle"
#load plugin "autosnoop"

# Control throttle/snoop with nsctl
load plugin "throttlectl"
load plugin "snoopctl"

""" % {'tunip': tunip}

        l = open('/etc/l2tpns/startup-config', 'wt')
        l.write(sysconf)
        l.close()

        initscript = """
#! /bin/sh
#
# l2tpns        Based on skeleton example file.
#
#               Written by Miquel van Smoorenburg <miquels@cistron.nl>.
#               Modified for Debian GNU/Linux
#               by Ian Murdock <imurdock@gnu.ai.mit.edu>.
#

PATH=/sbin:/bin:/usr/sbin:/usr/bin
DAEMON=/usr/sbin/l2tpns
NAME=l2tpns
DESC=l2tpns
ARGS="-d"

test -f $DAEMON || exit 0

set -e

case "$1" in
  start)
        echo -n "Starting $DESC: "
        start-stop-daemon --start --quiet --pidfile /var/run/$NAME.pid \
                --exec $DAEMON -- $ARGS
        sleep 5
        ifconfig tun0 %(tunip)s netmask 255.255.255.0
        echo "$NAME."
        ;;
  stop)
        echo -n "Stopping $DESC: "
        start-stop-daemon --oknodo --stop --signal 3 --quiet \
                --pidfile /var/run/$NAME.pid --exec $DAEMON -- $ARGS
        echo "$NAME."
        ;;
  reload)
        #
        #       If the daemon can reload its config files on the fly
        #       for example by sending it SIGHUP, do it here.
        #
        #       If the daemon responds to changes in its config file
        #       directly anyway, make this a do-nothing entry.
        #
        echo "Reloading $DESC configuration files."
        start-stop-daemon --stop --signal 1 --quiet --pidfile \
                /var/run/$NAME.pid --exec $DAEMON -- $ARGS
        sleep 2
        ifconfig tun0 %(tunip)s netmask 255.255.255.0
        ;;
  restart|force-reload)
        #
        #       If the "reload" option is implemented, move the "force-reload"
        #       option to the "reload" entry above. If not, "force-reload" is
        #       just the same as "restart".
        #
        echo -n "Restarting $DESC: "
        start-stop-daemon --stop --quiet --pidfile \
                /var/run/$NAME.pid --exec $DAEMON -- $ARGS
        sleep 5
        start-stop-daemon --start --quiet --pidfile \
                /var/run/$NAME.pid --exec $DAEMON -- $ARGS
        sleep 5
        ifconfig tun0 %(tunip)s netmask 255.255.255.0
        echo "$NAME."
        ;;
  *)
        N=/etc/init.d/$NAME
        # echo "Usage: $N {start|stop|restart|reload|force-reload}" >&2
        echo "Usage: $N {start|stop|restart|force-reload}" >&2
        exit 1
        ;;
esac

exit 0
""" % {'tunip': tunip}
        l = open('/etc/init.d/l2tpns', 'wt')
        l.write(initscript)
        l.close()
