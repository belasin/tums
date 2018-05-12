from enamel import authentication, deployment, pages, servers, storage, deferreds, tags, url
from enamel import sql, form
import enamel, sha

from custom import Widgets
from twisted.internet import utils, defer

from lib import PageBase, web

class Page(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('ticket.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def form_createTicket(self, data):
        ticket = form.Form()
        ticket.addField('subject', form.String(required=True), label = "Subject")
        ticket.addField('detail', form.String(required=True), form.TextArea, label = "Detail")

        ticket.addAction(self.sendTicket)

        return ticket

    def sendTicket(self, ctx, form, data):
        def gotUser(user):
            name = user[3]
            email = user[4]

            subject = data['subject'].encode('ascii', 'replace')
            text = data['detail'].encode('ascii', 'replace')

            web.sendMail("%s <%s>" % (name, email), ["support@vulani.net"], "[Vulani Support] %s" % subject, text)
            return url.root.child('Dashboard')

        return self.enamel.storage.getUser(self.avatarId.uid).addBoth(gotUser)

    def render_userForm(self, ctx, data):
        return ctx.tag[
            tags.directive('form createTicket')
        ]

