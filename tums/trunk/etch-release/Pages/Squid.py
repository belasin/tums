from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, log
from twisted.internet import defer

from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os, datetime, sha
import Tree, Settings
from Core import PageHelpers, confparse, Utils, WebUtils
from Pages import Tools

def reloadConfig(result):
    def reloadSquid(_, result):
        # Call configurator to reconfigure squid
        d = WebUtils.system('/usr/sbin/squid -k reconfigure > /dev/null 2>&1')
        return d.addCallback(lambda _: result)

    return WebUtils.system(Settings.BaseDir+'/configurator --squid').addBoth(reloadSquid, result)

def reloadGuard(result):
    return WebUtils.system(Settings.BaseDir+'/configurator --cfilter; /etc/init.d/dansguardian restart').addBoth(lambda _: result)

class AllowDomains(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Domain', 'domain')]
        domains = self.sysconf.ProxyAllowedDomains
        return headings, domains

    def addForm(self, form):
        form.addField('domain', formal.String(required=True), label = "Domain")

    def returnAction(self, data):
        Utils.log.msg('%s added allowed domain %s' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))

class AllowDest(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Destination', 'dest')]
        domains = self.sysconf.ProxyAllowedDestinations
        return headings, domains

    def addForm(self, form):
        form.addField('dest', formal.String(required=True), label = "Destination")

    def returnAction(self, data):
        Utils.log.msg('%s added allowed destination %s' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))

class AllowComp(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Address', 'host')]
        domains = self.sysconf.ProxyAllowedHosts
        return headings, domains

    def addForm(self, form):
        form.addField('host', formal.String(required=True), label = "Address")

    def returnAction(self, data):
        Utils.log.msg('%s added allowed address %s' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))

class DenyDomains(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Domain', 'domain')]
        domains = self.sysconf.ProxyBlockedDomains
        return headings, domains

    def addForm(self, form):
        form.addField('domain', formal.String(required=True), label = "Domain")

    def returnAction(self, data):
        Utils.log.msg('%s denied domain %s for web proxy' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))

class SiteWhiteList(PageHelpers.DataTable):
    def getTable(self):
        headings = [('URL', 'url')]
        domains = self.sysconf.ProxyConfig.get('cfilterurlwhitelist', [])
        return headings, domains

    def addForm(self, form):
        form.addField('url', formal.String(required=True), label = "URL")

    def returnAction(self, data):
        Utils.log.msg('%s added URL whitelist %s' % (self.avatarId.username, repr(data)))
        return reloadGuard(url.root.child('Squid'))

class RoutingACL(PageHelpers.DataTable):
    def getTable(self):
        headings = [("Source IP", 'src'), ("ACL Name", 'acl')]

        acls = self.sysconf.ProxyConfig.get('srcacls', [])
        return headings, acls

    def addForm(self, form):
        form.addField('acl', formal.String(required=True), label = "ACL Name")
        form.addField('src', formal.String(required=True), label = "Source IP")

    def returnAction(self, data):
        Utils.log.msg('%s created source ACL %s for web proxy' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))

class DomainACL(PageHelpers.DataTable):
    def getTable(self):
        headings = [("Destination Domain", 'src'), ("ACL Name", 'acl')]

        acls = self.sysconf.ProxyConfig.get('domacls', [])
        return headings, acls

    def addForm(self, form):
        form.addField('acl', formal.String(required=True), label = "ACL Name")
        form.addField('src', formal.String(required=True), label = "Destination Domain")

    def returnAction(self, data):
        Utils.log.msg('%s created domain ACL %s for web proxy' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))

class UserACL(PageHelpers.DataTable):
    def getTable(self):
        headings = [("Usernames", 'user'), ("ACL Name", 'acl')]

        acls = self.sysconf.ProxyConfig.get('aclusers', [])
        return headings, acls

    def addForm(self, form):
        form.addField('acl', formal.String(required=True), label = "ACL Name")
        form.addField('user', formal.String(required=True), label = "Users", description = "Comma separated list of users")

    def returnAction(self, data):
        Utils.log.msg('%s created user ACL %s for web proxy' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))

class RoutingGateway(PageHelpers.DataTable):
    def getTable(self):
        headings = [("Bind IP", 'gateway'), ("ACL Name", 'acl')]

        acls = self.sysconf.ProxyConfig.get('aclgateways', [])
        return headings, acls

    def addForm(self, form):
        acls = []

        for ip, i in self.sysconf.ProxyConfig.get('srcacls', []):
            acls.append((i,i))

        for n, i in self.sysconf.ProxyConfig.get('aclusers', []):
            acls.append((i,i))

        for n, i in self.sysconf.ProxyConfig.get('domacls', []):
            acls.append((i,i))


        form.addField('acl', formal.String(), formal.widgetFactory(formal.SelectChoice, options = acls), label = "ACL Name", 
                description = "Select the ACL to apply this rule to"),
 
        #form.addField('acl', formal.String(required=True), label = "ACL Name")
        form.addField('gateway', formal.String(required=True), label = "Bind IP", 
            description = "Local internet IP address to bind for this ACL")

    def returnAction(self, data):
        Utils.log.msg('%s created ACL gateway %s for web proxy' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))

class PermissionACL(PageHelpers.DataTable):
    def getTable(self):
        headings = [
            ("ACLs", 'acl'),
            ("Permission", 'perms')
        ]

        acls = self.sysconf.ProxyConfig.get('aclperms', [])
        return headings, acls

    def addForm(self, form):
        acls = []

        for ip, i in self.sysconf.ProxyConfig.get('srcacls', []):
            acls.append((i,i))

        for n, i in self.sysconf.ProxyConfig.get('aclusers', []):
            acls.append((i,i))

        for n, i in self.sysconf.ProxyConfig.get('domacls', []):
            acls.append((i,i))


        form.addField('acl', formal.Sequence(formal.String()), formal.widgetFactory(formal.CheckboxMultiChoice, options = acls), label = "ACLs", 
                description = "Select the ACL(s) to apply this rule to"),
 
        #form.addField('acl', formal.String(required=True), label = "ACL Name")
        form.addField('perms', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = [
            ('deny', 'deny'), 
            ('allow', 'allow')
        ]), label = "Permission")

        form.data['perms'] = 'deny'

    def addAction(self, data):
        print data

        dta = self.sysconf.ProxyConfig
        perms = dta.get('aclperms', [])

        perms.append([' '.join(data['acl']), data['perms']])
        
        dta['aclperms'] = perms
        self.sysconf.ProxyConfig = dta

    def returnAction(self, data):
        Utils.log.msg('%s created ACL permission set %s for web proxy' % (self.avatarId.username, repr(data)))
        return reloadConfig(url.root.child('Squid'))


class HostWhiteList(PageHelpers.DataTable):
    def getTable(self):
        headings = [('IP', 'ip')]
        domains = self.sysconf.ProxyConfig.get('cfilterhostwhitelist', [])
        return headings, domains

    def addForm(self, form):
        form.addField('ip', formal.String(required=True), label = "IP")

    def returnAction(self, data):
        Utils.log.msg('%s added IP whitelist %s' % (self.avatarId.username, repr(data)))
        return reloadGuard(url.root.child('Squid'))


class Page(Tools.Page):
    docFactory  = loaders.xmlfile('overview.xml', templateDir=Settings.BaseDir+'/templates')

    daymap = {
        'M':'Monday',
        'T':'Tuesday',
        'W':'Wednesday',
        'H':'Thursday',
        'F':'Friday',
        'A':'Saturday',
        'S':'Sunday',
    }

    def __init__(self, avatarId, db, updateSearch = None, *a, **kw):
        Tools.Page.__init__(self, avatarId, db, *a, **kw)
        self.updateSearch = updateSearch
        self.addDom      = AllowDomains(self, 'AllowDomains',  'domain', 'ProxyAllowedDomains')
        self.addDest     = AllowDest(self, 'AllowDest',  'destination', 'ProxyAllowedDestinations')
        self.addComp     = AllowComp(self, 'AllowComp',  'host', 'ProxyAllowedHosts')
        self.addBlock    = DenyDomains(self, 'DenyDomain',  'domain', 'ProxyBlockedDomains')

        self.cfilterSWL  = SiteWhiteList(self, 'SiteWhiteList',  'URL', 'ProxyConfig', 'cfilterurlwhitelist')
        self.cfilterHWL  = HostWhiteList(self, 'HostWhiteList',  'IP address', 'ProxyConfig', 'cfilterhostwhitelist')

        self.routingACL  = RoutingACL(self, 'RoutingACL',  'routing ACL', 'ProxyConfig', 'srcacls')
        self.domainACL  = DomainACL(self, 'DomainACL',  'domain ACL', 'ProxyConfig', 'domacls')
        self.routingGateway  = RoutingGateway(self, 'RoutingGateway',  'ACL gateway', 'ProxyConfig', 'aclgateways')
        self.permissionACL  = PermissionACL(self, 'ACLPermission',  'ACL permission', 'ProxyConfig', 'aclperms')
        self.userACL  = UserACL(self, 'UserACL',  'user ACL', 'ProxyConfig', 'aclusers')

    def flushObject(self, name):
        def flushDb(ret):
            return self.db[4].deleteFile(name)
        return WebUtils.system('rm -rf /var/lib/samba/updates/%s' % sha.sha(name).hexdigest()).addBoth(flushDb)

    def locateChild(self, ctx, segs):
        if segs[0] == "DeleteTime":
            np = self.sysconf.ProxyConfig

            del np['timedaccess'][int(segs[1])]

            self.sysconf.ProxyConfig = np

            return reloadConfig(url.root.child('Squid')), ()
        
        if segs[0] == "Flush":
            return self.flushObject(segs[1]).addBoth(lambda _: url.root.child('Squid')), ()

        if segs[0] == "Search":
            return Page(self.avatarId, self.db, updateSearch = segs[1]), ()

        return Tools.Page.locateChild(self, ctx, segs)

    def form_contentFilter(self, data):
        form = formal.Form()
        
        form.addField('porn', formal.Boolean(), label = "Pornography")
        form.addField('profanity', formal.Boolean(), label = "Profanity")
        form.addField('drugs', formal.Boolean(), label = "Drugs")
        form.addField('hate', formal.Boolean(), label = "Violence/Hate")
        form.addField('gambling', formal.Boolean(), label = "Gambling")
        form.addField('hacking', formal.Boolean(), label = "Hacking")
        form.addField('p2p', formal.Boolean(), label = "P2P sites")
        form.addField('webmail', formal.Boolean(), label = "Webmail")
        form.addField('chat', formal.Boolean(), label = "Chat sites")
        form.addField('news', formal.Boolean(), label = "News sites")
        form.addField('dating', formal.Boolean(), label = "Dating sites")
        form.addField('sport', formal.Boolean(), label = "Sport sites")
        form.addField('games', formal.Boolean(), label = "Games")

        for item in self.sysconf.ProxyConfig.get('blockedcontent', []):
            form.data[item] = True

        form.addAction(self.submitFilter)
        return form

    def submitFilter(self, ctx, form, data):
        k = self.sysconf.ProxyConfig

        blocks = []
        for item, state in form.data.items():
            print item, state
            if state == True:
                blocks.append(item)

        k['blockedcontent'] = blocks

        self.sysconf.ProxyConfig = k

        return reloadGuard(url.root.child('Squid'))

    def form_authentication(self, data):
        form = formal.Form()

        form.addField('adauth', formal.Boolean(), label = "Active Directory authentication")

        form.addField('adserv', formal.String(), label = "Active Directory Server")
        form.addField('addom', formal.String(), label = "Active Directory Domain")

        form.addField('contentfilter', formal.Boolean(), label = "Content filter")

        form.addField('advanced', formal.Boolean(), label = "Update cache",
            description = "Enable update caching support.")

        form.addField('captive', formal.Boolean(), label = "Captive portal",
            description = "Enable captive portal (Requires Update Cache to be enabled).")

        form.addField('captiveblock', formal.Boolean(), label = "Captive block",
            description = "Check this if you want the default captive portal firewall policy to be blocking. By default all traffic will be accepted from authenticated computers")

        form.addField('bindaddr', formal.String(), label = "Exit address", 
            description = "The IP address to use for outbound connections. Leave blank for default")

        form.addAction(self.submitAuth)

        k = self.sysconf.ProxyConfig
        data = {}
        if k.get('adauth', ''):
            data['ldapauth'] = False
            data['adauth'] = True
        else:
            data['ldapauth'] = True
            data['adauth'] = False

        data['contentfilter'] = k.get('contentfilter', False)
        data['captive'] = k.get('captive', False)
        data['captiveblock'] = k.get('captiveblock', False)

        data['adserv'] = k.get('adserver', u'').encode()
        data['addom'] = k.get('addom', u'').encode()

        if k.get('updates'):
            u = k['updates']

            data['advanced'] = u.get('enabled', False)

        data['bindaddr'] = k.get('bindaddr', '')

        form.data = data

        return form

    def submitAuth(self, ctx, form, data):
        k = self.sysconf.ProxyConfig
        if data['adauth']:
            k['adauth'] = True
        else:
            k['adauth'] = False
    
        if data['bindaddr']:
            k['bindaddr'] = data['bindaddr'].encode()

        if data['adserv']:
            k['adserver'] = data['adserv'] or ""
            k['addom'] = data['addom'] or ""
        else:
            k['adauth'] = False

        k['captive'] = data['captive']
        k['captiveblock'] = data['captiveblock']
        k['contentfilter'] = data['contentfilter']

        k['updates'] = {
            'enabled': data['advanced'],
            'maxdisk': '95',
            'maxspeed': '0'
        }

        self.sysconf.ProxyConfig = k

        def squidRestart(_):
            print _
            return reloadConfig(url.root.child('Squid'))

        return WebUtils.system('/usr/local/tcs/tums/configurator --shorewall; shorewall restart').addBoth(squidRestart)

    def form_addTime(self, data):
        acls = []

        for ip, i in self.sysconf.ProxyConfig.get('srcacls', []):
            acls.append((i,i))

        for n, i in self.sysconf.ProxyConfig.get('aclusers', []):
            acls.append((i,i))

        for n, i in self.sysconf.ProxyConfig.get('domacls', []):
            acls.append((i,i))

        form = formal.Form(self.submitTime)[        
            formal.Field('allow', formal.Boolean(), label = "Allow",
                description = "Allow traffic at these times"),
            formal.Field('from', formal.Time(required=True), label = "From time", 
                description = "Starting time (24 hour format)"),
            formal.Field('to', formal.Time(required=True), label = "To time", 
                description = "Ending time (24 hour format), must be later than the starting time and must not overlap midnight"),

            formal.Field('domain', formal.String(), label = "Domain", 
                description = "Apply this rule to a specific domain"), 

            formal.Field('exacl', formal.String(), formal.widgetFactory(formal.SelectChoice, options = acls), label = "Extra ACL", 
                description = "Apply this rule to a specific other ACL"),
            
            formal.Group('Days')[
                [ formal.Field(i, formal.Boolean(), label = i) for i in PageHelpers.days ]
            ]
        ]
        form.data['from'] = datetime.time(0,0)
        form.data['to'] = datetime.time(23,59)
        form.addAction(self.submitTime)
        return form

    def submitTime(self, ctx, form, data):
        k  = self.sysconf.ProxyConfig

        # Check how sane our times are...
        fr = (data['from'].hour *100) + data['from'].minute
        too = (data['to'].hour *100) + data['to'].minute

        if too < fr:
            return url.root.child('Squid').child('InsanityFailure')
        
        daymapinv = dict([(j,i) for i,j in self.daymap.items()])
            
        days = []
        for i in PageHelpers.days:
            if data["Days.%s" % i]:
                days.append(daymapinv[i])

        # make sure we have a configuration node
        if not k.get('timedaccess'):
            k['timedaccess'] = []

        if data['domain']:
            if data['domain'][0] != ".":
                domain = ".%s" % data['domain'].encode()
            else:
                domain = data['domain'].encode()
        else:
            domain = None

        # Append our new entry into the configuration
        k['timedaccess'].append((
            data['allow'],
            " ".join(days),
            "%s-%s" % ( str(data['from'])[:-3], str(data['to'])[:-3] ),
            domain,
            data['exacl']
        ))

        self.sysconf.ProxyConfig = k
        return reloadConfig(url.root.child('Squid'))
        
    def getData(self):
        #allow_domains  allow_dst  allow_hosts
        doms = self.sysconf.ProxyAllowedDomains
        dsts = self.sysconf.ProxyAllowedDestinations
        ips = self.sysconf.ProxyAllowedHosts
        bdoms = self.sysconf.ProxyBlockedDomains

        # Read timed access data
        l = self.sysconf.ProxyConfig
        times = []
        cnt = 0
        for action, days, time, domain, exacl in l.get('timedaccess', []):
            times.append((
                action and "Allow" or "Deny", 
                ", ".join([self.daymap[i] for i in days.split()]),
                time,
                domain or "", 
                exacl or "",
                tags.a(href="DeleteTime/%s/" % (cnt,), onclick="return confirm('Are you sure you want to delete this entry?');")[
                    tags.img(src="/images/ex.png")
                ]
            ))
            cnt += 1 

        domains = []
        cnt = 0 
        for ln in doms:
            l = ln.strip('\n')
            if l:
                domains.append([l, tags.a(href="Delete/Domain/%s/" % cnt, onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")] ] )
            cnt += 1

        bdomains = []
        cnt = 0 
        for ln in bdoms:
            l = ln.strip('\n')
            if l:
                bdomains.append([l, tags.a(href="Delete/BDomain/%s/" % cnt, onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")] ] )
            cnt += 1

        destinations = []
        cnt = 0
        for ln in dsts:
            l = ln.strip('\n')
            if l:
                destinations.append([l, tags.a(href="Delete/Destination/%s/" % cnt, onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")] ] )
            cnt += 1

        hosts = []
        cnt = 0
        for ln in ips:
            l = ln.strip('\n')
            if l:
                hosts.append([l, tags.a(href="Delete/Host/%s/" % cnt, onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")] ] )
            cnt += 1

        return domains, destinations, hosts, bdomains, times

    def form_searchCache(self, ctx):
        form = formal.Form()

        form.addField('filename', formal.String(required=True), label = "Filename")

        form.addAction(self.submitUpdateSearch)

        return form

    def submitUpdateSearch(self, ctx, form, data):
        fname = data['filename'].encode()

        return url.root.child('Squid').child('Search').child(fname)

    def render_updateCache(self, ctx, data):
        def returnPage(res):
            return ctx.tag[
                tags.directive('form searchCache'), 
                tags.h3["Search results"], 
                PageHelpers.dataTable(
                    (
                        ('str', 'Category'),
                        ('str', 'Filename'),
                        ('int', 'Hits'),
                        ('int', 'Size'), 
                        ('', '')
                    ),
                    [(
                        i[0],
                        i[1],
                        i[2] or 0,
                        Utils.intToH(i[3] or 0),
                        tags.a(href=url.root.child('Squid').child('Flush').child(i[1]))[tags.img(src='/images/ex.png')]
                    ) for i in res],
                    sortable = True
                )
            ]

        if self.updateSearch:
            # Perform a LIKE search
            return self.db[4].findFiles('%%%s%%' % self.updateSearch).addBoth(returnPage)
        return ctx.tag[
            tags.directive('form searchCache')
        ]

    def render_content(self, ctx, data):
        squidData = self.getData()
        tabs = [
            ('Setup', 'panelProxySetup'),
            ('Content', 'panelContent'),
            ('Allow', 'panelAllows'),
            ('Block Domain', 'panelBdom'),
            ('Access times', 'panelAtime'),
            ('ACL Routing', 'panelRouting'),
        ]
        updatePanel = ""
        k = self.sysconf.ProxyConfig
        if k.get('updates'):
            if k['updates'].get('enabled'):
                tabs.append( ('Updates', 'panelUpdate') )
                updatePanel = tags.div(id="panelUpdate", _class="tabPane")[
                    tags.h3["Updates Cache"],
                    tags.invisible(render=tags.directive('updateCache'))
                ]

        return ctx.tag[
            tags.h3[tags.img(src='/images/proxy.png'), " Web Proxy"],
            PageHelpers.TabSwitcher((
                tabs
            ), id="proxy"),
            tags.div(id="panelContent", _class="tabPane")[
                PageHelpers.TabSwitcher((
                    ('Content filters', 'panelCFilter'),
                    ('Site Whitelist', 'panelWlist'),
                    ('Host Whitelist', 'panelHWlist')
                ), id="pcfilter"),
                tags.div(id="panelCFilter", _class="tabPane")[
                    tags.h3["Blocked content"],
                    tags.directive('form contentFilter'),
                ],
                tags.div(id="panelWlist", _class="tabPane")[
                    tags.h3["Site Whitelist"], 
                    self.cfilterSWL.applyTable(self)
                ],
                tags.div(id="panelHWlist", _class="tabPane")[
                    tags.h3["Host Whitelist"],
                    self.cfilterHWL.applyTable(self)
                ],
                PageHelpers.LoadTabSwitcher(id="pcfilter")
            ],
            tags.div(id="panelProxySetup", _class="tabPane")[
                tags.h3["Proxy setup"],
                tags.directive('form authentication'),
            ],
            tags.div(id="panelAllows", _class="tabPane")[
                PageHelpers.TabSwitcher((
                    ('Allow Domain', 'panelAdom'),
                    ('Allow Destination', 'panelAdest'),
                    ('Allow Computer', 'panelAcomp'),
                ), id="allows"),
                tags.div(id="panelAdom", _class="tabPane")[
                    tags.h3["Allowed Domains"],
                    self.addDom.applyTable(self)
                ],
                tags.div(id="panelAdest", _class="tabPane")[
                    tags.h3["Allowed Destination Networks"],
                    self.addDest.applyTable(self)
                ],
                tags.div(id="panelAcomp", _class="tabPane")[
                    tags.h3["Allowed Computers"],
                    self.addComp.applyTable(self)
                ],
                PageHelpers.LoadTabSwitcher(id="allows")
            ],
            tags.div(id="panelAtime", _class="tabPane")[
                tags.h3["Access times"],
                PageHelpers.dataTable(['Permission', 'Days', 'Time', 'Domain', 'ACL', ''], squidData[4], sortable=True),
                tags.h3["Add time range"],
                tags.directive('form addTime'),
            ],
            tags.div(id="panelRouting", _class="tabPane")[
                PageHelpers.TabSwitcher((
                    ('User ACL', 'panelACLU'),
                    ('Source ACL', 'panelACLS'),
                    ('Domain ACL', 'panelACLD'),
                    ('ACL Gateway', 'panelACLG'),
                    ('Permission ACL', 'panelACLP'),
                ), id="acls"),
                tags.div(id="panelACLU", _class="tabPane")[
                    tags.h3["User ACL"],
                    tags.p["Manage username ACL's. These ACL's can then be used for timed access or source routing"],
                    self.userACL.applyTable(self),
                ],
                tags.div(id="panelACLS", _class="tabPane")[
                    tags.h3["Source ACL"],
                    tags.p["Manage source IP ACL's. These ACL's can then be used for timed access or source routing"],
                    self.routingACL.applyTable(self),
                ],
                tags.div(id="panelACLD", _class="tabPane")[
                    tags.h3["Domain ACL"],
                    tags.p["Manage destination domain ACL's. These ACL's can then be used for timed access or source routing"],
                    self.domainACL.applyTable(self),
                ],
                tags.div(id="panelACLG", _class="tabPane")[
                    tags.h3["ACL routes"], 
                    self.routingGateway.applyTable(self)
                ],
                tags.div(id="panelACLP", _class="tabPane")[
                    tags.h3["ACL permissions"], 
                    self.permissionACL.applyTable(self)
                ],
                PageHelpers.LoadTabSwitcher(id="acls")
            ],
            tags.div(id="panelBdom", _class="tabPane")[
                tags.h3["Blocked Domains"],
                self.addBlock.applyTable(self)
            ],
            updatePanel,
            PageHelpers.LoadTabSwitcher(id="proxy")
        ]
