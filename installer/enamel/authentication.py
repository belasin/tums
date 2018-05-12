from twisted.internet import reactor, defer, threads
from twisted.cred import portal, checkers, credentials, error
from twisted.python import failure
from zope.interface import implements
from axiom import userbase
import storage, types

UnauthorizedLogin = error.UnauthorizedLogin

class UsernamePasswordAvatar:
    def __init__(self, username = None, password = None, userId = 0):
        self.username = username
        self.password = password
        self.userId = userId

class DummyAuthenticator:
    """ A dummy authenticator which always returns a default avatar"""
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword,

    def __init__(self, enamel):
        self.enamel = enamel

    def handleAuthenticationResult(self, result, username, password):
        return self.enamel.avatar(username, password)

    def requestAvatarId(self, creds):
        return self.handleAuthenticationResult(None, creds.username, creds.password)

class DatabaseAuthenticator:
    """ A database authentication class. 
    Requires an Enamel Storage instance with an authenticateUser method which takes parameters of username and password 
    """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword, userbase.IPreauthCredentials,

    def __init__(self, enamel):
        self.enamel = enamel
        try:
            self.storage = storage.IStorage(enamel.storage)
            assert (isinstance(enamel.storage.authenticateUser, types.MethodType))
        except:
            print "[Enamel Error] DatabaseAuthenticator requires a Storage class with an authenticateUser method"
            raise 

    def handleAuthenticationResult(self, result, username, password):
        if result:
            return self.enamel.avatar(username, password)
        else:
            raise UnauthorizedLogin()

    def requestAvatarId(self, creds):
        if isinstance(creds, userbase.Preauthenticated):
            username = creds.username
            password = None
        else:
            username = creds.username
            password = creds.password or ""

        def authFailback(ohnoes):
            print globals()
            raise UnauthorizedLogin()

        def getHandler(result):
            return self.handleAuthenticationResult(result, username, password)

        return self.storage.authenticateUser(
            username, 
            password
        ).addCallbacks(getHandler, authFailback)

class LDAPAuthenticator:
    """ An LDAP credential checker """
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword, userbase.IPreauthCredentials,

    def __init__(self, enamel):
        self.authdn = enamel.ldapAuthDn
        self.password = enamel.ldapBindPassword
        self.ldapUrl = enamel.ldapAuthUrl
        self.enamel = enamel

    def authLDAP(self, username, password):
        import ldap, ldapurl
        ld = ldapurl.LDAPUrl(self.ldapUrl)

        ldapConnector = ldap.open(ld.hostport.split(':')[0])
        ldapConnector.protocol_version = ldap.VERSION3

        ldapConnector.simple_bind(self.authdn, self.password)
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ["userPassword"]
        if ld.filterstr:
            searchFilter = "(&(%s=%s)%s)" % (ld.attrs[0],username,ld.filterstr)
        else:
            searchFilter = "%s=%s" % (ld.attrs[0],username)

        try:
            ldap_result_id = ldapConnector.search(ld.dn, searchScope, searchFilter, retrieveAttributes)
            result_set = []
            while 1:
                result_type, result_data = ldapConnector.result(ldap_result_id, 0)
                if (result_data == []):
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set.append(result_data)
            if not result_set:
                return False

            return result_set[0][0][1]

        except ldap.LDAPError, e:
            print "[Enamel Error] Error in LDAP user lookup."
            print e
            return False

    def handleAuthenticationResult(self, result, username, password):
        ldapPass = result.get('userPassword', [''])[0]
        import ldappass
        passchecker = ldappass.UserPassword()

        if password == None:
            # handle preauth credentials ONLY if the password is a None type
            return self.enamel.avatar(username, "")

        if passchecker._compareSinglePassword(password, ldapPass):
            return self.enamel.avatar(username, password)
        else:
            raise UnauthorizedLogin()

    def requestAvatarId(self, creds):
        """ Called when a user logs in. Matches creds with the LDAP tree """
        def error(_):
            print "oops"
            raise UnauthorizedLogin()

        if isinstance(creds, userbase.Preauthenticated):
            username = creds.username
            password = None
        else:
            username = creds.username
            password = creds.password or ""

        def getHandler(result):
            return self.handleAuthenticationResult(result, username, password)

        return threads.deferToThread(
                self.authLDAP, 
                username, 
                password
            ).addCallbacks(getHandler, error)

