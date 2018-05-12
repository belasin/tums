import config, os
from Core import Utils


class Plugin(object):
    parameterHook = "--ha"
    parameterDescription = "Reconfigure high availability"
    parameterArgs = ""
    autoRun = False
    configFiles = [ 
        "/etc/heartbeat/ha.cf",
    ]

    def reloadServices(self):
        os.system('/etc/init.d/heartbeat restart')

    def configureSlave(self, name):
        os.system('scp root@%s:/usr/local/tcs/tums/runningProfile /tmp/slave_profile' % name) 
        profileName = open('/tmp/slave_profile').read().strip('\n')
        os.system('scp root@%s:/usr/local/tcs/tums/profiles/%s /tmp/slave_profile.py' % (name, profileName))

        slaveConfigFile = open('/tmp/slave_profile.py').read()
        slaveConfig = {}
        # Read out the configuration and make a configuration dictionary
        exec slaveConfigFile in slaveConfig

        haConf = config.General['ha'][name]

        # LAN 
        slaveConfig['EthernetDevices'] = config.EthernetDevices
        slaveConfig['LANPrimary'] = config.LANPrimary
        
        # WAN 
        slaveConfig['WANDevices'] = config.WANDevices
        slaveConfig['WANPrimary'] = config.WANPrimary

        # Firewall
        slaveConfig['Shorewall'] = config.Shorewall
        slaveConfig['ShorewallBalance'] = config.ShorewallBalance
        slaveConfig['ShorewallSourceRoutes'] = config.ShorewallSourceRoutes

        # Proxy
        slaveConfig['ProxyConfig'] = config.ProxyConfig
        slaveConfig['ProxyAllowedHosts'] = config.ProxyAllowedHosts
        slaveConfig['ProxyAllowedDestinations'] = config.ProxyAllowedDestinations
        slaveConfig['ProxyAllowedDomains'] = config.ProxyAllowedDomains
        slaveConfig['ProxyBlockedDomains'] = config.ProxyBlockedDomains

        # LDAP merge
        slaveConfig['LDAPBase'] = config.LDAPBase
        slaveConfig['LDAPPassword'] = config.LDAPPassword

        slaveServices = []

        if haConf['failover.dhcp']:
            slaveConfig['DHCP'] = config.DHCP
            slaveServices.append('/etc/init.d/dhcp3-server')

        if haConf['failover.dns']:
            if config.General.get('zones'):
                slaveConfig['General']['zones'] = config.General.get('zones', '')
            slaveConfig['ExternalName'] = config.ExternalName
            slaveConfig['Hostname'] = config.Hostname
            slaveConfig['Domain'] = config.Domain
            slaveConfig['ThusaDNSUsername'] = config.ThusaDNSUsername
            slaveConfig['ThusaDNSPassword'] = config.ThusaDNSPassword
            slaveConfig['ThusaDNSAddress'] = config.ThusaDNSAddress
            slaveConfig['ForwardingNameservers'] = config.ForwardingNameservers
            slaveConfig['TCSAliases'] = config.TCSAliases
            slaveServices.append('/etc/init.d/bind9')

        if haConf['failover.pdc']:
            slaveConfig['SambaDomain'] = config.SambaDomain

            slaveConfig['SambaConfig'] = config.SambaConfig
            slaveConfig['SambaShares'] = config.SambaShares
            slaveServices.append('/etc/init.d/samba')

        if haConf['failover.routing']:
            for k,v in config.EthernetDevices.items():
                if v.get('routes'):
                    slaveConfig['EthernetDevices'][k]['routes'] = v.get('routes')
            slaveServices.append('/etc/init.d/quagga')
            
        if haConf['failover.smtp']:
            slaveConfig['SMTPRelay'] = config.SMTPRelay
            slaveConfig['LocalDomains'] = config.LocalDomains
            slaveConfig['Mail'] = config.Mail
            slaveServices.append('/etc/init.d/exim4')

        # Build our merged config..
        l = ""

        for k,v in slaveConfig.items():
            if not "__" in k:
                # make sure we don't transfer builtins
                l += '%s = %s\n' % (k, repr(v))
        
        fi = open('/tmp/sprofile', 'wt')
        fi.write(l)
        fi.close()

        os.system('scp /tmp/sprofile root@%s:/usr/local/tcs/tums/profiles/ha-slave.py' % name)
        os.system('scp /etc/heartbeat/* root@%s:/etc/heartbeat/' % name)

        services = '\n'.join(slaveServices)
        fi = open('/tmp/sserv', 'wt')
        fi.write(services)
        fi.close()
        os.system('scp /tmp/sserv root@%s:/usr/local/tcs/tums/bin/haslave' % name)

        slaveResource = """#!/bin/sh
#
# Description:  Vulani Slave resource.d
#
# Author:       Colin Alston <colin@thusa.co.za>
# Support:      support@thusa.co.za
# License:      All rights reserved
# Copyright:    (C) 2008 Thusa Business Support (Pty) Ltd. 

# Source function library.
. /etc/ha.d/resource.d//hto-mapfuncs

usage() {
        echo "Usage: $0 [node1 node2 ... ] {start|stop|restart|status}"
}

for arg in "$@"; do
    op=$arg
done

case "$op" in
    start|restart)
        echo "Reconfiguring slave"
        cp /usr/local/tcs/tums/runningProfile /usr/local/tcs/tums/defaultProfile
        echo 'ha-slave.py' > /usr/local/tcs/tums/currentProfile
        echo 'ha-slave.py' > /usr/local/tcs/tums/runningProfile
        /usr/local/tcs/tums/configurator -B  > /dev/null 2>&1
        echo "Starting Vulani services.."
        for i in `cat /usr/local/tcs/tums/bin/haslave`; do $i restart; done
        /etc/init.d/shorewall restart
    ;;
    stop)
        echo "Reconfiguring slave" 
        cp /usr/local/tcs/tums/defaultProfile /usr/local/tcs/tums/currentProfile
        cp /usr/local/tcs/tums/defaultProfile /usr/local/tcs/tums/runningProfile
        /usr/local/tcs/tums/configurator -B  > /dev/null 2>&1
        # Stop invasive services...
        echo "Stopping Vulani services.."
        for i in `cat /usr/local/tcs/tums/bin/haslave`; do $i stop; done
        /etc/init.d/dhcp3-server stop > /dev/null 2>&1
        /etc/init.d/quagga stop > /dev/null 2>&1
        /etc/init.d/shorewall restart
    ;;
    status)
        exit 0;;
    usage)
        usage; exit 0;;
    *)  
        usage; exit 0;;
esac

nodelist=`echo $* | sed 's%'$op'$%%'`

exit 0\n"""
        fi = open('/tmp/sserv', 'wt')
        fi.write(slaveResource)
        fi.close()
        os.system('scp /tmp/sserv root@%s:/etc/heartbeat/resource.d/vulani' % name)
        os.system('ssh root@%s chmod a+x /etc/heartbeat/resource.d/vulani' % name)

       

    def sendLDAP(self, name):
        os.system('/etc/init.d/slapd stop')
        os.system('slapcat > /tmp/ldap_tree')

        # Reconfigre LDAP now for slave replication

        # Start LDAP back up
        os.system('/etc/init.d/slapd start')

        # Send our ldap tree to the remote server
        os.system('scp /tmp/ldap_tree root@%s:/tmp/' % name)
        os.system('ssh root@%s /etc/init.d/slapd stop')
        
        os.system('ssh root@%s rm /var/lib/ldap/*' % name)
        os.system('ssh root@%s slapadd < /tmp/ldap_tree' % name)
        os.system('ssh root@%s chown -R openldap:openldap /var/lib/ldap' % name)

        conf = """include         /etc/ldap/schema/core.schema
include         /etc/ldap/schema/cosine.schema
include         /etc/ldap/schema/nis.schema
include         /etc/ldap/schema/inetorgperson.schema
include         /etc/ldap/schema/thusa.schema
include         /etc/ldap/schema/samba.schema

allow bind_v2

pidfile         /var/run/slapd/slapd.pid
argsfile        /var/run/slapd/slapd.args
loglevel        256
modulepath      /usr/lib/ldap
moduleload      back_bdb
sizelimit 500
tool-threads 1
defaultsearchbase       "o=%(base)s"

backend         bdb
#checkpoint 512 30

database        bdb

suffix          "o=%(base)s"
rootdn          "cn=Manager,o=%(base)s"
rootpw          %(pass)s

directory       "/var/lib/ldap"

# Replication 
updatedn    cn=Manager,o=%(base)s

updateref   ldap://%(master)s

access to attrs=userPassword
        by self write
        by dn="cn=Manager,o=%(base)s" write
        by * auth

access to *
        by self write
        by dn="cn=Manager,o=%(base)s" write
        by peername.ip=127.0.0.1 read
        by * read
        by * auth

index dc eq
index objectClass eq
index sn  eq
index cn  eq
index uid eq
index uniqueMember,memberUid pres,eq
index accountStatus,mail pres,eq
index associatedDomain pres,eq
index sOARecord,aRecord pres,eq\n""" % {
            'base': config.LDAPBase, 
            'pass': config.LDAPPassword,
            'master': Utils.getLanIPs(config)[0]
        }
        
        l = open('/tmp/slaveLdapConf', 'wt')
        l.write(conf)
        l.close()

        os.system('scp /tmp/slaveLdapConf root@%s:/etc/ldap/slapd.conf' % name)

        # Start up LDAP
        os.system('ssh root@%s /etc/init.d/slapd restart' % name)
        os.system('ssh root@%s /etc/init.d/heartbeat restart' % name)
        
    def configureMasterLDAP(self):
        
        replicas = []

        haConf = config.General.get('ha')
        for nodeip, v in haConf.items():
            if v['topology'] == 'slave':
                replicas.append("""replica host=%(ip)s
        binddn="cn=Manager, o=%(base)s"
        bindmethod=simple credentials=%(pass)s""" % {
                    'base': config.LDAPBase,
                    'pass': config.LDAPPassword,
                    'ip': nodeip,
                })

        conf = """include         /etc/ldap/schema/core.schema
include         /etc/ldap/schema/cosine.schema
include         /etc/ldap/schema/nis.schema
include         /etc/ldap/schema/inetorgperson.schema
include         /etc/ldap/schema/samba.schema
include         /etc/ldap/schema/thusa.schema

allow bind_v2

pidfile         /var/run/slapd/slapd.pid
argsfile        /var/run/slapd/slapd.args
loglevel        256
modulepath      /usr/lib/ldap
moduleload      back_bdb
tool-threads    1
defaultsearchbase "o=%(base)s"

backend         bdb
database        bdb
suffix          "o=%(base)s"
#checkpoint      128 15

threads         16
idletimeout     0
sizelimit       unlimited

rootdn          "cn=Manager,o=%(base)s"
rootpw          %(pass)s

directory       "/var/lib/ldap"

access to attrs=userPassword
        by self write
        by dn="cn=Manager,o=%(base)s" write
        by * auth

access to *
        by self write
        by dn="cn=Manager,o=%(base)s" write
        by peername.ip=127.0.0.1 read
        by * read
        by * auth


replogfile /var/lib/ldap/replogfile

%(replica)s

index dc eq
index objectClass,givenname,sn,cn,uid pres,eq
index uniqueMember,memberUid pres,eq
index accountStatus,mail pres,eq
index uidNumber,mailAlternateAddress pres,eq
index associatedDomain pres,eq
index sOARecord,aRecord pres,eq
index sambaSID,sambaSIDList,sambaGroupType pres,eq
index gidNumber,displayName,employeeType pres,eq\n""" % {
            'base': config.LDAPBase,
            'pass': config.LDAPPassword, 
            'replica': '\n'.join(replicas)
        }

        Utils.writeConf('/etc/ldap/slapd.conf', conf, '#')

        os.system("sed -i 's/SLURPD_START=auto/SLURPD_START=yes/g' /etc/default/slapd")

        os.system('/etc/init.d/slapd restart')


    def writeConfig(self, *a):
        if not config.General.get('ha'):
            # No Xen config
            return 

        haConf = config.General.get('ha')
        nodes = []
        masterName = ""
        for nodeip, v in haConf.items():
            nodes.append(v['name'])
            if v['topology'] == "master":
                masterName = v['name']

        hacf = """logfile /var/log/ha.log
keepalive 1

deadtime 30
initdead 80

bcast  %(lan)s

#   Tell what machines are in the cluster
#   node    nodename ...    -- must match uname -n
node    %(node)s


# Usualy 'crm yes'
#crm respawn 

auto_failback yes
"""     %   { 
                'lan': haConf.get('port', Utils.getLans(config)[0]),
                'node': '   '.join(nodes)
            }

        Utils.writeConf('/etc/heartbeat/ha.cf', hacf, '#')

        auth = "auth 2\n2 sha1 haf%s\n" % masterName

        Utils.writeConf('/etc/heartbeat/authkeys', auth, '#')

        os.system('chmod 0600 /etc/heartbeat/authkeys')
        
        nets = []
        for k,v in config.EthernetDevices.items():
            nets.append('%s/%s' % (v['ip'], k))
        
        conline = "%s   %s  vulani\n" % (masterName, ' '.join(nets))
        Utils.writeConf('/etc/heartbeat/haresources', conline, '#')

        vulaniResource = """#!/bin/sh
#
# Description:  Vulani Master resource.d
#
# Author:       Colin Alston <colin@thusa.co.za>
# Support:      support@thusa.co.za
# License:      All rights reserved
# Copyright:    (C) 2008 Thusa Business Support (Pty) Ltd.

exit 0"""
        l = open('/etc/heartbeat/resource.d/vulani', 'wt')
        l.write(vulaniResource)
        l.close()

        os.system('chmod a+x /etc/heartbeat/resource.d/vulani')

        # Before we restart our local HB service, make sure our slaves are OFF
        
        for name, v in haConf.items():
            if v['topology'] == 'slave':
                os.system('ssh root@%s /etc/init.d/heartbeat stop' % name)

        os.system('/etc/init.d/heartbeat restart')
        

        # Reconfigure SSH to not do SHKC 
        # This is required in order for fresh hosts not to block eachother interactivly
        ssh_config = """# SSH client configuration

Host *
    StrictHostKeyChecking no
    SendEnv LANG LC_*
    HashKnownHosts yes
    GSSAPIAuthentication yes
    GSSAPIDelegateCredentials no\n"""
        
        Utils.writeConf('/etc/ssh/ssh_config', ssh_config, '#')


        # Configure master LDAP
        self.configureMasterLDAP()

        # Configure slaves
        for nodeip, v in haConf.items():
            if v['topology'] == 'slave':
                self.configureSlave(nodeip)
                self.sendLDAP(nodeip)
