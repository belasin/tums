from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha

from custom import Widgets

from twisted.internet import utils, reactor

class Page(pages.Standard):
    arbitraryArguments = True # Enable REST style arguments to the page
    def locateChild(self, ctx, segs):
        if segs[0] == "Upgrade":
            self.enamel.tcsClients.sendMessage(int(segs[1]), "tumsupgrade::")
            return url.root.child('Dashboard'), ()

        if self.arbitraryArguments:
            # A dodgey hack for passing arguments as child segments to a page
            if page == (None, ()):
                # If we got NotFound return a new instance of myself
                return self.__class__(self.avatarId, self.enamel, arguments=segs), ()

        return pages.Standard.locateChild(self, ctx, segs)

    def body(self):
        print self.arguments
        if self.arguments[0] == "HELO":
            self.enamel.tcsClients.sendMessage(int(self.arguments[1]), "HELO::")
        if self.arguments[0] == "RESET":
            # Reset my self first...
            self.enamel.tcsMaster.knownNodes = {}
            def resetAll(clients):
                for i in clients:
                    self.enamel.tcsClients.sendMessage(i[0], "resetPeers::")
                return "OK"

            return self.enamel.storage.getServers().addCallback(resetAll)

        if self.arguments[0] == "EX": 
            # Reset my self first...
            def resetAll(clients):
                for i in clients:
                    self.enamel.tcsClients.sendMessage(i[0], "execute::rm /etc/logrotate.d/*.ucf-dist")
                return "OK"

            return self.enamel.storage.getServers().addCallback(resetAll)
            
        if self.arguments[0] == "FILE":
            f = open('/home/colin/thekillers.mp3')
            self.enamel.tcsClients.sendMessage(int(self.arguments[1]), "FILE:killtest.mp3:%s" % f.read(2*1024))
            l = "n"
            while l:
                l = f.read(2*1024)
                if l:
                    self.enamel.tcsClients.sendMessage(int(self.arguments[1]), "FILEP:killtest.mp3:%s" % l)
            self.enamel.tcsClients.sendMessage(int(self.arguments[1]), "FILEE:killtest.mp3:")

        return ""
