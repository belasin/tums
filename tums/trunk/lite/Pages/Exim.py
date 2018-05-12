from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
import formal

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[self.text.tools]]

    def form_mailBlacklist(self, data):
        form = formal.Form()
        form.addField('blacklist', formal.String(), label = self.text.eximBlacklistEntry)
        form.addAction(self.submitBlacklist)
        return form

    def submitBlacklist(self, ctx, form, data):
        if not data['blacklist']:
            return url.root.child('Mailserver')

        mailConf = self.sysconf.Mail
        if mailConf.get('blacklist', None):
            mailConf['blacklist'].append(data['blacklist'].encode())
        else:
            mailConf['blacklist'] = [data['blacklist'].encode()]

        self.sysconf.Mail = mailConf

        if Settings.Mailer=="exim":
            WebUtils.system(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim restart')

        return url.root.child('Mailserver')

    def form_mailWhitelist(self, data):
        form = formal.Form()
        form.addField('whitelist', formal.String(), label = self.text.eximWhitelistEntry)
        form.addAction(self.submitBlacklist)
        return form

    def submitWhitelist(self, ctx, form, data):
        if not data['whitelist']:
            return url.root.child('Mailserver')

        mailConf = self.sysconf.Mail
        if mailConf.get('whitelist', None):
            mailConf['whitelist'].append(data['whitelist'].encode())
        else:
            mailConf['whitelist'] = [data['whitelist'].encode()]

        self.sysconf.Mail = mailConf

        if Settings.Mailer=="exim":
            WebUtils.system(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim restart')

        return url.root.child('Mailserver')


    def form_mailHubbed(self, data):
        form = formal.Form()
        form.addField('hubbedHosts', formal.String(), formal.TextArea, label = self.text.eximHubbedHostMappings,
            description = self.text.eximHubbedHostDescription)

        mailConf = self.sysconf.Mail
        form.data['hubbedHosts']  = '\n'.join(['    '.join(i) for i in mailConf['hubbed']])
        form.addAction(self.submitHubbed)
        return form

    def submitHubbed(self, ctx, form, data):
        mailConf = self.sysconf.Mail
        if data['hubbedHosts']:
            mailConf['hubbed'] = [ i.split() for i in data['hubbedHosts'].encode().replace('\r','').split('\n')]
        else:
            mailConf['hubbed'] = []

        self.sysconf.Mail = mailConf
        if Settings.Mailer=="exim":
            WebUtils.system(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim restart')
        return url.root.child('Mailserver')

    def form_mailLocal(self, data):
        form = formal.Form()
        form.addField('localDomains', formal.String(), formal.TextArea, label = self.text.eximLocalDomains,
            description = self.text.eximLocalDescription)

        local = self.sysconf.LocalDomains
        form.data['localDomains'] = '\n'.join(local)
        form.addAction(self.submitLocal)
        return form

    def submitLocal(self, ctx, form, data):
        mailConf = self.sysconf.Mail
        if data['localDomains']:
            self.sysconf.LocalDomains = data['localDomains'].encode().replace(' ', '').replace('\r','').split('\n')
            # You need local domains

        self.sysconf.Mail = mailConf
        if Settings.Mailer=="exim":
            WebUtils.system(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim restart')
        return url.root.child('Mailserver')

    def form_mailRelay(self, data):
        form = formal.Form()
        form.addField('relayDomains', formal.String(), formal.TextArea, label = self.text.eximRelayDomains,
            description = self.text.eximRelayDescription)

        form.data['relayDomains'] = '\n'.join(self.sysconf.Mail['relay'])
        form.addAction(self.submitRelay)
        return form

    def submitRelay(self, ctx, form, data):
        mailConf = self.sysconf.Mail
        if data['relayDomains']:
            mailConf['relay'] = data['relayDomains'].encode().replace(' ', '').replace('\r','').split('\n')
        else:
            mailConf['relay'] = []

        self.sysconf.Mail = mailConf
        if Settings.Mailer=="exim":
            WebUtils.system(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim restart')
        return url.root.child('Mailserver')

    def form_mailConfig(self, data):
        form = formal.Form()

        form.addField('maxsize', formal.String(), label = self.text.eximMaxMailSize, 
            description = self.text.eximMaxSizeDescription)

        form.addField('blockedFiles', formal.String(), label = self.text.eximBlockedAttachment,
            description = self.text.eximBlockedDescription)

        form.addField('blockMovies', formal.Boolean(), label = self.text.eximBlockedMovies, 
            description = self.text.eximBlockedMovieDescription)

        form.addField('blockHarm', formal.Boolean(), label = self.text.eximBlockHarmful,
            description = self.text.eximBlockHarmfulDescription)

        form.addField('greylisting', formal.Boolean(), label = self.text.eximGreylisting,
            description = self.text.eximGreylistingDescription)

        form.addField('spamscore', formal.Integer(), label = self.text.eximSpamScore,
            description = self.text.eximSpamScoreDescription)

        form.addField('smtprelay', formal.String(), label = self.text.eximSMTPRelay, 
            description = self.text.eximSMTPRelayDescription)

        form.addField('copyall', formal.String(), label = self.text.eximMailCopy, 
            description = self.text.eximMailCopyDescription)
    
        mailConf = self.sysconf.Mail
        form.data['maxsize'] = mailConf['mailsize']
        form.data['blockedFiles'] = ', '.join(mailConf['blockedfiles'])
        form.data['greylisting']  = mailConf.get('greylisting', True)
        form.data['smtprelay'] = self.sysconf.SMTPRelay
        form.data['copyall'] = mailConf.get('copytoall', "")
        form.data['spamscore'] = int(mailConf.get('spamscore', "70"))

        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        mailConf = self.sysconf.Mail
        blockedFiles = []

        if data['copyall']:
            mailConf['copytoall'] = data['copyall'] 
        else:
            mailConf['copytoall'] = ''

        mailConf['spamscore'] = str(data['spamscore'])

        if data['blockedFiles']:
            blockedFiles = data['blockedFiles'].encode().replace(' ', '').split(',')

        mailConf['greylisting'] = data['greylisting']

        if data['blockMovies']:
            for i in ['mp4', 'wmv', 'avi', 'mpeg', 'mp3', 'wav', 'snd', 'avs', 'qt', 'mov', 'mid']:
                if i not in blockedFiles:
                    blockedFiles.append(i)

        if data['blockHarm']:
            for i in ['exe', 'pif', 'lnk', 'bat', 'scr', 'vbs']:
                if i not in blockedFiles:
                    blockedFiles.append(i)
        
        mailConf['blockedfiles'] = blockedFiles

        if data['maxsize']:
            mailConf['mailsize'] = data['maxsize'].encode()
        else:
            mailConf['mailsize'] = ""

        if data['smtprelay']:
            self.sysconf.SMTPRelay = data['smtprelay'].encode()
        else:
            self.sysconf.SMTPRelay = ""
        
        self.sysconf.Mail = mailConf
        if Settings.Mailer=="exim":
            if os.path.exists('/etc/debian_version'):
                WebUtils.system(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim4 restart')
            else:
                WebUtils.system(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim restart')
        return url.root.child('Mailserver')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        blacklist = []
        j = 0 
        for i in self.sysconf.Mail.get('blacklist', []):
            blacklist.append([
                i, tags.a(href=url.root.child("Mailserver").child("BDelete").child(j), onclick="return confirm('%s');" % self.text.eximConfirmDelete)[tags.img(src="/images/ex.png")]
            ])
            j += 1

        whitelist = []
        j = 0 
        for i in self.sysconf.Mail.get('whitelist', []):
            whitelist.append([
                i, tags.a(href=url.root.child("Mailserver").child("WDelete").child(j), onclick="return confirm('%s');" % self.text.eximConfirmDelete)[tags.img(src="/images/ex.png")]
            ])
            j += 1


        return ctx.tag[
            tags.h2[tags.img(src="/images/mailsrv.png"), " Email Server Config"],
            PageHelpers.TabSwitcher((
                (self.text.eximTabMail, 'panelMail'),
                (self.text.eximTabRelay, 'panelRelay'),
                (self.text.eximTabHubbed, 'panelHubbed'),
                (self.text.eximTabLocal, 'panelLocal'),
                (self.text.eximTabBlocked, 'panelBlack'),
                (self.text.eximTabWhitelist, 'panelWhite')
            )),
            tags.div(id="panelMail", _class="tabPane")[tags.directive('form mailConfig')],
            tags.div(id="panelRelay", _class="tabPane")[tags.directive('form mailRelay')],
            tags.div(id="panelHubbed", _class="tabPane")[tags.directive('form mailHubbed')],
            tags.div(id="panelLocal", _class="tabPane")[tags.directive('form mailLocal')],
            tags.div(id="panelBlack", _class="tabPane")[
                PageHelpers.dataTable([self.text.eximAddr, ''], blacklist),
                tags.h3[self.text.eximAddBlacklist],
                tags.directive('form mailBlacklist')
            ],
            tags.div(id="panelWhite", _class="tabPane")[
                PageHelpers.dataTable([self.text.eximAddrOrHost, ''], whitelist),
                tags.h3[self.text.eximAddWhitelist],
                tags.directive('form mailWhitelist')
            ],
            PageHelpers.LoadTabSwitcher()
        ]
    def locateChild(self, ctx, segs):
        if segs[0] == "BDelete":
            mc = self.sysconf.Mail
            try:
                del mc['blacklist'][int(segs[1])]
            except:
                print "Error removing blacklist entry", segs[1]
            self.sysconf.Mail = mc
            return url.root.child('Mailserver'), ()

        if segs[0] == "WDelete":
            mc = self.sysconf.Mail
            try:
                del mc['blacklist'][int(segs[1])]
            except:
                print "Error removing", segs[1]
            self.sysconf.Mail = mc
            return url.root.child('Mailserver'), ()

        return rend.Page.locateChild(self, ctx, segs)
