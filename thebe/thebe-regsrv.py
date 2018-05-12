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
from Pages import Registration

from lib import rrd, system
# Construct a message handler

DEBUG = False
from OpenSSL import SSL

class ServerContextFactory:
    """ Factory for SSL context generation, see genkey.sh for generating
        OpenSSL certificates. """
    def getContext(self):
        """Create an SSL context."""
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file(Settings.BaseDir + '/server.pem')
        ctx.use_privatekey_file(Settings.BaseDir + '/privkey.pem')
        return ctx

class ThebeWeb(enamel.Enamel):
    """ Thebe Web management frontend """
    indexPage = Registration.Index
    
    storage = Database.ThebeStorage('mysql://thebe:thebe@localhost/thebe')
    anonymousAccess = True
    server = servers.TwistedWeb
    port = 8002

    vhostEnable = True

    # Our custom stuff
    Settings = Settings

IThebeWeb = ThebeWeb()

deployment.run('thebe-regsvr', [ 
    IThebeWeb, 
], pidLoc="./")

