#!/usr/bin/python
import os, sys, copy, time, datetime
import LDAP, ldap
import config

sys.path.append('.')
sys.path.append('/usr/lib/python2.5/site-packages')
sys.path.append('/usr/lib/python2.5')

LDAPOrganisation = config.CompanyName
LDAPBase = config.LDAPBase
LDAPPass = config.LDAPPassword
Domain = config.Domain

#LDAPBase = 'TRYPTOPHAN'
#LDAPPass = 'wsthusa'
#Domain = 'thusa.co.za'

LDAPServer = "127.0.0.1"   # LDAP Server
LDAPManager = "cn=Manager"

l = LDAP.createLDAPConnection(LDAPServer, 'o='+LDAPBase, LDAPManager, LDAPPass)
dc = "ou=People,%s,o=%s" % (LDAP.domainToDC(Domain), LDAPBase)
oldRecord =  LDAP.getUsers(l, dc, 'uid=root')[0]

newRoot = copy.deepcopy(oldRecord)

newRoot['objectClass'] = ['inetOrgPerson', 'sambaSamAccount', 'posixAccount', 'shadowAccount', 'thusaUser']
newRoot['employeeType'] = ['tumsAdmin', 'squid']
newRoot['accountStatus'] = ['active']
newRoot['mail'] = ['root@'+Domain]
newRoot['loginShell'] = ['/bin/false']
newRoot['mailForwardingAddress'] = ['notify@thusa.co.za'] 

try:
    LDAP.modifyElement(l, 'uid=root'+','+dc, oldRecord, newRoot)
except Exception, L:
    print "Failed to add root", L

