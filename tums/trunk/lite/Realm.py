""" Provides construction of the web interface servlet """
import sys

# Rev 1
sys.path.append('.')
from twisted.application import service, strports, internet
from twisted.web import server, static, resource, script
from twisted.internet import reactor, defer
from twisted.cred import portal, checkers, credentials, error
from twisted.python import failure

from nevow import inevow, rend, loaders, tags, vhost, appserver, static, guard, url
from zope.interface import implements, Interface
from websession import PersistentSessionWrapper

from Core import Auth, PageHelpers
import Core, Settings
from axiom.store import Store
from Pages import Index, Login, Menu

def noLogout():
    return None

class Realm:
    """ Realm
    Authentication realm implements checkers and redirects to the login page - handles passing the session data around.
    Called by createPortal.
    @ivar db: Tupple of C{AccessBroker} instances
    """
    implements(portal.IRealm)

    db = None

    def __init__(self, db):
        self.db = db

    #--------------------------------------#
    # Request avatar object from login     #
    #--------------------------------------#
    def requestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is inevow.IResource:
                if avatarId is checkers.ANONYMOUS:
                    # If we are not logged in then pass to the root page (login screen)
                    res = Login.Page()
                    res.realm = self
                    return (inevow.IResource, res, noLogout)
                else:
                    # on login pass to the default first page
                    res = Menu.Page(avatarId, self.db)
                    res.realm = self
                    return (inevow.IResource, res, res.logout)

        raise NotImplementedError, "Can't support that interface."

#--------------------------------------#
# Construct login Portal               #
#--------------------------------------#
def createPortal(db):
    """ createPortal
    Constructs our guarded realm and portal
    @param db: C{AccessBroker} instance
    """
    realm = Realm(db)
    porta = portal.Portal(realm)

    porta.registerChecker(checkers.AllowAnonymousAccess(), credentials.IAnonymous)
    checker = Auth.LDAPChecker(Settings.LDAPServer, Settings.LDAPManager, Settings.LDAPPass, Settings.LDAPBase)  # construct our database cred checker
    #checker = Auth.PlainChecker()
    porta.registerChecker(checker)

    return porta
#--------------------------------------#

#--------------------------------------#
# Construct session wrapper            #
#--------------------------------------#
def createResource(db):
    """ createResource
    returns a guarded session wrapper, passes a database pool
    @param db: tupple of C{AccessBroker} instances
    """
    #s = PersistentSessionWrapper(Store('tums.axiom'), createPortal(db))
    s = guard.SessionWrapper(createPortal(db))
    s.persistentCookies = True
    return s
#--------------------------------------#


#--------------------------------------#
# Deploy the system                    #
#--------------------------------------#
def deploy(db):
    """Creates an application service and guarded root
    @param db: C{AccessBroker} instance
    """
    guardSite = createResource(db)
    siteRoot = Index.Page(db)
    #siteRoot.putChild('vhost', vhost.VHostMonsterResource())
    siteRoot.putChild('auth', guardSite)
    site = appserver.NevowSite(siteRoot)

    site.context.remember(PageHelpers.TumsExceptionHandler(), inevow.ICanHandleException)

    return site

