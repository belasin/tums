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

from twisted.python import log

def restartExim():
    return WebUtils.system(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim4 restart')
 
def returnRoot(_):
    return url.root.child('Mailserver')

class BranchServers(PageHelpers.DataTable):
    def getTable(self):
        headings = [
                ('Server IP', 'server'),
                ('Relays',    'relays')
            ]
        branches = self.sysconf.Mail.get('branches', [])
        return headings, branches

    def addForm(self, form):
        form.addField('server', formal.String(required=True, strip=True, validators=[PageHelpers.IPValidator()]), label = "Server IP", 
            description = "IP address of branch server.")

        form.addField('relays', formal.String(), label = "Relay servers", 
            description = "A comma separated list of servers to relay this mail to. If left blank, the server IP will be used")

    def returnAction(self, data):
        Utils.log.msg('%s added branch server %s' % (self.avatarId.username, repr(data)))

        d = WebUtils.refreshBranches(self.sysconf)
        
        if type(d) == bool:
            return url.root.child('Mailserver')
        else:
            return d.addBoth(lambda _: url.root.child('Mailserver'))


class RelayDomains(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Domain', 'domain')]
        domains = self.sysconf.Mail.get('relay', [])
        return headings, domains

    def addForm(self, form):
        form.addField('domain', formal.String(required=True), label = "Domain")

    def returnAction(self, data):
        Utils.log.msg('%s added relay mail domain %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class Hubbed(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Domain', 'hubbedHost'), ('Destination', 'hubbedDest')]
        hlist = self.sysconf.Mail.get('hubbed', [])
        return headings, hlist

    def addForm(self,form):
        form.addField('hubbedHost', formal.String(required=True),label = "Domain",
            description = "Domain to relay to destination")
        form.addField('hubbedDest', formal.String(required=True),label = "Destination",
            description = "Destination to relay mail for the domain")

    def returnAction(self, data):
        Utils.log.msg('%s added hubbed mail entry %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class Local(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Domain', 'domain')]
        domains = self.sysconf.LocalDomains
        return headings, domains

    def addForm(self, form):
        form.addField('domain', formal.String(required=True), label = "Domain")

    def returnAction(self, data):
        Utils.log.msg('%s added local domain %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class RBLSub(PageHelpers.DataTable):
    def getTable(self):
        headings = [('RBL', 'rbl')]

        if not self.sysconf.Mail.get('rbls', []):
            M = self.sysconf.Mail 
            M['rbls'] = [
                "dsn.rfc-ignorant.org/$sender_address_domain",
                "zen.spamhaus.org",
                "dnsbl.njabl.org",
                "bhnc.njabl.org",
                "combined.njabl.org",
                "bl.spamcop.net",
                "psbl-mirror.surriel.com",
                "blackholes.mail-abuse.org",
                "dialup.mail-abuse.org"
            ]
            self.sysconf.Mail = M
        
        rbl = self.sysconf.Mail.get('rbls', [])
        
        return headings, rbl

    def addForm(self, form):
        form.addField('rbl', formal.String(required=True), label = "RBL")

    def returnAction(self, data):
        Utils.log.msg('%s added RBL entry %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class Blacklist(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Address', 'address')]
        blist = self.sysconf.Mail.get('blacklist', [])
        return headings, blist

    def addForm(self, form):
        form.addField('address', formal.String(required=True), label = "Blacklist Entry")

    def returnAction(self, data):
        Utils.log.msg('%s blacklisted email address %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class Whitelist(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Address', 'address')]
        blist = self.sysconf.Mail.get('whitelist', [])
        return headings, blist

    def addForm(self, form):
        form.addField('address', formal.String(required=True), label = "Whitelist Entry")

    def returnAction(self, data):
        Utils.log.msg('%s whitelisted email address %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class Catchall(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Domain', 'domain')]
        blist = self.sysconf.Mail.get('catchall', [])
        return headings, blist

    def addForm(self, form):
        form.addField('domain', formal.String(required=True), label = "Domain")

    def returnAction(self, data):
        Utils.log.msg('%s Set domain %s to allow catchall mailbox' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class Senders(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Address', 'address')]
        slist = self.sysconf.Mail.get('allowsend', [])
        return headings, slist

    def addForm(self, form):
        form.addField('address', formal.String(required=True), label = 'Address')

    def returnAction(self, data):
        Utils.log.msg('%s added allowed sender %s' % (self.avatarId.username, repr(data)))
        return restartExim().addCallback(returnRoot)

class Page(Tools.Page):
    addSlash = True
    def __init__(self, *a, **kw):
        PageHelpers.DefaultPage.__init__(self, *a, **kw)
        self.addRelay       = RelayDomains  (self, 'RelayDomains',  'Relay domain', 'Mail', 'relay')
        self.addHubbed      = Hubbed        (self, 'HubbedDomains', 'Mail routing', 'Mail', 'hubbed')
        self.addBlacklist   = Blacklist     (self, 'Blacklist',     'blacklist',    'Mail', 'blacklist')
        self.addWhitelist   = Whitelist     (self, 'Whitelist',     'whitelist',    'Mail', 'whitelist')
        self.addCatchall    = Catchall      (self, 'Catchall',      'catchall',     'Mail', 'catchall')
        self.addSender      = Senders       (self, 'Senders',       'sender',       'Mail', 'allowsend')

        self.addBranch      = BranchServers (self, 'BranchServers', 'server',       'Mail', 'branches')

        self.addLocal       = Local  (self, 'LocalDomains',  'Local domain', 'LocalDomains')

        self.addSub         = RBLSub (self, 'RBLSub',     'RBL subscription',    'Mail', 'rbls')

    def form_mailDisclaimer(self, data):
        form = formal.Form()
        form.addField('enabled', formal.Boolean(), label = "Enable Disclaimer", 
            description = "Tick to enable the disclaimer system which will append the disclaimer (below) to all outgoing mails")

        form.addField('disclaimer', formal.String(), formal.TextArea, label = "Disclaimer")
        form.addAction(self.mailDisclaimer)

        form.data['enabled'] = self.sysconf.Mail.get('disclaimer')
        try:
            text = open('/usr/local/tcs/tums/data/gldisclaimer').read()
            form.data['disclaimer'] = text
        except: 
            pass 

        return form

    def mailDisclaimer(self, ctx, f, data):
        enabled = data['enabled']

        # Save enabled state
        mailConf = self.sysconf.Mail
        mailConf['disclaimer'] = enabled
        self.sysconf.Mail = mailConf
        
        # Ensure our data directory exists
        try:
            os.mkdir('/usr/local/tcs/tums/data/')
        except:
            pass

        # Write disclaimer
        disclaimer = data['disclaimer'] or u''
        l = open('/usr/local/tcs/tums/data/gldisclaimer', 'wt')
        l.write(disclaimer.encode('utf-8'))
        l.close()

        return restartExim().addCallback(returnRoot)

    def form_mailRewrite(self, data):
        form = formal.Form()
        form.addField('ffrom', formal.String(required=True),label = "Domain",
            description = "Domain to modify")

        form.addField('tto', formal.String(required=True),label = "Rewrite to",
            description = "Domain to rewrite to")

        form.addField('tos', formal.Boolean(),label = "To header",  description = "Rewrite email To header")
        form.addField('froms', formal.Boolean(),label = "From header",  description = "Rewrite email From header")
        form.addField('bcr', formal.Boolean(),label = "BCC, CC and Recipient",  description = "Rewrite all other headers")
        form.addAction(self.submitRewrite)
        return form

    def submitRewrite(self, ctx, form, data):
        Utils.log.msg('%s added rewrite rule %s' % (self.avatarId.username, repr(data)))
        mailConf = self.sysconf.Mail

        if not mailConf.get('rewrites', None):
            mailConf['rewrites'] = []
        
        flags = ""
        if data['tos']:
            flags += "Tt"
        if data['froms']:
            flags += "Ff"
        if data['bcr']:
            flags += "bcr"

        mailConf['rewrites'].append([
            data['ffrom'].encode("ascii", "replace"),
            data['tto'].encode("ascii", "replace"),
            flags
        ])

        self.sysconf.Mail = mailConf
        return restartExim().addCallback(returnRoot)

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

        form.addField('smtpinterface', formal.String(), label = "External IP", 
            description = "Specify an external IP for outgoing SMTP")

        form.addField('relayfrom', formal.String(), label = "Relay From",
            description = "Comma separated list of networks from which we will accept mail (IP bound to LAN is included by default)")

        form.addField('copyall', formal.String(), label = self.text.eximMailCopy, 
            description = self.text.eximMailCopyDescription)

        form.addField('rpfilter', formal.Boolean(), label = "Send Filter", 
            description = "Enable local sender filtering. This will enforce a rule such that any relay host or local host is forced to send as a known local domain or authorised sender")


        form.addField('ratelimit', formal.Boolean(), label = "Rate Limiter", 
            description = "Enable local rate limiting. This will enforce a rate limit on the number of mails that can be sent in an hour from any address that is not local.")

        mailConf = self.sysconf.Mail
        form.data['maxsize'] = mailConf['mailsize']
        form.data['blockedFiles'] = ', '.join(mailConf['blockedfiles'])
        form.data['greylisting']  = mailConf.get('greylisting', True)
        form.data['smtprelay'] = self.sysconf.SMTPRelay
        form.data['smtpinterface'] = mailConf.get('smtpinterface', '')
        form.data['copyall'] = mailConf.get('copytoall', "")
        form.data['spamscore'] = int(mailConf.get('spamscore', "70"))
        form.data['relayfrom'] = ','.join(mailConf.get('relay-from', []))

        form.data['rpfilter'] = not mailConf.get('disablerpfilter', False)
        form.data['ratelimit'] = not mailConf.get('disableratelimit', False)

        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        Utils.log.msg('%s altered mail configuration %s' % (self.avatarId.username, repr(data)))
        mailConf = self.sysconf.Mail
        blockedFiles = []

        # Reverse filtering
        mailConf['disablerpfilter'] = not data['rpfilter']
        mailConf['disableratelimit'] = not data['ratelimit']

        if data['copyall']:
            mailConf['copytoall'] = data['copyall'] 
        else:
            mailConf['copytoall'] = ''

        mailConf['spamscore'] = str(data['spamscore'])

        mailConf['smtpinterface'] = data['smtpinterface']

        if data['blockedFiles']:
            blockedFiles = data['blockedFiles'].encode("ascii", "replace").replace(' ', '').split(',')

        mailConf['greylisting'] = data['greylisting']
        
        if data['relayfrom']:
            mailConf['relay-from'] = data['relayfrom'].encode("ascii", "replace").replace(' ', '').split(',')
        else:
            mailConf['relay-from'] = []

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
            mailConf['mailsize'] = data['maxsize'].encode("ascii", "replace")
        else:
            mailConf['mailsize'] = ""

        if data['smtprelay']:
            self.sysconf.SMTPRelay = data['smtprelay'].encode("ascii", "replace")
        else:
            self.sysconf.SMTPRelay = ""
        
        self.sysconf.Mail = mailConf
        return restartExim().addCallback(returnRoot)

    def render_content(self, ctx, data):

        if self.sysconf.Mail.get('branches'):
            branchTopology = [
                tags.p["Any mail loops or duplicates will be flagged in red. If any addresses appear red below, click on the image for a larger view."],
                tags.a(href="/auth/branchTopologyGraph", target="_blank")[
                    tags.img(src="/auth/branchTopologyGraph?size=5,5!")
                ]
            ]
        else:
            #Should not be undefined
            branchTopology = [tags.p["No branches defined"]]

        return ctx.tag[
            tags.h3[tags.img(src="/images/mailsrv.png"), " Email Server Config"],
            PageHelpers.TabSwitcher((
                (self.text.eximTabMail, 'panelMail'),
                ("Domains", "panelDomains"),
                (self.text.eximTabBlocked, 'panelBlack'),
                (self.text.eximTabWhitelist, 'panelWhite'),
                ("Catch-all", "panelCatch"),
                ("Branches", "panelBranch"),
                ("Disclaimer", "panelDisclaimer"),
            ), id="mail"),
            tags.div(id="panelMail", _class="tabPane")[tags.directive('form mailConfig')],
            tags.div(id="panelDisclaimer", _class="tabPane")[
                tags.directive('form mailDisclaimer')
            ],
            tags.div(id="panelBranch", _class="tabPane")[
                tags.h3['Branch servers'], 
                tags.p[
                    'Branch servers allow you to create a self-organising branch configuration.', 
                    'Each branch server must have every other branch server added to this section, ', 
                    'the servers will then update from one-another on a 15 minute basis. The discovered ',
                    'hierarchy will be displayed at the bottom of this page. ', 
                    tags.strong['This system does NOT interoperate with Exchange environments.']
                ],
                self.addBranch.applyTable(self), 
                branchTopology,
            ],
            tags.div(id="panelDomains", _class="tabPane")[
                PageHelpers.TabSwitcher((
                    (self.text.eximTabRelay, 'panelRelay'),
                    (self.text.eximTabHubbed, 'panelHubbed'),
                    (self.text.eximTabLocal, 'panelLocal'),
                    ("Senders", 'panelSenders'),
                    ("Rewrite", 'panelRewrite'),
                ), id="domainss"),

                tags.div(id="panelRelay", _class="tabPane")[
                    self.addRelay.applyTable(self)
                ],
                tags.div(id="panelHubbed", _class="tabPane")[
                    self.addHubbed.applyTable(self)
                ],
                tags.div(id="panelLocal", _class="tabPane")[
                    self.addLocal.applyTable(self)
                ],
                tags.div(id="panelRewrite", _class="tabPane")[
                    tags.p(_class="helpText")[
                        "Add domain rewrite rules here. When the domain appears in",
                        " the To, From, CC or BCC fields it will be rewriten to the required domain.",
                        " Note that this occurs pre-delivery and the mail routing rules will apply to the final result.",
                    ],
                    tags.br,
                    PageHelpers.dataTable(['From', 'To', 'Flags', ''], [ 
                        (fromm, to, flags,
                        tags.a(href=url.root.child("Mailserver").child("ReDelete").child(fromm), 
                            onclick="return confirm('%s');" % self.text.eximConfirmDelete)[
                                tags.img(src="/images/ex.png")
                            ]
                        ) for fromm,to,flags in self.sysconf.Mail.get('rewrites', [])
                    ], sortable=True),
                    tags.h3["Add mail rewrite"],
                    tags.directive('form mailRewrite')
                ],
                tags.div(id="panelSenders", _class = "tabPane")[
                    tags.p(_class="helpText")[
                        "Add email addresses here to allow them from the internal network"
                    ],
                    self.addSender.applyTable(self),
                ],
                PageHelpers.LoadTabSwitcher(id="domainss")
            ],
            tags.div(id="panelBlack", _class="tabPane")[
                PageHelpers.TabSwitcher((
                    ('Addresses', 'panelAddrs'), 
                    ('Subscriptions', 'panelSubs'),
                ), id = "blacklistpane"), 

                tags.div(id="panelSubs", _class="tabPane")[
                    self.addSub.applyTable(self)
                ],
                tags.div(id="panelAddrs", _class="tabPane")[
                    self.addBlacklist.applyTable(self)
                ], 
                PageHelpers.LoadTabSwitcher(id="blacklistpane")
            ],
            tags.div(id="panelWhite", _class="tabPane")[
                self.addWhitelist.applyTable(self)
            ],
            tags.div(id="panelCatch", _class="tabPane")[
                tags.h3["Catch-all Domains"],
                self.addCatchall.applyTable(self),
                tags.p[ "Enabling Catchall Domains allows a domain to catch mails addressed to non-existant users in a single account.",
                        " Each domain where this will be used must have an account named 'catchall' created." ]
            ],
            PageHelpers.LoadTabSwitcher(id="mail")
        ]

    def locateChild(self, ctx, segs):
        def returnPage(_):
            return url.root.child('Mailserver'), ()

        if segs[0] == "ReDelete":
            Utils.log.msg('%s deleted rewrite domain entry %s' % (self.avatarId.username, segs[1]))
            mc = self.sysconf.Mail
            newRelay = []
            for i in mc.get('rewrites'):
                if i[0] != segs[1]:
                    newRelay.append(i)
            mc['rewrites'] = newRelay
            self.sysconf.Mail = mc

            return restartExim().addCallback(returnPage)

        return Tools.Page.locateChild(self, ctx, segs)
