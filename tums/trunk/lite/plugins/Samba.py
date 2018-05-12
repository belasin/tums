import config, os
from Core import Utils


class Plugin(object):
    parameterHook = "--samba"
    parameterDescription = "Reconfigure Samba"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/samba/smb.conf",
        "/etc/samba/shares.conf",
    ]

    def reloadServices(self):
        os.system('/etc/init.d/samba restart')

    def writeConfig(self, *a):
        shares = ""
        for name in config.SambaShares:
            shares += "[%s]\n" % name

            for key, value in config.SambaShares[name].items():
                shares += "    %s = %s\n" % (key,value)
            shares += "\n"
        l = open('/etc/samba/shares.conf', 'wt')
        l.write(shares)
        l.close()
        start = """[global]\n    server string = %s
    netbios name = %s
    workgroup = %s
    interfaces = %s
    security = user
    max log size = 50
    log file = /var/log/samba/log.%%m
    printing = cups
    dont descend = /proc /dev
    dos filemode = yes\n""" % (config.CompanyName, config.Hostname, config.SambaDomain, config.LANPrimary)

        for k,v in config.SambaConfig.items():
            start+="    %s = %s\n" % (k,v)

        end = """    \n    passdb backend = ldapsam:ldap://127.0.0.1/
    ldap passwd sync = Yes
    ldap suffix = %s,o=%s
    ldap admin dn = cn=Manager,o=%s
    ;ldap ssl = start tls
    ldap group suffix = ou=Groups
    ldap user suffix = ou=People
    ldap machine suffix = ou=Computers
    ldap idmap suffix = ou=People
    add user script = /usr/sbin/smbldap-useradd -m "%%u"
    ldap delete dn = no
    delete user script = /usr/sbin/smbldap-userdel "%%u"
    add machine script = /usr/sbin/smbldap-useradd -w "%%u"
    add group script = /usr/sbin/smbldap-groupadd -p "%%g"
    delete group script = /usr/sbin/smbldap-groupdel "%%g"
    add user to group script = /usr/sbin/smbldap-groupmod -m "%%u" "%%g"
    delete user from group script = /usr/sbin/smbldap-groupmod -x "%%u" "%%g"
    set primary group script = /usr/sbin/smbldap-usermod -g "%%g" "%%u"

    include = /etc/samba/shares.conf\n""" % (
            ','.join(["dc=%s"%(i,) for i in config.Domain.split('.')]),
            config.LDAPBase,
            config.LDAPBase
        )

        l = open('/etc/samba/smb.conf', 'wt')
        l.write(start)
        l.write(end)
        l.close()

