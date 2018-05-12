from twisted.web import server, static, twcgi, proxy
from twisted.internet import reactor
import base64
import urlparse

class AuthApacheProxy(proxy.ReverseProxyResource):
    """ I proxy requests to some server whilst appending the
    provided credentials to the header """
    addSlash = True
    def __init__(self, host, port, path, username, password):
        proxy.ReverseProxyResource.__init__(self, host, port, path)
        self.username = username
        self.password = password

    def encodeAuthHeader(self):
        return base64.encodestring("%s:%s" % (self.username, self.password,))

    def getChild(self, path, request):
        return AuthApacheProxy(self.host, self.port, self.path+'/'+path, self.username, self.password)

    def render(self, request):
        request.received_headers['host'] = self.host
        request.received_headers['authorization'] = "Basic %s" % (self.encodeAuthHeader(),)
        request.content.seek(0, 0)
        qs = urlparse.urlparse(request.uri)[4]
        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path
        clientFactory = proxy.ProxyClientFactory(request.method, rest,
                                     request.clientproto,
                                     request.getAllHeaders(),
                                     request.content.read(),
                                     request)
        reactor.connectTCP(self.host, self.port, clientFactory)
        return server.NOT_DONE_YET
