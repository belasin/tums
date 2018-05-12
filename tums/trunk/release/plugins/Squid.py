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
        "/etc/squid/msntauth.conf",
        "/etc/squid/redir_hosts"
    ]

    def reloadServices(self):
        os.system('/etc/init.d/squid reload')

    def writeConfig(self, *a):
        path = "/etc/squid/"
        # Make sure Dansguardian is sorted 
        os.system('mkdir -p /var/log/dansguardian')
        os.system('touch /var/log/dansguardian/access.log')
        os.system('chown -R dansguardian:dansguardian /var/log/dansguardian')

        # Sort out update cache permissions
        os.system('mkdir -p /var/lib/samba/updates/download')
        os.system('chown -R proxy:proxy /var/lib/samba/updates')
        os.system('chmod -R a+rwx /var/lib/samba/updates')
        os.system('chmod -R a+rwx /usr/local/tcs/tums/uaxeldb')
        #Fix read permissions for config files
        os.system('chmod a+r /etc/squid')
        os.system('chmod a+r /etc/squid/allow_hosts')
        os.system('chmod a+r /etc/squid/allow_dst')
        os.system('chmod a+r /etc/squid/allow_domains')
                
        allowDest = ""
        allowHost = ""
        allowDom = "vulaniblockdomainholder.vulani\n"
        blockDom = "vulaniblockdomainholder.vulani\n"
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

        adGroupAuth = ""
        adGroups = []

        aclEntries = [] #Make sure we don't break the squid config by making reference to undefined acls keep a list of defined acls and only use them if they are in this list

        if config.ProxyConfig.get('adauth', None):
            if config.ProxyConfig.get('addom', None) and config.ProxyConfig.get('adldapuser', None) and config.ProxyConfig.get('adldappass', None):
                basedn = str.join(',',["dc="+str(dfrag) for dfrag in config.ProxyConfig.get('addom', str).split('.')])
                adInfo = {
                    'basedn': basedn,
                    'ldapuser': config.ProxyConfig['adldapuser'],
                    'ldappass': config.ProxyConfig['adldappass'],
                    'adserver': config.ProxyConfig['adserver']
                }
                authentication = "auth_param basic program /usr/lib/squid/ldap_auth -R -b \"%(basedn)s\" -D \"%(ldapuser)s\" -w \"%(ldappass)s\" -f sAMAccountName=%%s -h %(adserver)s -p389" % adInfo

                if config.ProxyConfig.get('adacls', None):
                    adGroupPaths = []
                    for adacl in config.ProxyConfig.get('adacls', []):
                        if '=' in adacl[1]:
                            filter = "(memberof=cn=%%a,%s,%s)" % (adacl[1],basedn)
                            if filter not in adGroupPaths:
                                adGroupPaths.append(filter)
                            adGroups.append("acl vacl_%s external adACLGroup %s" % (adacl[2], adacl[0]))
                            aclEntries.append(adacl[2])
                        else:
                            print "Invalid AD Group path", adacl[1]

                    if len(adGroupPaths) > 0:
                        if len(adGroupPaths) > 1:
                            adInfo["adGroupFilter"] = "(|%s)" % str.join("",adGroupPaths)
                        else:
                            adInfo["adGroupFilter"] = adGroupPaths[0]


                        authentication = authentication + "\nexternal_acl_type adACLGroup %%LOGIN /usr/lib/squid/squid_ldap_group -R -b \"%(basedn)s\" -D \"%(ldapuser)s\" -w \"%(ldappass)s\" -f \"(&%(adGroupFilter)s(objectclass=person)(sAMAccountName=%%v))\" -h %(adserver)s -p389" % adInfo

            else:
                authentication = "auth_param basic program /usr/lib/squid/msnt_auth"
                l = open(path+'msntauth.conf', 'wt')
                l.write('server      %s       %s       %s\n' % (config.ProxyConfig['adserver'], config.ProxyConfig['adserver'], config.ProxyConfig['addom']))
                l.close()
                os.system('chmod a+r %smsntauth' % path) 
        else:
            #authentication = "auth_param basic program /usr/libexec/squid/squid_ldap_auth -b "ou=People,%s,o=%s" -f (&(uid=%%s)(employeeType=squid)) localhost
            #""" % (','.join(["dc=%s"%(i,) for i in config.Domain.split('.')]), config.LDAPBase)
            
            authentication = "auth_param basic program /usr/libexec/squid/squid_ldap_auth -b \"o=%s\" -f " % config.LDAPBase
            # Muchos haxed ldap search
            authentication += "(&(|(mail=%%s@%s)(mail=%%s))(employeeType=squid)) localhost \n" % config.Domain 

        if config.ProxyConfig.get('contentfilter', None):
            cfilter = "cache_peer 127.0.0.1 parent 8081 0 no-query login=*:nopassword\n"
        else:
            cfilter = ""

            
        
        timeAcls = ""

        # Do user ACLS here

        for usrs, aclname in config.ProxyConfig.get('aclusers',[]):
            timeAcls += "acl vacl_%s proxy_auth %s\n" % (aclname, ' '.join([i.strip() for i in usrs.split(',')]))
            aclEntries.append(aclname)

        # Do more destination ACL's here
        for doms, aclname in config.ProxyConfig.get('domacls',[]):
            timeAcls += "acl vacl_%s dstdomain %s\n" % (aclname, ' '.join([i.strip() for i in doms.split(',')]))
            aclEntries.append(aclname)
            
        srcacls = ""
        for i in config.ProxyConfig.get('srcacls', []):
            src, acl = i 
            if not '/' in src:
                src_ip = "%s/32" % src
            else:
                src_ip = src

            srcacls += "acl vacl_%s src %s\n" % (acl, src_ip)
            aclEntries.append(acl)

        denys = ""
        allows = ""
        cnt = 0
        if config.ProxyConfig.get('timedaccess', None):
            for action, days, times, domain, exacl in config.ProxyConfig['timedaccess']:
                if exacl not in aclEntries:
                    continue
                cnt += 1
                timeAcls += "acl time_acl%s time %s %s\n" % (cnt, days, times)
                if domain:
                    timeAcls += "acl domain_acl%s dstdomain %s\n" % (cnt, domain)

                if action: 
                    allows += "http_access allow all time_acl%s" % (cnt, )
                else:
                    allows += "http_access deny all time_acl%s" % (cnt, )

                if domain:
                    allows += " domain_acl%s" % (cnt)

                if exacl:
                    allows += " vacl_%s" % exacl

                allows += "\n"

        bindaddr = ""
        if config.ProxyConfig.get('bindaddr'):
            bindaddr = "tcp_outgoing_address %s" % config.ProxyConfig.get('bindaddr')

        routingacls = ""
        for i in config.ProxyConfig.get('aclgateways', []):
            gateway, acl = i
            if acl in aclEntries:
                routingacls += "tcp_outgoing_address %s vacl_%s\n" % (gateway, acl)

        for acl,perm in config.ProxyConfig.get('aclperms', []):
            aclList = []
            for e in acl.split():
                if e in aclEntries:
                    aclList.append('vacl_'+e)
            if aclList:
                if perm == "allow":
                    allows += "http_access allow all %s\n" % str.join(' ',aclList)
                else:
                    allows += "http_access deny all %s\n" % str.join(' ',aclList)
       
        # Configure our update accelerator
        updator = ""
        redirCache = ""
        redircacheallow = ""
        if config.ProxyConfig.get('updates', {}).get('enabled',None):

            # Allow redir hosts to bypass all Squid auth when we use a captive portal. Also point all to the rewriter
            if config.ProxyConfig.get('captive'):
                redirCache = "acl redir_hosts src \"/etc/squid/redir_hosts\""
                redircacheallow = "http_access allow redir_hosts"
            
            rfi = open('/etc/squid/redir_hosts', 'wt')
            for iface, net in Utils.getLanNetworks(config).items():
                rfi.write(net+'\n')
            rfi.close()
            
            updateConf = config.ProxyConfig['updates']
            # Get config options and set some defaults
            diskspace = updateConf.get('maxspace', 95)
            speed = updateConf.get('maxspeed', 256)
            
            # accelerator.conf
            accelerator = """#Proxy Settings
UPSTREAM_USER=
UPSTREAM_PASSWORD=
PROXY_PORT=8080
ENABLE_UPDXLRATOR=on
UPSTREAM_PROXY=

#Accelerator Settings
AUTOCHECK_SCHEDULE=daily
LOW_DOWNLOAD_PRIORITY=off
ENABLE_AUTOCHECK=on
PASSIVE_MODE=off
FULL_AUTOSYNC=off
ENABLE_LOG=on
MAX_DISK_USAGE=%s
NOT_ACCESSED_LAST=month1
CHILDREN=5
MAX_DOWNLOAD_RATE=%s

GREEN_ADDRESS=127.0.0.1\n""" % (diskspace, speed)
            
            acc = open('/etc/squid/accelerator.conf', 'wt')
            acc.write(accelerator)
            acc.close()

            # meh
            os.system('chmod a+r /etc/squid/accelerator.conf')
            
            # squid.conf directives
            updator = "url_rewrite_program /usr/local/tcs/tums/bin/update_cache\n"
            updator += "url_rewrite_children 20\n"
            updator += "url_rewrite_access allow redir_cache\n"
            if config.ProxyConfig.get('captive'):
                updator += "url_rewrite_access allow redir_hosts\n"
            updator += "url_rewrite_access deny allow_hosts\n"
            updator += "url_rewrite_access deny allow_domain\n"
            updator += "url_rewrite_access deny allow_dst\n"

            if not config.ProxyConfig.get('captive'):
                updator += "url_rewrite_access deny all\n"

        #Allow for someone to specify alternative bound ports asside from the default 8080
        #Some installations require explicit binding to port 3128, by no means does this mean
        #that it should be encouraged ...
        squidConf_bindPorts = ""
        if config.ProxyConfig.get('bindports'):
            bindPorts = str(config.ProxyConfig.get('bindports'))
            for port in bindPorts.replace(' ','').split(','):
                if port == "8080":
                    continue
                squidConf_bindPorts += "http_port %s transparent\n" % (port)

        squidconf = """http_port 8080 transparent
%(bindPorts)s
visible_hostname %(host)s
hierarchy_stoplist cgi-bin ? .pl
acl QUERY urlpath_regex cgi-bin \\? .pl .asp mail.%(domain)s
no_cache deny QUERY
cache_mem 32 MB
maximum_object_size 1000000 KB
cache_dir ufs /var/cache/squid/ 10000 16 256
cache_access_log /var/log/squid/access.log
cache_log  /var/log/squid/cache.log
cache_store_log none
pid_filename /var/run/squid.pid
#ftp_user squid@bulwer.thusa.net
ignore_expect_100 on

hosts_file /etc/hosts
%(auth)s
auth_param basic children 5
auth_param basic realm Vulani Web Proxy
auth_param basic credentialsttl 2 hours
refresh_pattern ^ftp:           1440    20%%     10080
refresh_pattern ^gopher:        1440    0%%      1440
refresh_pattern .               0       20%%     4320
refresh_pattern windowsupdate.com/.*\\.(cab|exe)         4320 100%% 43200 reload-into-ims
refresh_pattern download.microsoft.com/.*\\.(cab|exe)    4320 100%% 43200 reload-into-ims
refresh_pattern akamai.net/.*\\.(cab|exe)                4320 100%% 43200 reload-into-ims
strip_query_terms off
#acl support.microsoft.com dstdomain support.microsoft.com
#reply_header_access Accept-Encoding deny support.microsoft.com
#request_header_access Accept-Encoding deny support.microsoft.com
acl all src 0.0.0.0/0.0.0.0
acl manager proto cache_object
acl localhost src 127.0.0.1/32
acl to_localhost dst 127.0.0.0/8
%(srcacls)s
%(adAcls)s
acl allow_hosts src "/etc/squid/allow_hosts"
acl denied_domains dstdomain "/etc/squid/denied_domains"
acl allow_domain dstdomain "/etc/squid/allow_domains"
acl allow_dst dst "/etc/squid/allow_dst"
acl redir_cache dstdomain .microsoft.com
acl redir_cache dstdomain .windowsupdate.com
acl redir_cache dstdomain .mirror.ac.za
acl redir_cache dstdomain .debian.org
acl redir_cache dstdomain .ubuntu.com
acl redir_cache dstdomain .avg.com
%(redircache)s
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
redirector_access deny localhost
http_access allow manager localhost
http_access deny manager
http_access allow purge localhost
http_access deny purge
http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access deny to_localhost
http_access allow all localhost
%(allows)s
http_access deny denied_domains

http_access allow allow_domain
http_access allow allow_dst
%(denys)s
http_access allow allow_hosts
%(redircacheallow)s
%(passwordAuth)s
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
snmp_access deny all\n%(updator)s\n%(bindaddr)s\n%(cfilter)s\n%(routingacls)s""" % {
            'redircache': redirCache,
            'host':config.Hostname + "." + config.Domain,
            'bindPorts':squidConf_bindPorts,
            'domain':config.Domain,
            'auth':authentication,
            'ldappass':config.LDAPPassword,
            'timeacls':timeAcls,
            'allows': allows,
            'denys': denys,
            'redircacheallow':redircacheallow,
            'updator': updator,
            'bindaddr': bindaddr, 
            'cfilter': cfilter,
            'routingacls': routingacls, 
            'srcacls': srcacls,
            'adAcls': str.join('\n', adGroups),
            'passwordAuth': len(adGroups) > 0 and config.ProxyConfig.get('adGroupDefaultDeny', False) and ' ' or 'http_access allow all password'
        }
        # Apply debian fixes
        squidconf = squidconf.replace('/usr/libexec/squid/squid_ldap_auth', '/usr/lib/squid/ldap_auth')
        #squidconf = squidconf.replace('/etc/squid/', '/etc/squid/')
        os.system('mkdir -p /var/cache/squid > /dev/null 2>&1')
        os.system('mkdir -p /var/log/squid > /dev/null 2>&1')
        os.system('chown proxy:proxy /var/cache/squid')
        os.system('touch /var/log/tums_cache.log')
        os.system('chown proxy:proxy /var/log/tums_cache.log')
        os.system('chmod a+rwx /var/log/tums_cache.log')
        os.system('chown -R proxy:proxy /var/log/squid')
        os.system('rm -r /var/log/squid3 > /dev/null 2>&1')
        l = open(path+'squid.conf', 'wt')
        l.write(squidconf)
        l.close()

        # Configure WPAD script for each LAN range. 
        for ip in Utils.getLanIPs(config):
            pacfile = """function FindProxyForURL(url, host)
{
  if (shExpMatch(url, "http:*")) 
     return "PROXY %(proxyUrl)s:8080";
  if (shExpMatch(url, "https:*"))
     return "PROXY %(proxyUrl)s:8080";
  if (shExpMatch(url, "ftp:*"))
     return "PROXY %(proxyUrl)s:8080";

  return "DIRECT";
}\n""" % {'proxyUrl': ip}
            fp = open('/var/www/localhost/htdocs/wpad-%s.pac' % ip.replace('.', '-'), 'wt')
            fp.write(pacfile)
            fp.close()

        try:
            default = Utils.getLanIPs(config)[0]
            os.system('cp /var/www/localhost/htdocs/wpad-%s.pac /var/www/localhost/htdocs/wpad.dat' % default.replace('.', '-'))
        except:
            pass
