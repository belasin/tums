echo "auth,authpriv.*                 /var/log/auth.log" > /etc/syslog.conf
echo "*.*;lpr,user,uucp,cron,auth,authpriv,local0,local1,local2,local3,local4,local5,local6,local7.none          -/var/log/syslog" >> /etc/syslog.conf
echo "cron.*                         /var/log/cron.log" >> /etc/syslog.conf
echo "daemon.*                        -/var/log/daemon.log" >> /etc/syslog.conf
echo "kern.*                          -/var/log/kern.log" >> /etc/syslog.conf
echo "lpr.*                           -/var/log/lpr.log" >> /etc/syslog.conf
echo "mail.*                          /var/log/mail.log" >> /etc/syslog.conf
echo "user.*                          -/var/log/user.log" >> /etc/syslog.conf
echo "uucp.*                          -/var/log/uucp.log" >> /etc/syslog.conf
echo "local0,local1,local3,local5.*   -/var/log/localproc.log" >> /etc/syslog.conf
echo "local6.*                        -/var/log/imapd.log" >> /etc/syslog.conf
echo "local2.*                        -/var/log/ppp.log" >> /etc/syslog.conf
echo "local4.*                        -/var/log/slapd.log" >> /etc/syslog.conf
echo "local7.*                        -/var/log/dhcpd.log" >> /etc/syslog.conf
echo "mail.info                       -/var/log/mail.info" >> /etc/syslog.conf
echo "mail.warn                       -/var/log/mail.warn" >> /etc/syslog.conf
echo "mail.err                        /var/log/mail.err" >> /etc/syslog.conf
echo "*.=debug;\\" >> /etc/syslog.conf
echo "        auth,authpriv.none;\\" >> /etc/syslog.conf
echo "        news.none;mail.none     -/var/log/debug" >> /etc/syslog.conf
echo "*.=info;*.=notice;*.=warn;\\" >> /etc/syslog.conf
echo "        auth,authpriv.none;\\" >> /etc/syslog.conf
echo "        cron,daemon.none;\\" >> /etc/syslog.conf
echo "        mail,news.none          -/var/log/messages" >> /etc/syslog.conf
echo "*.emerg                         *" >> /etc/syslog.conf
echo "*.emerg                         /var/log/emergency" >> /etc/syslog.conf
/etc/init.d/sysklogd restart
tail /var/log/syslog | mail -s "THEBE Syslog reconfigured." notify@thusa.co.za
