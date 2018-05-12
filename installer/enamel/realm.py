""" Provides construction of the web interface servlet """
import sys
from twisted.application import service, strports, internet
from twisted.web import server, static, resource, script
from twisted.internet import reactor, defer
from twisted.cred import portal, checkers, credentials, error
from twisted.python import failure
from nevow import inevow, rend, loaders, tags, vhost, appserver, static, guard, url
from zope.interface import implements, Interface

from websession import PersistentSessionWrapper

import authentication

def noLogout():
    return None

class Realm(object):
    """ Realm
    Authentication realm implements checkers and redirects to the login page - handles passing the session data around.
    Called by createPortal.
    @ivar enamel: C{Enamel} instance
    """
    implements(portal.IRealm)

    def __init__(self, enamel):
        self.enamel = enamel

    # Request avatar object from login
    def requestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is inevow.IResource:
                if avatarId is checkers.ANONYMOUS:
                    if self.enamel.anonymousAccess:
                        avatarId = self.enamel.avatar()
                        res = self.enamel.indexPage(avatarId, self.enamel)
                    else:
                        res = self.enamel.loginPage(None, self.enamel)
                    res.realm = self
                    return (inevow.IResource, res, noLogout)
                else:
                    # on login pass to the default first page
                    res = self.enamel.indexPage(avatarId, self.enamel)
                    res.realm = self
                    return (inevow.IResource, res, res.logout)

        raise NotImplementedError, "Can't support that interface."

def createPortal(enamel):
    """ createPortal
    Constructs our guarded realm and portal
    @param enamel: C{Enamel} instance
    """
    realm = Realm(enamel)
    porta = portal.Portal(realm)

    porta.registerChecker(checkers.AllowAnonymousAccess(), credentials.IAnonymous)
    porta.registerChecker(enamel.authenticator(enamel))

    return porta

from axiom.store import Store
class BlankStore:
    def __init__(self):
        self.store = Store('enamel.axiom')

def createResource(enamel):
    """ createResource
    returns a guarded session wrapper, passes a database pool
    @param enamel: C{Enamel} instance
    """
    s = PersistentSessionWrapper(BlankStore().store, createPortal(enamel), appname=enamel.parentName)
    #s = guard.SessionWrapper(createPortal(enamel))
    #s.persistentCookies = True
    return s

class VhostFakeRoot:
    """
    I am a wrapper to be used at site root when you want to combine 
    vhost.VHostMonsterResource with nevow.guard. If you are using guard, you 
    will pass me a guard.SessionWrapper resource.
    """
    implements(inevow.IResource)
    def __init__(self, wrapped):
        self.wrapped = wrapped
    
    def renderHTTP(self, ctx):
        return self.wrapped.renderHTTP(ctx)
        
    def locateChild(self, ctx, segments):
        """Returns a VHostMonster if the first segment is "vhost". Otherwise
        delegates to the wrapped resource."""
        if segments[0] == "vhost":
            return vhost.VHostMonsterResource(), segments[1:]
        else:
            return self.wrapped.locateChild(ctx, segments)

class Enamel(object):
    parentName = "enamelApp"
    anonymousAccess = True
    vhostEnable = False
    storage = None

    authenticator = None
    avatar = authentication.UsernamePasswordAvatar

    def __init__(self):
        if not self.anonymousAccess:
            try:
                assert(issubclass(self.loginPage, rend.Page))
            except:
                print "[Enamel Error] You must have a loginPage instance without anonymousAccess"
                raise 
        try:
            assert(issubclass(self.indexPage, rend.Page))
        except:
            print "[Enamel Error] You need an indexPage instance"
            raise

    def site(self):
        """ Returns a NevowSite instance for this application """

        # If we have an authenticator then use it, or else just return the index.
        # XXX Change this so that we don't really need an authenticator to provide anonymous session
        if not self.authenticator:
            # Use the dummy authenticator so we always have a realm
            self.authenticator = authentication.DummyAuthenticator

        sessionWrapper = createResource(self)

        if self.vhostEnable:
            siteRoot = VhostFakeRoot(sessionWrapper)
        else:
            siteRoot = sessionWrapper

        site = appserver.NevowSite(siteRoot)

        return (site, )

