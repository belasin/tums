# A bot for connecting to an IRC server and giving information where XMLRPC fails

from twisted.words.protocols import irc
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, defer,  threads, utils, protocol
from twisted.internet.defer import deferredGenerator, waitForDeferred as wait
import Settings

server = 'za.shadowfire.org'

class ThebeBot(irc.IRCClient):
    nickname = Settings.LDAPBase.lower()
    realname = 'Thusa Bot'
    username = 'thebe'
    versionName = 'Keep away - Bot belongs to Karnaugh'

    chan = '#thusa'
    ready = False
    chanNames = {}

    def __init__(self, *args, **kwargs):
        self.cmdFns = {
            'ps':self.checkPS,
            'aptitude':self.aptitude,
            'emerge':self.emerge,
            'execute':self.execute,
        }

    def execute(self, args):
        print "Got execute command"
        def Ok(_):
            output = _.split('\n')
            for ln in output[-10:]:
                l = ln.strip()
                if l:
                    self.msg(self.chan, '\x0312[EXEC]\x03 \x038 %s\x03' % l)

            return None

        def Fail(_):
            self.msg(self.chan, '\x0312[EXEC]\x03 \x039Execution error\x03')
            return None

        return utils.getProcessOutput(args[0], args[1:], errortoo=1).addCallbacks(Ok, Fail)
        

    def emerge(self, args):
        def Ok(_):
            output = _.split('\n')
            for ln in output[-10:]:
                l = ln.strip()
                if l:
                    self.msg(self.chan, '\x0312[EMERGE]\x03 \x038 %s\x03' % l)

            return None

        def Fail(_):
            self.msg(self.chan, '\x0312[EMERGE]\x03 \x039EMERGE Error\x03')
            return None

        return utils.getProcessOutput('/usr/bin/emerge', args, errortoo=1).addCallbacks(Ok, Fail)
 
    def aptitude(self, args):
        def Ok(_):
            output = _.split('\n')
            for ln in output[-10:]:
                l = ln.strip()
                if l:
                    self.msg(self.chan, '\x0312[APT]\x03 \x03 8%s\x03' % l)

            return None

        def Fail(_):
            self.msg(self.chan, '\x0312[APT]\x03 \x039 APT Error\x03')
            return None

        return utils.getProcessOutput('/usr/bin/aptitude', args, errortoo=1).addCallbacks(Ok, Fail)
 
    def checkPS(self, args):
        def Ok(_):
            output = _.split('\n')
            for ln in output:
                print ln
                l = ln.strip()
                if args[0] in l:
                    self.msg(self.chan, '\x0312[PS]\x03 \x038 %s\x03' % l)

            return None

        def Fail(_):
            self.msg(self.chan, '\x0312[PS]\x03 \x039PS Error\x03')
            return None

        return utils.getProcessOutput('/bin/ps', ['aux'], errortoo=1).addCallbacks(Ok, Fail)
    
    def privmsg(self, user, channel, message):
        nick = user.split('!')[0]
        if self.chan in channel:
            authorised = False
            for i in self.chanNames[channel]:
                if '@'+nick in i:
                    authorised = True

            if authorised:
                if (self.nickname+':' == message.split()[0]) or ('all:' == message.split()[0]):
                    cmds = message.split()[1:]
                    if cmds[0].lower() in self.cmdFns:
                        self.cmdFns[cmds[0].lower()](cmds[1:])

    def irc_MODE(self, prefix, params):
        if params[0] == self.chan:
            if ('o' in params[1]) and ('+' in params[1]):
                self.chanNames[self.chan].append('@'+params[2])
                print params[2], "is now an op"

    def irc_RPL_NAMREPLY(self, p, r):
        for i in r[3].split(' '):
            if not i == "":
                self.chanNames[r[2]].append(i)

    def irc_RPL_ENDOFNAMES(self, p, r):
        print "channel synced"

    def updateNames(self, channel):
        self.sendLine('NAMES %s' % channel)

    def joined(self, channel):
        print "Joined ", channel
        self.chanNames[channel] = []
        self.updateNames(channel)
        self.ready = True

    def signedOn(self):
        print "Bot Active"
        self.mode(self.nickname, True, '+B')
        self.join(self.chan)


class tbFactory(ClientFactory):
    protocol = ThebeBot
    def clientConnectionFailed(self, connector, reason):
        print "efg - ", repr(reason)
        reactor.callLater(5, connector.connect)

    def clientConnectionLost(self, connector, reason):
        print "Efg!! - ", repr(reason)
        reactor.callLater(5, connector.connect)

