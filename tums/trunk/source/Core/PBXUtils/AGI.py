from Core import confparse
from twisted.internet import defer
import hashlib

sysconf = confparse.Config()

def authFactory(agi):
    auth = Authenticate(sysconf)
    return auth(agi)

class Authenticate(object):
    """Provides an authentication system useable for pin dialing"""
    agi = None
    sysconf = None

    def __init__(self, sysconf):
        self.sysconf = sysconf

    def __call__(self, agi):
        self.agi = agi
        return self.start()

    def handlError(self, err, message = ""):
        if message:
            message = " " + message
        print "[AGIError(%s)] %s%s" % (
            self.agi.variables['agi_channel'], 
            message,
            err.getTraceback())
        self.agi.finish()

    def start(self):
        return self.agi.answer().addCallback(self.onAnswered).addErrback(self.handlError)

    @defer.inlineCallbacks
    def onAnswered(self, resultLine):
        username = None
        self.CID = yield self.agi.getVariable("CALLERID(num)")
        audiofile = "agent-pass"
        for i in range(0,3):
            res = yield self.agi.getData(audiofile,5,10)
            if not res[1]:
                if "*" not in res[0]:
                    cid = self.CID
                    passw = res[0]
                else:
                    cid, passw = res[0].split("*",1)
                username = self.validateUser(cid, passw)
            if username:
                break
            else:
                audiofile = "auth-incorrect"
                #yield self.agi.streamFile("auth-incorrect")
        if not username:
            yield self.agi.streamFile("vm-goodbye")
            yield self.agi.hangup()
            yield self.agi.finish()
        else:
            yield self.agi.setVariable("__AUTHUSER", username)
            yield self.agi.finish()

    def validateUser(self, cid, passw):
        hash = hashlib.new("md5", "%s*%s" % (cid, passw)).hexdigest()
        passFile = open('/etc/asterisk/pinauth.passwd', 'r')
        for line in passFile:
            if ":" in line and line[0] != ";":
                user, compHash = line.split(':',1)
                if hash in compHash:
                    passFile.close()
                    return user
        passFile.close()
