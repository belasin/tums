import sys
sys.path.append('/usr/local/tcs/tums')
import ldap, time
from ldap import modlist
import sha, binascii, copy, random
from Core import Utils

def retryCommand(fn, *args):
    for i in range(10):
        try:
            k = fn(*args)
            return k
        except Exception, e:
            print "Retrying... ", fn
    
    raise e

def createLDAPConnection(host, baseDN, user=None, password=None):
    ldapConnector = ldap.open(host)
    ldapConnector.protocol_version = ldap.VERSION3
    if user:
        retryCommand(ldapConnector.simple_bind, "%s, %s" %(user, baseDN), password)
    return ldapConnector
                    
def searchTree(ldapConnector, baseDN, searchFilter = '', retrieveAttributes = ['']):
    searchScope = ldap.SCOPE_SUBTREE
    try:
        ldap_result_id = ldapConnector.search(baseDN, searchScope, searchFilter, retrieveAttributes)
        result_set = []
        while 1:
            result_type, result_data = ldapConnector.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)

    except ldap.LDAPError, e:
        print "LDAP error", e
        pass # error
        result_set = []
 
    return result_set

def getUsers(ldapConnector, baseDN, searchFilter = 'uid=*', retrieveAttributes = ['*']):
    return [person[0][1] for person in 
        searchTree(ldapConnector, baseDN, searchFilter, retrieveAttributes)]

def getDomInfo(ldapConnector, baseDN, dom = '', retrieveAttributes = ['*']):
    return [i for i in 
        searchTree(ldapConnector, baseDN, 'sambaDomainName='+dom, retrieveAttributes)][0][0][1]

def getDomUsers(ldapConnector, baseDN, dom = '', retrieveAttributes = ['*']):
    return [i for i in
        searchTree(ldapConnector, 'ou=Groups,'+baseDN, 'cn=Domain Users', retrieveAttributes)][0][0][1]

def getGroup(ldapConnector, baseDN, group='Domain Users', retrieveAttributes=['*']):
    return [i for i in
        searchTree(ldapConnector, 'ou=Groups,'+baseDN, 'cn='+group, retrieveAttributes)][0][0][1]       

def getGroups(ldapConnector, baseDN):
    return [(''.join(i[0][1]['cn'][0].split()), i[0][1]['cn'][0]) for i in 
        searchTree(ldapConnector, 'ou=Groups,'+baseDN, 'cn=*', [])]

def getGroupMembers(ldapConnector, baseDN, group='Domain Users', retrieveAttributes=['memberUid']):
    sr = searchTree(ldapConnector, 'ou=Groups,'+baseDN, 'cn='+group, retrieveAttributes)
    if sr:
        return sr[0][0][1].get(retrieveAttributes[0], [])
    else:
        return []

def isMemberOf(ldapConnector, baseDN, uid, group='Domain Users', retrieveAttributes=['memberUid']):
    sr = searchTree(ldapConnector, 'ou=Groups,'+baseDN, 'cn='+group, retrieveAttributes)
    if sr:
        members = sr[0][0][1].get(retrieveAttributes[0], [])
        return uid in members
    else:
        return False

def makeMemberOf(ldapConnector, baseDN, uid, group='Domain Users'):
    domainUsers = getGroup(ldapConnector, baseDN, group)
    if not uid in domainUsers.get('memberUid', []):
        newDomainUsers = copy.deepcopy(domainUsers)
        if not domainUsers.get('memberUid', None):
            # empty group
            newDomainUsers['memberUid'] = [uid]
        else:
            newDomainUsers['memberUid'].append(uid)
        modifyElement(ldapConnector, 'cn='+group+',ou=Groups,'+baseDN, domainUsers, newDomainUsers)

def makeNotMemberOf(ldapConnector, baseDN, uid, group='Domain Users'):
    domainUsers = getGroup(ldapConnector, baseDN, group)
    if uid in domainUsers.get('memberUid', []):
        newDomainUsers = copy.deepcopy(domainUsers)
        del newDomainUsers['memberUid'][newDomainUsers['memberUid'].index(uid)]
        modifyElement(ldapConnector, 'cn='+group+',ou=Groups,'+baseDN, domainUsers, newDomainUsers)            

def hashPassword(passwd):
    return binascii.b2a_base64(sha.new(passwd).digest())[:-1]

def deleteElement(ldapConnector, dn):
    #deleteDN = "uid=anyuserid, ou=Customers, ou=Sales, o=anydomain.com"
    try:
        ldapConnector.delete_s(dn)
    except ldap.LDAPError, e:
        print e
        pass # nothing to delete

def modifyAttributes(ldapConnector, dn, attr):
    retryCommand(ldapConnector.modify_s, dn, [(ldap.MOD_REPLACE, k, v) for k,v in attr.items()])
    
def addAttribute(ldapConnector, dn, k,v):
    retryCommand(ldapConnector.modify_s, dn, [(ldap.MOD_ADD, k,v)])

def modifyElement(ldapConnector, dn, oldData, newData):
    retryCommand(ldapConnector.modify_s, dn, modlist.modifyModlist(oldData, newData))

def renameElement(ldapConnector, dn, newDn):
    retryCommand(ldapConnector.rename_s, dn, newDn)

def addElement(ldapConnector, dn, data):
    retryCommand(ldapConnector.add_s, dn, modlist.addModlist(data))

def domainToDC(dom):
    return 'dc='+',dc='.join(dom.split('.'))


class LDAPConnector(object):
    def __init__(self, domain, sysconf, server=None, baseDN=None, bindDN=None, bindPW = None, **kw):
        # Get settings
        try: 
            import Settings
            self.server = Settings.LDAPServer
            self.baseDN = 'o='+Settings.LDAPBase
            self.bindDN = Settings.LDAPManager
            self.bindPW = Settings.LDAPPass
            self.smbDomain = Settings.SMBDomain
            self.ldapOrg = Settings.LDAPOrganisation
            self.defaultDomain = Settings.defaultDomain
        except:
            self.server = server
            self.baseDN = baseDN
            self.bindDN = bindDN
            self.bindPW = bindPW
            self.smbDomain = kw.get('smbDomain')
            self.ldapOrg = kw.get('LDAPOrganisation')
            self.defaultDomain = kw.get('defaultDomain')

        self.domain = domain
        self.baseDC = "%s,%s" % (domainToDC(self.domain), self.baseDN)
        self.userDN = "ou=People,%s" % self.baseDC 
        self.sysconf = sysconf
        # Know if we are acting on the default domain
        self.sambaDN = self.domain == self.defaultDomain

    def connect(self):
        self.ldapConnector = createLDAPConnection(self.server, self.baseDN, self.bindDN, self.bindPW)

    def disconnect(self):
        self.ldapConnector.unbind_s()

    def getDomainData(self):
        """ Get all the useful bits of domain data """
        self.connect()
        domainData  = getDomInfo(self.ldapConnector, self.baseDC, self.smbDomain)
        domainUsers = getDomUsers(self.ldapConnector, self.baseDC)

        self.disconnect()

        nextUID = int(domainData['uidNumber'][0])

        return {
            'memberUid': domainUsers.get('memberUid', []), 
            'sambaSID' : domainData['sambaSID'][0], 
            'uidNumber': nextUID, 

            'sambaPrimaryGroupSID': "%s-%s" % (domainData['sambaSID'][0], 1001 + (nextUID*2)),
            'sambaSID':             "%s-%s" % (domainData['sambaSID'][0], 1000 + (nextUID*2))
        }, domainUsers, domainData

    def ldapify(self, inDict):
        # Every item needs to be in a list
        nd = {}
        for k,v in inDict.items():
            if isinstance(v, list):
                nd[k] = v
            else:
                if isinstance(v, unicode):
                    # Encode all our unicode as utf-8
                    v = v.encode('utf-8', 'replace')

                if not isinstance(v, str):
                    # LDAP needs everything as a string (bleh)
                    v = str(v)

                # Store as a list
                nd[k] = [v]

        return nd

    def validateSettings(self, data, newRecord):
        """ Validates a form into the ldap record. Must be interchangable between add and edit """
        user = data['userSettings.uid'].encode('ascii', 'replace').lower()
        newRecord['uid'] =  user

        # Set employeeType values
        empVals = []
        if data.get('userPermissions.employeeType'):
            empVals.append('squid')

        if data.get('userPermissions.tumsAdmin', None):
            # Tums Admin overrides every other setting
            empVals.append('tumsAdmin')
        else:
            if data.get('userPermissions.tumsUser', None):
                tuenc = 'tumsUser[%s]' % ','.join(data['userPermissions.tumsUser'])
                empVals.append(tuenc.encode("ascii", "replace"))

            if data.get('userPermissions.tumsReports', None):
                empVals.append('tumsReports')

        if empVals:
            newRecord['employeeType'] = empVals
        elif newRecord.get('employeeType'):
            del newRecord['employeeType']

        # Account is active
        if data.get('userPermissions.accountStatus'):
            newRecord['accountStatus'] = 'active'
        elif newRecord.get('accountStatus'):
            del newRecord['accountStatus']

        # Mail forwarding addresses
        mFA = []
        for i in xrange(10):
            # Reap data into list
            if data.get('mailSettings.mailForwardingAddress%s' % i):
                ad = data['mailSettings.mailForwardingAddress%s' % i].replace(' ', '').replace('\r','')
                if ad:
                    mFA.append(ad)
        if mFA:
            newRecord['mailForwardingAddress'] = [ le.encode("ascii", "replace") for le in mFA ]
        elif newRecord.get('mailForwardingAddress'):
            del newRecord['mailForwardingAddress']


        # Mail aliases
        mAA = []
        for i in xrange(10):
            # Reap data into list
            if data.get('mailSettings.mailAlternateAddress%s' % i):
                ad = data['mailSettings.mailAlternateAddress%s' % i].replace(' ', '').replace('\r','')
                if ad:
                    mAA.append(ad)
        if mAA:
            newRecord['mailAlternateAddress'] = [ le.encode("ascii", "replace").strip('\r') for le in mAA ]
        elif newRecord.get('mailAlternateAddress'):
            del newRecord['mailAlternateAddress']

        # Password
        if data['userSettings.userPassword']:
            newRecord['userPassword'] = "{SHA}"+hashPassword(data['userSettings.userPassword'].encode("ascii", "replace"))
            
            if self.sambaDN:
                newRecord['sambaPwdLastSet'] = int(time.time())
                clearPassword = data['userSettings.userPassword'].encode('ascii', 'replace')
                newRecord['sambaLMPassword'] = Utils.createLMHash(clearPassword)
                newRecord['sambaNTPassword'] = Utils.createNTHash(clearPassword)
                if newRecord.get('sambaPwdMustChange'):
                    del newRecord['sambaPwdMustChange']

        sn = data.get('userSettings.sn') or '-'
        gn = data.get('userSettings.givenName') or user.capitalize()

        newRecord['sn']         = sn
        newRecord['givenName']  = gn
        newRecord['cn']         = "%s %s" % (gn, sn)

        # FTP data
        if data.get('userAccess.ftpGlobal'):
            ftp = self.sysconf.FTP
            if ftp.get('globals', None):
                if newRecord['uid'] not in ftp['globals']:
                    ftp['globals'].append(user)
            else:
                ftp['globals'] = [user]

            self.sysconf.FTP = ftp
        else:
            ftp = self.sysconf.FTP
            newGlobals = []
            globals = ftp.get('globals', [])
            for id in globals:
                if id != user:
                    newGlobals.append(id)
            ftp['globals'] = newGlobals
            self.sysconf.FTP = ftp
        
        if self.sambaDN:
            newRecord['loginShell'] = data.get('userAccess.ftpEnabled', False) and '/bin/bash' or '/bin/false'
            newRecord['homeDirectory'] = '/home/%s' % user

        emailAddress = str("%s@%s" % (user, self.domain))
        newRecord['mailMessageStore'] = '/var/spool/mail/' + emailAddress
        newRecord['mail']             = emailAddress

    def addUserToSmbDomain(self, data):
        """ Add a user to a samba domain""" 
        # Hall out some data
        relevantData, domainUsers, domainData = self.getDomainData()
        timeNow = int(time.time())

        if data['userSettings.userPassword']:
            clearPassword = data['userSettings.userPassword'].encode('ascii', 'replace')
        else:
            clearPassword = sha.sha("%s%s%s" % (random.randint(1,2000), time.time(), random.randint(1, 4000))).hexdigest()
            data['userSettings.userPassword'] = clearPassword
            
        LM, NT = (Utils.createLMHash(clearPassword), Utils.createNTHash(clearPassword))

        # Grab some data
        user = data['userSettings.uid'].encode('ascii', 'replace').lower()

        # SMB template 
        newRecord = {
            'sambaPrimaryGroupSID': relevantData['sambaPrimaryGroupSID'],
            'sambaSID':             relevantData['sambaSID'],
            'uidNumber':            relevantData['uidNumber'],
            'gidNumber':            513,
            'sambaPasswordHistory': '0000000000000000000000000000000000000000000000000000000000000000',
            'sambaPwdMustChange':   2147483647,
            'sambaPwdCanChange':    timeNow,
            'sambaNTPassword':      NT,
            'sambaLMPassword':      LM,
            'gecos':                'System User',
            'o':                    self.ldapOrg,
            'objectClass':          ['top', 'inetOrgPerson', 'posixAccount', 'shadowAccount',
                                     'SambaSamAccount', 'thusaUser'],
            'sambaAcctFlags':       '[U          ]',
            'sambaPwdLastSet':      timeNow,

            # set this later..
            'employeeType':         []
        }

        self.validateSettings(data, newRecord)
        print self.ldapify(newRecord)
        # Add user element
        self.connect()
        addElement(self.ldapConnector, 'uid=%s,%s' % (user, self.userDN), self.ldapify(newRecord))

        # Add user to domain group if not already there
        if user not in domainUsers.get('memberUid'):
            newDomainUsers = copy.deepcopy(domainUsers)
            if not newDomainUsers.get('memberUid'):
                newDomainUsers['memberUid'] = [user]
            else:
                newDomainUsers['memberUid'].append(user)
            modifyElement(self.ldapConnector, 'cn=Domain Users,ou=Groups,'+self.baseDC, domainUsers, newDomainUsers)

        # increment nextUid
        newDom = copy.deepcopy(domainData)
        newDom['uidNumber'] = [str(relevantData['uidNumber']+1)]
        modifyElement(self.ldapConnector, 'sambaDomainName=%s,%s' % (self.smbDomain, self.baseDC), domainData, newDom)
    
        # Disconnect ourselves.
        self.disconnect()

        # Return the record we have added
        return self.ldapify(newRecord)

    def addUserToStandardDomain(self, data):
        """ Add a user to a normal domain """
        # Grab some data
        user = data['userSettings.uid'].encode('ascii', 'replace').lower()
        emailAddress = str("%s@%s" % (user, self.domain))

        if data['userSettings.userPassword']:
            clearPassword = data['userSettings.userPassword'].encode('ascii', 'replace')
        else:
            clearPassword = sha.sha("%s%s%s" % (random.randint(1,2000), time.time(), random.randint(1, 4000))).hexdigest()
            data['userSettings.userPassword'] = clearPassword

        newRecord = {
            'o':                self.ldapOrg,
            'objectClass':      ['top', 'inetOrgPerson', 'thusaUser'],
            'employeeType':     []
        }

        self.validateSettings(data, newRecord)

        # Add user element
        self.connect()
        addElement(self.ldapConnector, 'uid=%s,%s' % (user, self.userDN), self.ldapify(newRecord))
        # Disconnect ourselves.
        self.disconnect()

        # Return the record we have added
        return self.ldapify(newRecord)

    def addUser(self, data):
        """ Add a user to this domain """
        
        # Is this a samba domain?
    
        if self.sambaDN:
            return self.addUserToSmbDomain(data)
        else:
            return self.addUserToStandardDomain(data)

    def getUser(self, username):
        self.connect()
        un = getUsers(self.ldapConnector, self.userDN, 'uid=' + username)[0]
        self.disconnect()

        return un

    def renameUser(self, oldusername, newusername):
        self.connect()
        renameElement(self.ldapConnector, 'uid=%s,%s' % (oldusername, self.userDN), 'uid=%s' % newusername)
        self.disconnect()

    def modifyUser(self, username, data):
        user = data['userSettings.uid'].encode('ascii', 'replace').lower()

        if user != username:
            # User renamed
            self.renameUser(username, user)
            username = user

        oldRecord = self.getUser(username)
        print oldRecord
        newRecord = copy.deepcopy(oldRecord)
        
        self.validateSettings(data, newRecord)

        self.connect()
        modifyElement(self.ldapConnector, 'uid=%s,%s' % (username, self.userDN), oldRecord, self.ldapify(newRecord))
        self.disconnect()

        return oldRecord, self.ldapify(newRecord)
