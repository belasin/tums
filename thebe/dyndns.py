#!/usr/bin/python
from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql
import enamel
import cPickle, time, os

# Twisted extras
from twisted.internet import reactor

# Our stuff
import Settings, Database

# Pages
from Pages import Index

class ThebeAvatar:
    def __init__(self, username = "", password = "", id = 0, gids = [0] ):
        print "Got UID", id
        self.uid = id
        self.gids = gids
        self.username = username

class ThebeAuth(authentication.DatabaseAuthenticator):
    def handleAuthenticationResult(self, result, username, password):
        print result, username, password
        def gotGids(gid):
            # Get the gid
            print gid
            if gid:
                gids = [i[2] for i in gid]
            else:
                # Set -1 here if the user is not in any group at all - we can't
                # assume that they are 1 (Thusa Group)
                gids = [0]
            return ThebeAvatar(username, password, result[0], gids)
        
        def gotBusted(r):
            print r
            print "Yikes.."
            return ThebeAvatar(username, password, result[0], [-1])

        if result:
            print "Hello!"
            return self.enamel.storage.getGids(result[0]).addCallbacks(gotGids, gotBusted)
        else:
            raise authentication.UnauthorizedLogin()


class DynDNS(enamel.Enamel):
    """ Thebe Web management frontend """
    indexPage = Index.Index
    #loginPage = Index.Login
    storage = Database.ThebeStorage('mysql://thebe:thebe@localhost/thebe')
    #authenticator = ThebeAuth 
    anonymousAccess = True
    server = servers.TwistedWeb
    port = 8001

    vhostEnable = True

    Settings = Settings
IDynDNS = DynDNS()

deployment.run('dyndns', [ 
    IDynDNS, 
], pidLoc="./")

