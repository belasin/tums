from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, confparse, Utils, WebUtils
from Pages import Tools

from twisted.python import log

def reloadSamba():
    def cont(_):
        return WebUtils.system("/etc/init.d/samba restart")

    return WebUtils.system(Settings.BaseDir+'/configurator --samba').addBoth(cont)

class Shares(PageHelpers.DataTable):
    def getTable(self):
        headings = [
            ('Share Name', 'share'), 
            ('Shared Path', 'path'), 
            ('Comment', 'comment'), 
            ('Writable', 'writable'), 
            ('Public', 'public'),
            ('Permission', 'group')
        ]
        sharesconf = self.sysconf.SambaShares

        shares = []

        for share in sharesconf.keys():
            if share=="global":
                continue

            row = [share]
            for i in ['path', 'comment', 'writable', 'public','valid users']:
                sdata = sharesconf[share].get(i, "")
                if i == 'valid users':
                    sdata = sdata.replace('@', '').replace('"', '').replace(',root', '').strip()

                row.append(sdata)

            shares.append(row)

        return headings, shares

    def addForm(self, form):
        form.addField('share', formal.String(required=True), label = "Shared Folder")
        form.addField('path', formal.String(required=True), label = "Shared Path", description = "Path to be shared")
        form.addField('comment', formal.String(required=True), label = "Comment")

        form.addField('public', formal.Boolean(), label = "Public")
        form.addField('writable', formal.Boolean(), label = "Writable")

        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(Settings.defaultDomain), Settings.LDAPBase)

        groups = LDAP.getGroups(l, dc)
        groups.sort()
        
        form.addField('group', formal.String(), 
            formal.widgetFactory(formal.SelectChoice, options = [(i[1],i[1]) for i in groups]), 
            label = "Required Group")
 
    def addAction(self, data):
        if "/" in data['path']:
            if data['path'][0] == "/": # Starts with a /
                path = data['path']
            else:
                path = "/var/lib/samba/data/%s" % data['path']
        else:
            path = '/var/lib/samba/data/%s' % data['path']
            
        share = {} #[%s]\n" % (data['share'],)
        share["path"] = path
        share["comment"] = data['comment']
        share["create mode"] = '664'
        share["directory mode"] = '775'
        share["nt acl support"] = 'yes'
        WebUtils.system('mkdir -p %s' % path)
        
        if data['public']:
            share["public"] = "yes"

        if data['writable']:
            share["writable"] = "yes"

        if data['group']:
            share["valid users"] = '@"%s",root' % data['group']
            WebUtils.system('chown -R root:"%s" %s' % (data['group'], path))

        WebUtils.system('chmod a+rwx %s' % path)
        WebUtils.system('chmod -R a+rw %s' % path)

        shares = self.sysconf.SambaShares
        shares[data['share'].encode()] = share
        self.sysconf.SambaShares = shares
 
    def deleteItem(self, item):
        shares = self.getTable()[1]

        target = shares[item]

        name = target[0]

        shares = self.sysconf.SambaShares
        del shares[name]
        self.sysconf.SambaShares = shares

    def returnAction(self, data):
        Utils.log.msg('%s added file share %s' % (self.avatarId.username, repr(data)))
        return reloadSamba().addBoth(lambda _: url.root.child('Samba'))

class Page(Tools.Page):
    def __init__(self, *a, **kw):
        Tools.Page.__init__(self, *a, **kw)
        self.shareTable = Shares(self, 'Shares', 'share')

    def render_content(self, ctx, data):
   
        return ctx.tag[
            tags.h3[tags.img(src="/images/sharefold.png"), " Shared folders"],
            self.shareTable.applyTable(self)
        ]
