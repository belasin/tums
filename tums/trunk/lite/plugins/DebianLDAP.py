import config, os
from Core import Utils

class Plugin(object):
    """ Configures everything needed for Debian LDAP. """
    parameterHook = "--debldap"
    parameterDescription = "Reconfigure LDAP PAM on Debian"
    parameterArgs = ""
    autoRun = True
    required = "debian"
    configFiles = [ 
        "/etc/pam.d/common-account",
        "/etc/pam.d/common-auth",
        "/etc/pam.d/common-password",
        "/etc/pam.d/common-session",
        "/etc/pam.d/passwd",
        "/etc/nsswitch.conf",
        "/etc/ldap.conf",
        "/etc/ldap.secret"
    ]

    def reloadServices(self):
        os.system('/etc/init.d/dhcpd restart')

    def writeFile(self, file, content):
        f = open(file,'wt')
        f.write(content)
        f.close()

    def commonAuth(self):
        content = """auth    required        pam_unix.so nullok_secure
auth    sufficient      pam_ldap.so\n"""
        self.writeFile('/etc/pam.d/common-auth', content)

    def commonAccount(self):
        content = """account sufficient      pam_ldap.so
account required        pam_unix.so\n"""
        self.writeFile('/etc/pam.d/common-account', content)

    def commonPassword(self):
        content = """password   sufficient  pam_unix.so nullok obscure min=4 max=8 md5
password   sufficient   pam_ldap.so\n"""
        self.writeFile('/etc/pam.d/common-password', content)

    def commonSession(self):
        content = """session required        pam_mkhomedir.so skel=/etc/skel/
session required        pam_unix.so
session sufficient      pam_ldap.so
session optional        pam_foreground.so\n"""
        self.writeFile('/etc/pam.d/common-session', content)

    def domainToDC(self, dom):
        return 'dc='+',dc='.join(dom.split('.'))

    def nscdSetup(self):
        nsswitch = """passwd:   files ldap [NOTFOUND=return] db
shadow:      files ldap [NOTFOUND=return] db
group:       files ldap [NOTFOUND=return] db
# passwd:    db files nis
# shadow:    db files nis
# group:     db files nis
hosts:       files dns
networks:    files dns
services:    db files
protocols:   db files
rpc:         db files
ethers:      db files
netmasks:    files
netgroup:    files
bootparams:  files
automount:   files
aliases:     files\n"""
        self.writeFile('/etc/nsswitch.conf', nsswitch)

        nssconf = """host 127.0.0.1
ssl off
suffix    "ou=People,%(binddn)s,o=%(bindorg)s"
uri ldap://127.0.0.1/
pam_password exop
ldap_version 3
bind_policy soft
port 389
scope one
pam_filter objectclass=posixAccount
pam_login_attribute uid
pam_member_attribute uidNumber
pam_template_login_attribute uid
nss_base_passwd         ou=People,%(binddn)s,o=%(bindorg)s
nss_base_passwd         ou=Computers,%(binddn)s,o=%(bindorg)s
nss_base_shadow         ou=People,%(binddn)s,o=%(bindorg)s
nss_base_group          ou=Groups,%(binddn)s,o=%(bindorg)s
base ou=People,%(binddn)s,o=%(bindorg)s
rootbinddn cn=Manager,o=%(bindorg)s
binddn cn=Manager,o=%(bindorg)s
bindpw %(bindpass)s\n""" % {
    'bindorg': config.LDAPBase,
    'binddn': self.domainToDC(config.Domain),
    'bindpass': config.LDAPPassword
    }
        self.writeFile('/etc/ldap.conf', nssconf)
        self.writeFile('/etc/ldap.secret', config.LDAPPassword)
        # Fix file linking
        os.system('rm /etc/libnss-ldap.conf /etc/libnss-ldap.secret /etc/pam_ldap.conf /etc/pam_ldap.secret')
        os.system('ln -s /etc/ldap.conf /etc/libnss-ldap.conf')
        os.system('ln -s /etc/ldap.conf /etc/pam_ldap.conf')
        os.system('ln -s /etc/ldap.secret /etc/libnss-ldap.secret')
        os.system('ln -s /etc/ldap.secret /etc/pam_ldap.secret')
        # permissions fix
        os.system('chmod og-rw /etc/ldap.secret')
        os.system('chmod og-rw /etc/ldap.conf') 

    def writeConfig(self, *a):
        #os.system('cp /usr/share/doc/samba-doc/examples/LDAP/samba.schema.gz /etc/ldap/schema/')
        #os.system('gunzip /etc/ldap/schema/samba.schema.gz')

        # We really should do TLS on OpenLDAP so lets go
        

        self.commonAuth()
        self.commonAccount()
        self.commonPassword()
        self.commonSession()
        self.nscdSetup()

