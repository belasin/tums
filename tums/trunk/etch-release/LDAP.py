import ldap
from ldap import modlist
import sha, binascii, copy

def createLDAPConnection(host, baseDN, user=None, password=None):
    ldapConnector = ldap.open(host)
    ldapConnector.protocol_version = ldap.VERSION3
    if user:
        ldapConnector.simple_bind("%s, %s" %(user, baseDN), password)
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

def retryCommand(fn, *args):
    for i in range(3):
        try:
            fn(*args)
            return 
        except Exception, e:
            print "Retrying... ", fn
    
    raise e

def modifyAttributes(ldapConnector, dn, attr):
    retryCommand(ldapConnector.modify_s, dn, [(ldap.MOD_REPLACE, k, v) for k,v in attr.items()])
    
def addAttribute(ldapConnector, dn, k,v):
    retryCommand(ldapConnector.modify_s, dn, [(ldap.MOD_ADD, k,v)])

def modifyElement(ldapConnector, dn, oldData, newData):
    retryCommand(ldapConnector.modify_s, dn, modlist.modifyModlist(oldData, newData))

def addElement(ldapConnector, dn, data):
    retryCommand(ldapConnector.add_s, dn, modlist.addModlist(data))

def domainToDC(dom):
    return 'dc='+',dc='.join(dom.split('.'))
