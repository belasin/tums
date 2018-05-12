import config, os
from Core import Utils
import xmlrpclib, sha, time

class Plugin(object):
    parameterHook = "--tums"
    parameterDescription = "Reconfigure TUMS"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/usr/local/tcs/tums/Settings.py",
    ]

    def reloadServices(self):
        os.system('/etc/init.d/tums stop; /etc/init.d/tums start')


    def writeConfig(self, *a):
    
        initd = """#!/sbin/runscript
# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

start() {
    ebegin "Starting Tums"
    export PYTHONPATH='/usr/local/tcs/tums'
    start-stop-daemon --start --pidfile /var/run/tums.pid --exec /usr/local/tcs/tums/tums
    start-stop-daemon --start --pidfile /var/run/tums-fc.pid --exec /usr/local/tcs/tums/tums-fc
    /usr/local/tcs/exilog-tums/exilog_agent.pl > /dev/null 2>&1
    /usr/sbin/fprobe -i %s -p -f ip 127.0.0.1:9685
    eend 0
}

stop() {
    ebegin "Stopping Tums"
    start-stop-daemon --stop --pidfile /var/run/tums.pid > /dev/null 2>&1
    start-stop-daemon --stop --pidfile /var/run/tums-fc.pid > /dev/null 2>&1
    killall -r exilog > /dev/null 2>&1
    killall fprobe
    eend 0
}

restart() {
    start-stop-daemon --stop --pidfile /var/run/tums.pid > /dev/null 2>&1
    start-stop-daemon --stop --pidfile /var/run/tums-fc.pid > /dev/null 2>&1
    sleep 2
    export PYTHONPATH='/usr/local/tcs/tums'
    killall -r exilog > /dev/null 2>&1
    killall fprobe
    /usr/local/tcs/exilog-tums/exilog_agent.pl > /dev/null 2>&1
    start-stop-daemon --start --pidfile /var/run/tums.pid --exec /usr/local/tcs/tums/tums
    start-stop-daemon --start --pidfile /var/run/tums-fc.pid --exec /usr/local/tcs/tums/tums-fc
    /usr/sbin/fprobe -i %s -p -f ip 127.0.0.1:9685
    eend 0
}\n""" % (config.LANPrimary, config.LANPrimary)
        host = config.ExternalName
        user = ''.join(host.split('.'))

        debianinitd = """#!/bin/sh -e 
#### BEGIN INIT INFO
# Provides:          tums
# Required-Start:    $syslog $time $local_fs $remote_fs
# Required-Stop:     $syslog $time $local_fs $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      S 0 1 6
# Short-Description: User management system
# Description:       Debian init script for TUMS providing administrative features to TCS.
### END INIT INFO
#
# Author:       Colin Alston <colin@thusa.co.za>
#

. /lib/lsb/init-functions

case "$1" in
    start)
        log_daemon_msg "Starting Tums" "tums"
        export PYTHONPATH='/usr/local/tcs/tums'
        start-stop-daemon --start --pidfile /var/run/tums.pid --exec /usr/local/tcs/tums/tums
        start-stop-daemon --start --pidfile /var/run/tums-fc.pid --exec /usr/local/tcs/tums/tums-fc
        /usr/local/tcs/exilog-tums/exilog_agent.pl > /dev/null 2>&1
        /usr/sbin/fprobe -i %s -p -f ip 127.0.0.1:9685
        log_end_msg 0
    ;;

    stop)
        log_daemon_msg "Stopping Tums" "tums"
        start-stop-daemon --stop --pidfile /var/run/tums.pid > /dev/null 2>&1
        start-stop-daemon --stop --pidfile /var/run/tums-fc.pid > /dev/null 2>&1
        killall -r exilog > /dev/null 2>&1
        killall fprobe
        log_end_msg 0 
    ;;

    force-reload|restart)
        log_daemon_msg "Restarting tums" "tums"
        start-stop-daemon --stop --pidfile /var/run/tums.pid > /dev/null 2>&1
        start-stop-daemon --stop --pidfile /var/run/tums-fc.pid > /dev/null 2>&1
        sleep 2
        export PYTHONPATH='/usr/local/tcs/tums'
        killall -r exilog > /dev/null 2>&1
        killall fprobe
        /usr/local/tcs/exilog-tums/exilog_agent.pl > /dev/null 2>&1
        start-stop-daemon --start --pidfile /var/run/tums.pid --exec /usr/local/tcs/tums/tums
        start-stop-daemon --start --pidfile /var/run/tums-fc.pid --exec /usr/local/tcs/tums/tums-fc
        /usr/sbin/fprobe -i %s -p -f ip 127.0.0.1:9685
        log_end_msg 0
    ;;\nesac\n""" % (config.LANPrimary, config.LANPrimary)
        host = config.ExternalName
        user = ''.join(host.split('.'))

        password = sha.sha(user).hexdigest()
        pwdhash = sha.sha(password).hexdigest()
        userD = {user:pwdhash}
        secret = password

        settings = ""

        settings += "LDAPPass = '%s'\n" % config.LDAPPassword
        settings += "LDAPBase = '%s'\n" % config.LDAPBase
        settings += "LDAPOrganisation = '%s'\n" % config.CompanyName
        settings += "defaultDomain = '%s'\n" % config.Domain
        settings += "SMBDomain = '%s'\n" % config.SambaDomain
        settings += 'users = %s\n' % repr(userD)
        settings += 'secret = %s\n' % repr(secret)
        
        updateServer = 'https://thebe.thusa.co.za:9680/'

        staticSettings = """LDAPPersonIdentifier = 'mail'
LDAPServer = '127.0.0.1'
LDAPManager = 'cn=Manager'
LDAPPeople = 'ou=People'
BaseDir = '/usr/local/tcs/tums'
sambaDN = True
port = 9682
Mailer='exim'
updateServer = '%s'
packageServer = 'http://updates.thusa.co.za/'
installDirectory = '/usr/local/tcs/tums'
capabilities = {'ipv6':True}
hiveAddress = "thebe.thusa.co.za"
thebePort='9680'\n""" % (
        updateServer
    )

        try:
            bghash = sha.sha(host+user+password).hexdigest()
            print bghash, host
            con = xmlrpclib.Server(updateServer)
            l   = con.addUser(bghash, host, config.CompanyName, user, password, secret, False)

            if l != "OK":
                print " Something went wrong creating the user account (Server did not OK). Please check it manualy. "

        except:
            print "Something broke creating the user account - please check it manualy"
        settings += staticSettings
        if os.path.exists('/etc/debian_version'):
            Utils.writeConf('/etc/init.d/tums', debianinitd, None)
        else:
            Utils.writeConf('/etc/init.d/tums', initd, None)

        os.system('chmod +x /etc/init.d/tums')
        Utils.writeConf('/usr/local/tcs/tums/Settings.py', settings, None)
        try: 
            ts = open('/usr/local/tcs/tums/tcsstore.dat')
        except:
            ts = open('/usr/local/tcs/tums/tcsstore.dat', 'wt')
            ts.write('V1.3\n')
        ts.close()

        os.system('mkdir -p /usr/local/tcs/tums/images/graphs > /dev/null 2>&1')

        if os.path.exists('/etc/debian_version'):
            os.system('echo "GRANT ALL ON exilog.* to exilog@localhost identified by \'exilogpw\';" | mysql  >/dev/null 2>&1 ')
        else:
            os.system('echo "GRANT ALL ON exilog.* to exilog@localhost identified by \'exilogpw\';" | mysql -u root --password="rossi"  >/dev/null 2>&1 ')

