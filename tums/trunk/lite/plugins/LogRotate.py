import config, os
from Core import Utils


class Plugin(object):
    parameterHook = "--logs"
    parameterDescription = "Reconfigure logging"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/logrotate.d/",
        "/etc/syslog.conf"
    ]

    def __init__(self):
        if os.path.exists('/etc/debian_version'):
            self.configFiles = ["/etc/ddclient.conf"]
    
    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        syslogConfig="""# TCS Logging setup
auth,authpriv.*                 /var/log/auth.log
*.*;lpr,user,uucp,cron,auth,authpriv,local0,local1,local2,local3,local4,local5,local6,local7.none          -/var/log/syslog
cron.*                         /var/log/cron.log
daemon.*                        -/var/log/daemon.log
kern.*                          -/var/log/kern.log
lpr.*                           -/var/log/lpr.log
mail.*                          /var/log/mail.log
user.*                          -/var/log/user.log
uucp.*                          -/var/log/uucp.log
local0,local1,local3,local5.*   -/var/log/localproc.log
local6.*                        -/var/log/imapd.log
local2.*                        -/var/log/ppp.log
local4.*                        -/var/log/slapd.log
local7.*                        -/var/log/dhcpd.log
mail.info                       -/var/log/mail.info
mail.warn                       -/var/log/mail.warn
mail.err                        /var/log/mail.err
*.=debug;\
        auth,authpriv.none;\
        news.none;mail.none     -/var/log/debug
*.=info;*.=notice;*.=warn;\
        auth,authpriv.none;\
        cron,daemon.none;\
        mail,news.none          -/var/log/messages
*.emerg                         *
*.emerg                         /var/log/emergency"""

        Utils.writeConf('/etc/syslog.conf', syslogConfig, '#')

        if os.path.exists('/etc/debian_version'):
            clamavd = """/var/log/clamav/clamav.log {
     rotate 12
     weekly
     compress
     delaycompress
     create 640  Debian-exim Debian-exim
     postrotate
     /etc/init.d/clamav-daemon reload-log > /dev/null
     endscript
     }\n"""
            clamavfc = """/var/log/clamav/freshclam.log {
     rotate 12
     weekly
     compress
     delaycompress
     create 640 Debian-exim Debian-exim
     postrotate
     /etc/init.d/clamav-freshclam reload-log > /dev/null
     endscript
     }\n"""
            exim4 = """/var/log/exim4/mainlog /var/log/exim4/rejectlog {
        daily
        missingok
        rotate 10
        compress
        delaycompress
        notifempty
        create 640 Debian-exim adm
}           

/var/log/exim4/paniclog {
        weekly
        missingok
        rotate 10
        compress
        delaycompress
        notifempty
        create 640 Debian-exim adm
}\n"""
            Utils.writeConf('/etc/logrotate.d/clamav-daemon', clamavd, '#')
            Utils.writeConf('/etc/logrotate.d/clamav-freshclam', clamavfc, '#')
            Utils.writeConf('/etc/logrotate.d/exim4-base', exim4, '#')

