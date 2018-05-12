"""Authenticated XML-RPC classes """
from twisted.web import server, xmlrpc
from twisted.internet import reactor, defer
import xmlrpclib, sha

from OpenSSL import SSL

class AuthXMLRPCServer(xmlrpc.XMLRPC):
    """ Authenticated XML-RPC server class"""

    def render(self, request):
        # From twisted.web.xmlrpc
        request.content.seek(0, 0)

        args, functionPath = xmlrpclib.loads(request.content.read())

        # Append the request host to the first argument
        newArgs = tuple([request.client.host] + list(args))

        try:
            function = self._getFunction(functionPath)
        except Exception, f:
            self._cbRender(f, request)
        else:
            request.setHeader("content-type", "text/xml")
            defer.maybeDeferred(function, *newArgs).addErrback(
                self._ebRender
            ).addCallback(
                self._cbRender, request
            )

        return server.NOT_DONE_YET

