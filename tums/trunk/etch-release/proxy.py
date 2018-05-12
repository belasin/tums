#!/usr/bin/python
from twisted.internet import reactor, protocol
from twisted.application import internet, service
from twisted.web import proxy, server, http
import urlparse, sha, os
from Core import Utils
import Settings

fpath = "/var/lib/samba/updates"

class ProxycatorClient(proxy.ProxyClient):
    """ A ProxyClient implementation which stores any data transfered through it"""
    def __init__(self, command, rest, version, headers, data, father):
        proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
        print headers, version, command, data
        self.fname = rest.split('/')[-1]
        self.fhash = sha.sha(self.fname).hexdigest()
        self.out_headers = {}

        if not os.path.exists('%s/%s' % (fpath, self.fhash)):
            os.mkdir('%s/%s' % (fpath, self.fhash)) 

        if headers.get('range'):
            self.foutput = None
        elif os.path.exists('%s/%s/%s' % (fpath, self.fhash, self.fname)) and os.path.exists('%s/%s/done' % (fpath, self.fname)):
            # It's done and the file exists
            print "Already fetched: %s" % self.fname
            self.foutput = None
        else:
            print "Fetching %s" % rest
            self.foutput = open('%s/%s/%s' % (fpath, self.fhash, self.fname), 'wb') 

    def handleHeader(self, key, value):
        self.out_headers[key] = value
        print key, value
        self.father.transport.write("%s: %s\r\n" % (key, value))

    def handleResponsePart(self, buffer):
        if self.foutput:
            self.foutput.write(buffer)

        self.father.transport.write(buffer)

    def completeFile(self):
        done = open('%s/%s/done' % (fpath, self.fhash), 'wt')
        done.write('1\n')
        done.close()
        print "Done writing", self.fname

    def handleResponseEnd(self):
        if self.foutput:
            self.foutput.close()

            # Check size
            size = int(self.out_headers.get('Content-Length', -1))
            writeSize = os.stat('%s/%s/%s' % (fpath, self.fhash, self.fname)).st_size

            if size > 0:
                if (size == writeSize) and (size > 921600):
                    self.completeFile()
                else:
                    print "Skipping badly sized update ", self.fname
            else:
                # No content-length to use
                self.completeFile()
        
        self.transport.loseConnection()
        self.father.channel.transport.loseConnection()

class ProxycatorClientFactory(proxy.ProxyClientFactory):
    protocol = ProxycatorClient

class Proxycator(proxy.ReverseProxyResource):
    """A proxy implementation which acquires its host destination from the first URL segment.
    """
    def getChild(self, path, request):
        return Proxycator(self.host, self.port, self.path+'/'+path)

    def render(self, request):
        request.received_headers['host'] = self.host
        request.content.seek(0, 0)
        qs = urlparse.urlparse(request.uri)[4]
        segs = self.path.split('/',2)
        st = ""
        if len(segs) > 2:
            st = segs[1]
            self.path = '/'+segs[-1]
        else:
            st = self.path
            self.path = ''
        port = 80
        if ':' in st:
            st, port = st.split(':')

        request.received_headers['host'] = st

        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path
        
        print st, qs, request.uri, rest

        clientFactory = ProxycatorClientFactory(request.method, rest,
                                     request.clientproto,
                                     request.getAllHeaders(),
                                     request.content.read(),
                                     request)
        reactor.connectTCP(st, port, clientFactory)
        return server.NOT_DONE_YET

print "Proxy started",

application = service.Application('PROXY')

site = server.Site(Proxycator('127.0.0.1', 80, ''))

proxyapp = internet.TCPServer(10632, site, interface='127.0.0.1')
proxyapp.setServiceParent(application)

log = '/var/log/tums-proxy.log'
daemon = 0
#log = None
if __name__ == '__main__':
    Utils.startTwisted(application, Settings.BaseDir, daemon, log, Settings.BaseDir, pidfile='/var/run/tums-proxy.pid')

