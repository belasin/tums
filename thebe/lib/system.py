from twisted.internet.defer import deferredGenerator, waitForDeferred as wait, DeferredList

@deferredGenerator
def system(e):
    from twisted.internet import utils
    mq = utils.getProcessOutput('/bin/sh', ['-c', e], errortoo=1)
    res = wait(mq)
    yield res
    yield res.getResult()

def portCheck(portList, host):
    def returnOpen(_):
        print _
        if "open" in _:
            return True
        return False
    def returnFailure(_):
        return None

    dList = [
        system('nmap -P0 -p %s %s | grep %s' % (port, host, port)).addCallbacks(returnOpen, returnFailure)
        for port in portList
    ]
    return DeferredList(dList)
