#!/usr/bin/python2.4
import os, sys, copy, time, datetime
import LDAP, ldap
import config
LDAPOrganisation = config.CompanyName # Organisation name
LDAPBase = config.LDAPBase         # Top level o of LDAP tree
LDAPPass = config.LDAPPassword      # Password for manager
Domain = config.Domain     # The domain which becomes the base dn
SDomain = config.SambaDomain   # The Samba domain name
clearPassword = "password"    # Password to set for the users

LDAPServer = "127.0.0.1"   # LDAP Server
LDAPManager = "cn=Manager"
infi = open(sys.argv[1], 'rt')

uid = ""

thisrec = {}

records = []

for i in infi:
    line = i.strip('\n')

    if line:
        if "dn:" in line:
            uid = line.split("uid=")[-1].split(',')[0].strip()
	    print uid
            if thisrec:
                records.append(thisrec)
            thisrec = {}
        else:
            attr = line.split(':')[0]
            val = line.split(':')[-1]

            if thisrec.get(attr, False):
                thisrec[attr].append(val.strip())
            else:
                thisrec[attr] = [val.strip()]

records.append(thisrec) # the last record

for data in records:
    user = data['uid'][0]
    emailAddress = "%s@%s" % (user, Domain)
    try:
        if not data['sn']:
            data['sn'] = ["-"]
    except:
        data['sn'] = ["-"]
    try:
        if not data['givenName']:
            data['givenName'] = [user.capitalize()]
    except:
        data['givenName'] = [user.capitalize()]

    # Acquire local SID
    SID = os.popen('net getlocalsid').read().strip('\n').split()[-1]

    # Construct NTLM hashes.
    (LM, NT) = tuple(os.popen('./ntlmgen/ntlm.pl %s' % (clearPassword)).read().strip('\n').split())

    # Acquire UID offset
    l = LDAP.createLDAPConnection(LDAPServer, 'o='+LDAPBase, LDAPManager, LDAPPass)
    dc = "%s,o=%s" % (LDAP.domainToDC(Domain), LDAPBase)
    domainData =  LDAP.getDomInfo(l, dc, SDomain)
    uidOffset =  int(domainData['uidNumber'][0])
    # Make RID
    SIDOffset = 2*uidOffset

    # Append user to Domain Users
    try:
        domainUsers = LDAP.getDomUsers(l, dc)
        newDomainUsers = copy.deepcopy(domainUsers)
        if not newDomainUsers.get('memberUid', None): # Very very new domain
            newDomainUsers['memberUid'] = []
        newDomainUsers['memberUid'].append(user)
        LDAP.modifyElement(l, 'cn=Domain Users,ou=Groups,'+dc, domainUsers, newDomainUsers)
    except:
        pass # User already in group

    # Increment UID for domain
    newDom = copy.deepcopy(domainData)
    newDom['uidNumber'] = [str(uidOffset+1)]
    try:
        LDAP.modifyElement(l, 'sambaDomainName=%s,%s,o=%s' %
            (SDomain, LDAP.domainToDC(Domain), LDAPBase), domainData, newDom)
    except:
        pass # User has a uid or something

    timeNow = str(int(time.time()))
    # LDAP template for SAMBA
    newRecord = {
        'sambaPrimaryGroupSID': [SID+"-"+str(1000+SIDOffset+1)],
        'sambaSID':             [SID+"-"+str(1000+SIDOffset)],
        'gidNumber':            ['513'],
        'uidNumber':            [str(uidOffset)],
        'sambaPasswordHistory': ['0000000000000000000000000000000000000000000000000000000000000000'],
        'sambaPwdMustChange':   ['2147483647'],
        'sambaPwdCanChange':    [timeNow],
        'sambaNTPassword':      [NT],
        'sambaLMPassword':      [LM],
        'gecos':                ['System User'],
        'sn':                   data['sn'],
        'givenName':            data['givenName'],
        'cn':                   ["%s %s" % (data['givenName'][0], data['sn'][0])],
        'o':                    [LDAPOrganisation],
        'objectClass':          ['top', 'inetOrgPerson', 'posixAccount', 'shadowAccount',
                                 'SambaSamAccount', 'thusaUser'],
        'loginShell':           ['/bin/bash'],
        'sambaPwdLastSet':      [timeNow],
        'sambaAcctFlags':       ['[U          ]'],
        'mailMessageStore':     [data['mailMessageStore'][0]],
        'mail':                 [emailAddress],
        'homeDirectory':        ['/home/%s' % user],
        'uid':                  [user],
        'employeeType':         []
    }


    newRecord['employeeType'] = data['employeeType']

    newRecord['accountStatus'] = data['accountStatus']

    if data.get('mailForwardingAddress', None):
        newRecord['mailForwardingAddress'] = data['mailForwardingAddress']

    if data.get('mailAlternateAddress', None):
        newRecord['mailAlternateAddress'] = data['mailAlternateAddress']

    newRecord['userPassword'] = ["{SHA}"+LDAP.hashPassword(clearPassword)]

    l = LDAP.createLDAPConnection(LDAPServer, 'o='+LDAPBase, LDAPManager, LDAPPass)
    dc = "ou=People,%s,o=%s" % (LDAP.domainToDC(Domain), LDAPBase)

    try:
        LDAP.addElement(l, 'uid=%s,%s' % (user, dc), newRecord)
    except Exception, L:
    	print "Failed to add", user
        print L
    # Send a mail to the luser to enable it...
    l = os.popen("echo 'Welcome to your new account, %s' | mail -s 'Welcome %s' %s" %
            (newRecord['cn'][0], newRecord['givenName'][0], newRecord['mail'][0])
        )

    # Create Home directory and restart NSCD
    #os.system('/etc/init.d/nscd restart')
    os.system('mkdir /home/%s' % (user))
    #os.system('chown %s:Domain\ Users /home/%s' % (user, user))
    #os.system('chown %s:Domain\ Users /var/lib/samba/profiles/%s' % (user, user))



