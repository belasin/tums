"""
Vulani Fetchmail plugin
Copyright (c) 2009, Thusa Business Support (Pty) Ltd.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Thusa Business Support (Pty) Ltd. nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY Thusa Business Support (Pty) Ltd. ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Thusa Business Support (Pty) Ltd. BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

# Vulani modules
from Core import PageHelpers, WebUtils
import Settings

# Nevow and Twisted
from nevow import tags, rend, loaders, url
from twisted.python import log
import formal

# System libraries
import os


class FetchmailBoxes(PageHelpers.DataTable):
    def getTable(self):
        # Table headings
        headings = [
            ('Server', 'server'), 
            ('Domain', 'domain'), 
            ('User',   'user'), 
            ('Password', 'password'), 
            ('Destination', 'destination')
        ]

        # Fetch data from configuration storage
        data = self.sysconf.Mail.get('fetchmail', [])

        return headings, data

    def addForm(self, form):
        # Define the fetchmail form. Field ID's must match headings
        form.addField('user', formal.String(required=True), label = "Username", 
                description = "Username for remote server")
        form.addField('password', formal.String(required=True), label = "Password",
                description = "Password for remote server")
        form.addField('server', formal.String(required=True), label = "Remote Server", 
                description = "Hostname or IP of remote server")
        form.addField('domain', formal.String(required=True), label = "Local Domain", 
                description = "The local domain name for mail delivery from this account")
        form.addField('destination', formal.String(required=True), label = "Destination Account", 
                description = "The local address to which email should be delivered. '*' will match remote usernames to local ones and is usualy fine")

        form.data['destination'] = '*'
        form.data['domain'] = self.sysconf.Domain

    def returnAction(self, data):
        log.msg("User %s added new fetchmail account %s" % (self.avatarId.username, repr(data)))

        # Restart the fetchmail service. This works since we called our configurator hook --fetchmail also
        return WebUtils.restartService('fetchmail').addBoth(
            # Return back to our page view
            lambda _: url.root.child('Fetchmail')
        )

class FetchmailPage(PageHelpers.ToolsPage):
    def __init__(self, *a, **kw):
        PageHelpers.ToolsPage.__init__(self, *a, **kw)

        self.FetchmailBoxesTable = FetchmailBoxes(self, 
                "FetchmailBoxes",    # Unique name for this widget
                "fetchmail account", # Description text for editor
                "Mail",      # Configuration storage container
                "fetchmail"  # storage sub container
            )

    # This is the default render method for page content
    def render_content(self, ctx, tag):
        return ctx.tag[
            self.FetchmailBoxesTable.applyTable(self)
        ]
