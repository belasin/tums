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

class Page(Tools.Page):
    def reloadSamba(self):
        WebUtils.system(Settings.BaseDir+'/configurator --samba')
        WebUtils.system("/etc/init.d/samba restart");

    def form_configSamba(self, data):
        form = formal.Form()

        form.addField('pdc', formal.Boolean(), label = "Domain controller")
        form.addField('profileroam', formal.Boolean(), label = "Roaming Profiles")

        form.addAction(self.submitForm)

        smbcfg = self.sysconf.SambaConfig

        if smbcfg.get('logon path', None):
            if smbcfg['logon path']:
                form.data['profileroam'] = True
        if smbcfg.get('domain logons', None):
            if smbcfg['domain logons'] == 'yes':
                form.data['pdc'] = True
        return form

    def submitForm(self, ctx, form, data):
        smbcfg = self.sysconf.SambaConfig

        if data['pdc']:
            smbcfg['domain logons'] = 'yes'
            smbcfg['domain master'] = 'yes'
        else:
            smbcfg['domain logons'] = 'no'
            smbcfg['domain master'] = 'no'

        if data['profileroam']:
            smbcfg['logon path'] = '\\\\%L\\Profiles\\%U'
        else:
            smbcfg['logon path'] = ''

        self.sysconf.SambaConfig = smbcfg

        self.reloadSamba()
        
        return url.root.child('SambaConfig')

    def render_content(self, ctx, data):
        shares = self.sysconf.SambaShares

        return ctx.tag[
            tags.h3[tags.img(src="/images/sharefold.png"), " Domain configuration"],
            tags.directive('form configSamba'),
        ]
