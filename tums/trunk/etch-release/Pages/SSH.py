from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, log
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, Utils, confparse, WebUtils
from Pages import Tools
import formal, copy

class SSHKeys(PageHelpers.DataTable):
    def getTable(self):
        headings = [
            ('Name', 'name'), 
            ('Key', 'key'), 
        ]

        table = []
        
        for n, k in self.sysconf.General.get('sshkeys', []):
            v = k.split()
            type = v[0]
            authorizer = v[-1]
            table.append((n, '%s ... %s' % (type, authorizer)))
        
        return headings, table

    def addForm(self, form):
        form.addField('name', formal.String(required=True), label = "Name")

        form.addField('key', formal.String(required=True), formal.TextArea, label = "Key")

    def addAction(self, data):
        key = data['key'].encode().replace('\r', '').replace('\n', '')
        name = data['name'].encode()

        r = [name, key]

        t = self.sysconf.General 
        
        if t.get('sshkeys'):
            t['sshkeys'].append(r)
        else:
            t['sshkeys'] = [r]

        self.sysconf.General = t
        
    def returnAction(self, data):
        def ret(_):
            return url.root.child('SSH')
        return WebUtils.system(Settings.BaseDir+'/configurator --ssh').addBoth(ret)

class Page(Tools.Page):
    addSlash = True

    def __init__(self, *a, **kw):
        Tools.Page.__init__(self, *a, **kw)
        self.keys = SSHKeys  (self, 'SSHKey',  'ssh key', 'General', 'sshkeys')

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/remote_access_section.png"), " SSH Keys"],
            self.keys.applyTable(self)
        ]

        
