from twisted.internet.defer import deferredGenerator, waitForDeferred as wait, DeferredList

from twisted.internet.protocol import ProcessProtocol

from twisted.internet import reactor


@deferredGenerator
def system(e):
    from twisted.internet import utils
    mq = utils.getProcessOutput('/bin/sh', ['-c', e], errortoo=1)
    res = wait(mq)
    yield res
    yield res.getResult()


class TarExtractor(ProcessProtocol):
    def __init__(self, fragment, file):
        self.fragment = fragment
        self.file = file
        self.linesTotal = 0

    def outReceived(self, data):
        n = len(data.split('\n'))-1
        self.linesTotal += n
        self.fragment.progressUpdate(self.file, self.linesTotal)

    def processEnded(self, status):
        print "Completed %s with status %s" % (self.file, status.value.exitCode)
        print self.linesTotal, "total"
        self.fragment.fileComplete(self.file)

        self.file = file

def extractBz2(fragment, filename):
    rproc = TarExtractor(fragment, filename)
    reactor.spawnProcess(rproc, "/bin/tar", ["tar", "-pPjvx", "-C", "/mnt/target/", "-f", "/root/%s" % filename])

