from twisted.mail import imap4
from twisted.internet import protocol, ssl, defer, stdio, reactor
from twisted.protocols import basic


class SimpleIMAP4Client(imap4.IMAP4Client):
    greetDeferred = None

    def __init__(self, avatarId, *a, **kw):
        self.avatarId = avatarId
        imap4.IMAP4Client.__init__(self, *a, **kw)
    
    def serverGreeting(self, caps):
        self.serverCapabilities = caps
        if self.greetDeferred is not None:
            d, self.greetDeferred = self.greetDeferred, None
            d.callback(self)

    def fetchSpecific(self, messages, uid=0, headerType=None, headerNumber=None, headerArgs=None, peek=None, offset=None, length=None):

        fmt = '%s (FLAGS BODY%s[%s%s%s]%s)'

        if headerNumber is None:
            number = ''
        elif isinstance(headerNumber, types.IntType):
            number = str(headerNumber)
        else:
            number = '.'.join(headerNumber)
        if headerType is None:
            header = ''
        elif number:
            header = '.' + headerType
        else:
            header = headerType
        if header:
            if headerArgs is not None:
                payload = ' (%s)' % ' '.join(headerArgs)
            else:
                payload = ' ()'
        else:
            payload = ''
        if offset is None:
            extra = ''
        else:
            extra = '<%d.%d>' % (offset, length)
        fetch = uid and 'UID FETCH' or 'FETCH'
        cmd = fmt % (messages, peek and '.PEEK' or '', number, header, payload, extra)
        d = self.sendCommand(imap4.Command(fetch, cmd, wantResponse=('FETCH',)))
        d.addCallback(self.__cbFetchSpecific)
        return d

    def __cbFetchSpecific(self, (lines, last)):
        info = {}
        for line in lines:
            parts = line.split(None, 2)
            if len(parts) == 3:
                if parts[1] == 'FETCH':
                    try:
                        id = int(parts[0])
                    except ValueError:
                        raise imap4.IllegalServerResponse, line
                    else:
                        info[id] = imap4.parseNestedParens(parts[2])
        return info


class SimpleIMAP4ClientFactory(protocol.ClientFactory):
    usedUp = False

    protocol = SimpleIMAP4Client

    def __init__(self, avatarId, onConn):
        self.ctx = ssl.ClientContextFactory()
        
        self.avatarId = avatarId
        self.onConn = onConn

    def buildProtocol(self, addr):
        assert not self.usedUp
        self.usedUp = True
        
        p = self.protocol(self.avatarId, self.ctx)
        p.factory = self
        p.greetDeferred = self.onConn

        auth = imap4.CramMD5ClientAuthenticator(self.avatarId.username)
        p.registerAuthenticator(auth)
        
        return p
    
    def clientConnectionFailed(self, connector, reason):
        d, self.onConn = self.onConn, None
        d.errback(reason)

class IMAPClient(object):   
    def __init__(self, avatar):
        self.proto = None
        self.avatar = avatar

    def getFolder(self, folder):
        return self.proto.select(folder)

    def getMail(self, start, end="*", **kw):
        range = "%s:%s" % (start, end)
        return self.proto.fetchSpecific(range, peek=True,**kw)

    def markRead(self, mail):
        return self.proto.setFlags('%s:%s' % (mail,mail), ['\\Seen'])

    def delete(self, mail):
        def expunge(*a):
            return self.proto.expunge()
        return self.proto.setFlags('%s:%s' % (mail,mail), ['\\Deleted']).addBoth(expunge)

    def getFolders(self, *a):
        if not self.proto:
            return self.connect().addBoth(self.getFolders)

        def gotFolders(lines):
            fTree = {}

            lines.sort()

            for state, root, path in lines:
                segs = path.split('.')

                dcPointer = fTree
                for i in segs:
                    
                    if not i in dcPointer:
                        dcPointer[i] = {}
                    # Shift pointer
                    dcPointer = dcPointer[i]
            return fTree

        return self.proto.list("", "*").addBoth(gotFolders)

    def auth(self, proto):
        self.proto = proto
        def finished(ok):
            return ok

        return proto.login(proto.avatarId.username, proto.avatarId.password).addCallback(finished)

    def disconnect(self):
        if self.proto:
            self.proto.transport.loseConnection()

    def connect(self, host='127.0.0.1'):
        ocd = defer.Deferred().addCallback(self.auth)
        factory = SimpleIMAP4ClientFactory(self.avatar, ocd)
        c = reactor.connectTCP(host, 143, factory)

        return ocd
