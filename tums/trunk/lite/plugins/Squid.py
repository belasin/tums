import config, os
from Core import Utils


class Plugin(object):
    parameterHook = "--squid"
    parameterDescription = "Reconfigure Squid"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/squid/allow_dst",
        "/etc/squid/allow_hosts",
        "/etc/squid/allow_domains",
        "/etc/squid/squid.conf",
        "/etc/squid/msntauth.conf"
    ]
    def __init__(self):
        if os.path.exists('/etc/debian_version'):
            # Patch for debian
            confs = []
            for i in self.configFiles:
                confs.append(i.replace('squid/', 'squid3/'))
            self.configFiles = confs

    def reloadServices(self):
        os.system('/etc/init.d/squid reload')

    def writeConfig(self, *a):
        path = "/etc/squid/"
        if os.path.exists('/etc/debian_version'):
            path = "/etc/squid3/"
                
        allowDest = ""
        allowHost = ""
        allowDom = ""
        blockDom = ""
        for h in config.ProxyAllowedDomains:
            allowDom += "%s\n" % h

        for h in config.ProxyBlockedDomains:
            blockDom += "%s\n" % h

        for h in config.ProxyAllowedDestinations:
            allowDest += "%s\n" % h

        for h in config.ProxyAllowedHosts:
            allowHost += "%s\n" % h

        l = open(path+'allow_dst', 'wt')
        l.write(allowDest)
        l.close()

        l = open(path+'allow_hosts', 'wt')
        l.write(allowHost)
        l.close()

        l = open(path+'allow_domains', 'wt')
        l.write(allowDom)
        l.close()

        l = open(path + 'denied_domains', 'wt')
        l.write(blockDom)
        l.close()

        if config.ProxyConfig.get('adauth', None):
            if os.path.exists('/etc/debian_version'):
                authentication = "auth_param basic program /usr/lib/squid3/msnt_auth"
            else:
                authentication = "auth_param basic program /usr/libexec/squid/msnt_auth"
            l = open(path+'msntauth.conf', 'wt')
            l.write('server      %s       %s       %s\n' % (config.ProxyConfig['adserver'], config.ProxyConfig['adserver'], config.ProxyConfig['addom']))
            l.close()
        else:
            authentication = """auth_param basic program /usr/libexec/squid/squid_ldap_auth -b "ou=People,%s,o=%s" -f (&(uid=%%s)(employeeType=squid)) localhost
""" % (','.join(["dc=%s"%(i,) for i in config.Domain.split('.')]), config.LDAPBase)

        timeAcls = ""
        denys = ""
        allows = ""
        if config.ProxyConfig.get('timedaccess', None):
            for name, value in config.ProxyConfig['timedaccess'].items():
                acl = ""
                if value['sites']:
                    l = open(path+name+'-sites', 'wt')
                    l.write('\n'.join(value['sites']))
                    l.close()
                    timeAcls += "acl %ssites dstdomain \"/etc/squid/%s-sites\"\n" % (name, name)
                    acl = "%stime %ssites" % (name, name)
                else:
                    acl = "%stime"

                timeAcls += "acl %stime time %s %s-%s\n" % (name, value['days'], value['timefrom'], value['timeto'])

                if value['allow']:
                    if value['authenticate']:
                        acl += " password"
                    
                    allows += "http-access allow %s\n" % acl
                else:
                    denys += "http-access deny %s\n" % acl

        squidconf = """http_port 8080 transparent
visible_hostname %(host)s
hierarchy_stoplist cgi-bin ? .pl
acl QUERY urlpath_regex cgi-bin \\? .pl .asp mail.%(domain)s
no_cache deny QUERY
cache_mem 32 MB
maximum_object_size 1000000 KB
cache_dir ufs /var/cache/squid/ 10000 16 256
cache_access_log /var/log/squid/access.log
cache_store_log none
pid_filename /var/run/squid.pid
#ftp_user squid@bulwer.thusa.net
hosts_file /etc/hosts
%(auth)s
auth_param basic children 5
auth_param basic realm TCS Web Proxy
auth_param basic credentialsttl 2 hours
refresh_pattern ^ftp:           1440    20%%     10080
refresh_pattern ^gopher:        1440    0%%      1440
refresh_pattern .               0       20%%     4320
refresh_pattern windowsupdate.com/.*\\.(cab|exe)         4320 100%% 43200 reload-into-ims
refresh_pattern download.microsoft.com/.*\\.(cab|exe)    4320 100%% 43200 reload-into-ims
refresh_pattern akamai.net/.*\\.(cab|exe)                4320 100%% 43200 reload-into-ims
acl all src 0.0.0.0/0.0.0.0
acl manager proto cache_object
acl localhost src 127.0.0.1/32
acl to_localhost dst 127.0.0.0/8
acl allow_hosts src "/etc/squid/allow_hosts"
acl denied_domains dstdomain "/etc/squid/denied_domains"
acl allow_domain dstdomain "/etc/squid/allow_domains"
acl allow_dst dst "/etc/squid/allow_dst"
%(timeacls)s
acl password proxy_auth REQUIRED
acl SSL_ports port 443 563
acl Safe_ports port 80          # http
acl Safe_ports port 21          # ftp
acl Safe_ports port 443 563     # https, snews
acl Safe_ports port 70          # gopher
acl Safe_ports port 210         # wais
acl Safe_ports port 1025-65535  # unregistered ports
acl Safe_ports port 280         # http-mgmt
acl Safe_ports port 488         # gss-http
acl Safe_ports port 591         # filemaker
acl Safe_ports port 777         # multiling http
acl Safe_ports port 901         # SWAT
acl purge method PURGE
acl CONNECT method CONNECT
#redirect_program /usr/local/bin/scavr.py -c /etc/squid/scavr.conf
redirect_children 5
redirector_access deny localhost
http_access allow manager localhost
http_access deny manager
http_access allow purge localhost
http_access deny purge
http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access deny to_localhost
http_access deny denied_domains
http_access allow allow_domain
http_access allow allow_dst
%(denys)s
http_access allow allow_hosts
%(allows)s
http_access allow all password
http_access deny all
http_reply_access allow all
icp_access allow all
cache_mgr postmaster@%(domain)s
logfile_rotate 7
append_domain .%(domain)s
forwarded_for on
cachemgr_passwd %(ldappass)s shutdown
cachemgr_passwd %(ldappass)s info stats/objects
cachemgr_passwd disable all
snmp_access allow localhost
coredump_dir /var/log/squid
extension_methods REPORT MERGE MKACTIVITY CHECKOUT
acl snmpcommunity snmp_community public
snmp_port 3401
snmp_access allow snmpcommunity localhost
snmp_access deny all\n""" % {
            'host':config.Hostname + "." + config.Domain,
            'domain':config.Domain,
            'auth':authentication,
            'ldappass':config.LDAPPassword,
            'timeacls':timeAcls,
            'allows': allows,
            'denys': denys,
        }
        # Apply debian fixes
        if os.path.exists('/etc/debian_version'):
            squidconf = squidconf.replace('/usr/libexec/squid/squid_ldap_auth', '/usr/lib/squid3/squid_ldap_auth')
            squidconf = squidconf.replace('/etc/squid/', '/etc/squid3/')
            os.system('mkdir -p /var/cache/squid > /dev/null 2>&1')
            os.system('chown proxy:proxy /var/cache/squid')
        l = open(path+'squid.conf', 'wt')
        l.write(squidconf)
        l.close()



