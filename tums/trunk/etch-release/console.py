#!/usr/bin/python
#
#  Vulani TUMS 
#  Copyright (C) Thusa Business Support (Pty) Ltd.
#  All rights reserved
#  
#  console.py - Console Startup Daemon.
#
from twisted.conch.manhole import ColoredManhole
from twisted.conch.insults import insults
from twisted.conch.telnet import TelnetTransport, TelnetBootstrapProtocol
from twisted.conch.manhole_ssh import ConchFactory, TerminalRealm

from twisted.internet import protocol,reactor
from twisted.application import internet, service
from twisted.cred import checkers, portal
import sys
sys.path.append('/usr/local/tcs/tums/')
import Settings
sys.path.append(Settings.BaseDir)
from Core import Auth, confparse, Utils
import os, re, datetime, pydoc

from Console import Help, Show, Set, Service

config = confparse.Config()

class TumsConsole(ColoredManhole):
    
    def __init__(self, *a, **kw):
        ColoredManhole.__init__(self, *a, **kw)
        #Define namespace and populate it with instances of the base commands
        self.namespace = {
            'help': Help.HelpHooker(config), #This needs to be changed
            'show': Show.Show(config),
            'config' : Set.Config(config),
            'service' : Service.Service(config),
        }
        """Thanks colin for the plugin stuff"""
        dirList = os.listdir("Console/plugins/")
        for pluginFileName in dirList:
            if ".py" == pluginFileName[-3:] and not "__init__" in pluginFileName:
                try: 
                    """File is therefore a valid .py file and should be loaded into memory"""
                    consolePlugin = __import__("Console.plugins."+pluginFileName.replace('.py',''),globals(), locals(), ['plugins']).Plugin(config)            
                    if len(consolePlugin.name) > 0:
                        """At this point we could add in some checks to see if the user should have access
                           however for the moment I am just going to hook the plugin directly into the subnamespace"""
                        [self.namespace[actionName].attachHook(consolePlugin) for actionName in self.namespace.keys()]
                        print "[Console] Loaded Plugin: %s(%s)" % (pluginFileName, consolePlugin.name)
                    else:
                        print "[Console] Invalid Plugin(name attribute is invalid):", pluginFileName
                        continue
                except Exception, e:                    
                    print "[Console] Invalid Plugin(%s): %s" % (e,pluginFileName)
                    continue
                    

    def lineReceived(self, line):
        params = []
        if ':' in line:
            par = line.split(':',1)[-1].split()
            lastQuote = ""
            for i in par:
                # If we encounter a quote then keep parsing untill the end of the quote
                if '"' in i and not lastQuote:
                    lastQuote = i.strip('"')
                    continue
                elif '"' in i and lastQuote:
                    lastQuote += ' '+i.strip('"')
                    i = lastQuote
                    lastQuote = ""
                elif lastQuote:
                    lastQuote += ' '+i
                    continue

                # wrap strings if there are any..
                try:
                    l = int(i)
                    params.append(i)
                except:
                    params.append('"%s"' % i.replace('"', '\\"'))

        com = line.split(':',1)[0].split()
        # Sanitise our input
        if com and com[0] not in self.namespace.keys():
            line = 'print "No such command: %s"' % line
        elif com:
            # Valid command
            line = '.'.join(com[:2])
            if com[2:]:
                line += '_'
                line += '_'.join(com[2:])

            if params:
                line += "(%s)" % ','.join(params)
            elif len(com)>1:
                line += "()"
        try:
            if com[1] == 'config':
                line = 'print "No such command: %s config"' % (com[0])
        except:
            pass

        more = self.interpreter.push(line)
        self.pn = bool(more)
        if self._needsNewline():
            self.terminal.nextLine()
        self.terminal.write(self.ps[self.pn])

def makeService(args):
    #checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(username="password", password="hi")
    csvc = internet.TCPServer(args['ssh'], genSSHProtocol(args))

    m = service.MultiService()
    #tsvc.setServiceParent(m)
    csvc.setServiceParent(m)
    return m

def genSSHProtocol(args):    
    checker = Auth.LDAPChecker(Settings.LDAPServer, Settings.LDAPManager, Settings.LDAPPass, Settings.LDAPBase) 
    f = protocol.ServerFactory()
    f.protocol = lambda: TelnetTransport(TelnetBootstrapProtocol,
                                         insults.ServerProtocol,
                                         args['protocolFactory'],
                                         *args.get('protocolArgs', ()),
                                         **args.get('protocolKwArgs', {}))
    #tsvc = internet.TCPServer(args['telnet'], f)

    def chainProtocolFactory():
        return insults.ServerProtocol(
            args['protocolFactory'],
            *args.get('protocolArgs', ()),
            **args.get('protocolKwArgs', {}))

    rlm = TerminalRealm()
    rlm.chainedProtocolFactory = chainProtocolFactory
    ptl = portal.Portal(rlm, [checker])
    f = ConchFactory(ptl)
    return f

application = service.Application("TUMS Console")

makeService({'protocolFactory': TumsConsole,
             'protocolArgs': (None,),
             #'telnet': 6023,
             'ssh': 6022}).setServiceParent(application)
            
if __name__ == '__main__':        
            
    ## TwistD bootstrap code
    nodaemon = 0
    log = '/var/log/tums-console.log'
    if len(sys.argv) > 1:
        if sys.argv[1] == "-n":
            nodaemon = 1
            log = None

    Utils.startTwisted(application, Settings.BaseDir, nodaemon, log, Settings.BaseDir, pidfile='/var/run/tums-console.pid')
