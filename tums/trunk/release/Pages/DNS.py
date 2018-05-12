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

class EditDNS(Tools.Page):
    def __init__(self, avatarId = None, db = None, domain="", *a, **kw):
        self.domain = domain
        PageHelpers.DefaultPage.__init__(self,avatarId, db, *a, **kw)

    def form_editZone(self, data):
        form = formal.Form()

        form.addField('master', formal.Boolean(), label = "Master")
        form.addField('notify', formal.Boolean(), label = "Notify slaves")
        form.addField('update', formal.String(), label = "Update", description="Comma sepparated list of hosts allowed to update this zone")

        form.addField('ns', formal.String(), label = "Nameservers", description="Comma sepparated list of authoritive servers for this zone")

        form.addField('forward', formal.String(), label = "Forwarders", description="Comma sepparated list of servers to forward requests to for this zone")

        # populate form
        Z = self.sysconf.General['zones'][self.domain]
        
        form.data['ns'] = ', '.join(Z['ns'])
        form.data['update'] = ', '.join(Z['update'])
        
        form.data['master'] = "type master" in Z['options']
        form.data['notify'] = "notify no" not in Z['options']


        form.data['forward'] = Z.get('forward', '')
        
        form.addAction(self.submitZone)
        return form

    def submitZone(self, ctx, form, data):
        G = self.sysconf.General
        # save form to zone options
        
        type = data['master'] and "master" or "slave"
        options = ['type %s' % type]

        if data['forward']:
            type = 'forward'
            options = ['type %s' % type]
            G['zones'][self.domain]['forward'] = data['forward']
        else:
            G['zones'][self.domain]['forward'] = []
            

        if data['notify']:
            options.append('notify yes')
        else:
            options.append('notify no')
        
        G['zones'][self.domain]['options'] = options
        G['zones'][self.domain]['update'] = data['update'].encode("ascii", "replace").replace(' ','').split(',')
        G['zones'][self.domain]['ns'] = data['ns'].encode("ascii", "replace").replace(' ','').split(',')
        
        self.sysconf.General = G

        def returnRoot(_):
            print _
            return url.root.child('DNS')#.child('Edit').child(self.domain)

        return WebUtils.restartService('bind').addCallback(returnRoot)

    def form_addRecord(self, data):
        recordTypes = [
            "CNAME",
            "A",
            "AAAA",
            "NS",
            "MX"
        ]
        
        form = formal.Form()
        
        form.addField('type', formal.String(required=True), formal.widgetFactory(formal.SelectChoice,
            options = [(i,i) for i in recordTypes]), label = "Type")
        form.addField('host', formal.String(), label = "Host", description="Hostname or blank for a record in the base FQDN")
        form.addField('data', formal.String(), label = "Data", description="Content of the record")
        form.addField('prio', formal.Integer(), label = "Priority", description="Priority of MX record")
        
        form.addAction(self.submitRecForm)
        return form

    def submitRecForm(self, ctx, form, data):
        G = self.sysconf.General

        if data['type'] == "MX":
            if not data['prio']:
                data['prio'] = 1

        # Check users blood alcohol level
        if not data['host']:
            host = "%s." % self.domain
        else:
            host = data['host'].encode("ascii", "replace").strip('.')

        if self.domain in host:
            host = "%s." % self.domain
        
        record = "%(host)s %(type)s%(prio)s %(data)s" % {
            "type": data['type'].encode("ascii", "replace"),
            "prio": data['prio'] and " %s"%data['prio'] or "",
            "host": host,
            "data": data['data'].encode("ascii", "replace")
        }
        
        G['zones'][self.domain]['records'].append(record)
        
        self.sysconf.General = G
        def returnRoot(_):
            print _
            return url.root.child('DNS').child('Edit').child(self.domain)

        return WebUtils.restartService('bind').addCallback(returnRoot)

    def locateChild(self, ctx, segs):
        if '.' in segs[0] and len(segs) < 3:
            return EditDNS(self.avatarId, self.db, segs[0]), ()

        if len(segs)>1 and segs[1] == "Delete":
            G = self.sysconf.General
            print self.avatarId.username, " deleting zone record", G['zones'][segs[0]]['records'][int(segs[2])]
            del G['zones'][segs[0]]['records'][int(segs[2])]
            self.sysconf.General = G
            def null(_):
                print "Restart done"
                return url.root.child('DNS').child('Edit').child(segs[0]),  ()
            return WebUtils.restartService('bind').addBoth(null)
        
        return url.root.child('DNS'), ()

    def parseZone(self):
        records = []
        try:
            zonefile = open('/etc/bind/pri/%s.zone' % self.domain)
        
            last = self.domain
            SOA = True  # Flag for currently processing SOA (header)
            for ln in zonefile:
                l = ln.strip('\n')
                if not l:
                    continue
                if l[0]=="$":
                    continue

                if "SOA" in l:
                    # Never process SOA 
                    continue
            
                if SOA and "NS" not in l:
                    continue
                else:
                    SOA = False
            
                # We start hitting useful records. 
                if l[0] == " ": # starts with a space
                    if last == self.domain:
                        l = last+'. '+l
                    else:
                        l = last+l
                else:
                    last = l.split()[0]
            
                rec = l.split(None, 2)
                nrec = [rec[0], rec[1], rec[2], ""]
                trec = ' '.join(nrec)

                brec = trec.replace(' ', '')
                found = False
                for r in self.sysconf.General['zones'][self.domain].get('records', []):
                    existRec = r.replace(' ', '').lower()
                    if brec.lower() == existRec:
                        found = True
                if found:
                    continue

                if (trec not in records) and (nrec[1]!="NS"):
                    records.append(trec)
        except Exception, e:
            print e
        return records

    def render_content(self, ctx, data):
        records = []
        if not self.sysconf.General['zones'][self.domain]['records']:
            records = self.parseZone()

        for rec in self.sysconf.General['zones'][self.domain]['records']:
            # Ditch duplicates automatically
            if rec not in records:
                records.append(rec)

        # Save parsed records
        G = self.sysconf.General
        G['zones'][self.domain]['records'] = records
        self.sysconf.General = G 

        # Make the table
        rnum = 0
        nrecords = []
        for r in records:
            l = r.split()
            
            if len(l)>3 and "MX" in r:
                # Has MX
                thisRec = [l[0], l[1], l[3], l[2]]
            else:
                thisRec = l
                thisRec.append("")
            
            thisRec.append(tags.a(href="Delete/%s/"%rnum)["Delete"])
            
            rnum += 1
            nrecords.append(thisRec)
        
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Editing zone %s" % self.domain],
            PageHelpers.TabSwitcher((
                ('Records', 'panelDNSRecs'),
                ('Add Record', 'panelDNSAdd'),
                ('Edit Options', 'panelDNSOpt'),
            )),
            tags.div(id="panelDNSRecs", _class="tabPane")[
                PageHelpers.dataTable(["Host", "Type", "Data", "Priority", ""],
                    nrecords, sortable = True
                ),
            ],
            tags.div(id="panelDNSAdd", _class="tabPane")[
                tags.h3["Add new record"],
                tags.directive('form addRecord'),
            ],
            tags.div(id="panelDNSOpt", _class="tabPane")[
                tags.h3["Edit zone options"],
                tags.directive('form editZone')
            ],
            PageHelpers.LoadTabSwitcher()
        ]

class DyndnsEntry(PageHelpers.DataTable):
    provMap = {
        "ZoneEdit"      : 'zoneedit1',
        "EasyDNS"       : 'easydns',
        "DynDNS"        : 'dyndns2',
        "DSL Reports"   : 'dslreports1',
        "DNS Park"      : 'dnspark',  
        "Namecheap.com" : 'namecheap',
        'Thusa DNS'     : 'thusadns',
 
        'zoneedit1'     : "ZoneEdit",
        'easydns'       : "EasyDNS",
        'dyndns2'       : "DynDNS",
        'dslreports1'   : "DSL Reports",
        'dnspark'       : "DNS Park",
        'namecheap'     : "Namecheap.com",
        'thusadns'      : 'Thusa DNS'
    }

    def getTable(self):
        dyndns = []
        
        for entry in self.sysconf.General.get('dyndns', []):
            provider = self.provMap[entry[0]]
            dyndns.append([provider, entry[1], entry[2], entry[3], entry[4]])

        headings = [
            ("Provider", 'provider'),
            ("Server", 'server'), 
            ("Hostname", 'hostname'),
            ("User", "user"), 
            ("Password", 'password'), 
        ]

        return headings, dyndns

    def addForm(self, form):
        providers = [(i,i) for i in [
            "ZoneEdit",
            "EasyDNS",
            "DynDNS",
            "DSL Reports",
            "DNS Park",
            "Namecheap.com",
            "Thusa DNS"
        ]]
 
        form.addField('provider', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = providers), 
            label = "Provider")
        
        form.addField('server', formal.String(required=True), label = "Server")
        form.addField('hostname', formal.String(required=True), label = "Hostname")
        form.addField('user', formal.String(required=True), label = "Username")
        form.addField('password', formal.String(required=True), label = "Password")

    def addAction(self, data):
        Utils.log.msg('%s created dynamic DNS entry %s' % (self.avatarId.username, repr(data)))
        
        G = self.sysconf.General

        entries = G.get('dyndns', [])
        entries.append([
            self.provMap[data['provider'].encode("ascii", "replace")], 
            data['server'].encode("ascii", "replace"), 
            data['hostname'].encode("ascii", "replace"),
            data['user'].encode("ascii", "replace"),
            data['password'].encode("ascii", "replace")
        ])
        
        G['dyndns'] = entries

        self.sysconf.General = G
        
    def deleteItem(self, item):
        G = self.sysconf.General

        Utils.log.msg('%s deleted dynamic DNS entry %s' % (self.avatarId.username, G['dyndns'][item]))

        del G['dyndns'][item]

        self.sysconf.General = G

    def returnAction(self, data):
        return WebUtils.restartService('ddclient').addBoth(lambda _: url.root.child('DNS'))


class Page(Tools.Page):
    addSlash = True
    
    childPages = {
        'Edit': EditDNS,
    }
    def __init__(self, *a, **kw):
        Tools.Page.__init__(self, *a, **kw)
        self.DynDNS = DyndnsEntry(self, 'DynDNS', 'dynamic DNS entry')

    def childFactory(self, ctx, seg):
        if seg in self.childPages.keys():
            return self.childPages[seg](self.avatarId, self.db)
        else:
            return PageHelpers.DefaultPage.childFactory(self, ctx, seg)
    
    def locateChild(self, ctx, segs):
        if segs[0] == "Delete":
            G = self.sysconf.General
            print self.avatarId.username, " deleting zone ", segs[1]
            
            if segs[1] == self.sysconf.Domain:
                G['zones'][segs[1]] = {}
            else:
                del G['zones'][segs[1]]
            self.sysconf.General = G
            def null(_):
                return url.root.child('DNS'),  ()
            return WebUtils.restartService('bind').addCallbacks(null, null)

        return PageHelpers.DefaultPage.locateChild(self, ctx, segs)
    
    
    def form_nameservers(self, data):
        form = formal.Form()
        form.addField('forward', formal.String(), label = "DNS Forward", 
            description = "DNS forwarders (comma separated) that the Vulani internal DNS server should use for non-authoritive requests. This is usualy your upstream DNS")
        
        form.addField('sysresolv', formal.String(), label = "DNS Servers",
            description = "The DNS server which this server should perform it's own lookups from. This is usualy itself (127.0.0.1) or if the internal DNS is unused then it is the upstream DNS servers")
        
        form.data['forward'] = ','.join(self.sysconf.ForwardingNameservers)
        
        if self.sysconf.General.get('sysresolv', []):
            form.data['sysresolv'] = ','.join(self.sysconf.General['sysresolv'])
        else:
            form.data['sysresolv'] = '127.0.0.1'
        
        form.addAction(self.submitNSForm)
        return form

    def submitNSForm(self, ctx, form, data):
        Utils.log.msg('%s changed forwarding nameservers %s' % (self.avatarId.username, repr(data)))
        forward = data['forward'].replace(' ', '').replace('\n', '').replace('\r', '').split(',')
        self.sysconf.ForwardingNameservers = forward
        
        gen = self.sysconf.General
        
        sysresolv = data['sysresolv'].replace(' ', '').replace('\n', '').replace('\r', '').split(',')
        gen['sysresolv'] = sysresolv
        self.sysconf.General = gen
        
        def res(_):
            return url.root.child('DNS')
        return WebUtils.restartService('bind').addCallbacks(res, res)

    def form_addZone(self, data):
        form = formal.Form()
        
        form.addField('zone', formal.String(required=True), label = "Domain")
        form.addField('master', formal.Boolean(), label = "Master")
        form.addField('update', formal.String(), label = "Update", description ="If this server is not the master, enter the master servers IP here")
        form.addField('forward', formal.String(), label = "Forward", description ="Forward requests for this zone to another server")
        
        form.data['master'] = True
        
        form.addAction(self.submitZone)
        return form

    def submitZone(self, ctx, form, data):
        D = self.sysconf.General
        
        type = data['master'] and "master" or "slave"
        options = ['type %s' % type, 'notify no']

        if data['forward']:
            type = 'forward'
            options = ['type %s' % type]
            
        if data['update']:
            update = ['127.0.0.1', data['update'].encode("ascii", "replace")]
        else:
            update = ['127.0.0.1']
        
        defaultZone = {
            'update': update,
            'options': options, 
            'ns': [self.sysconf.ExternalName],
            'records' : [], 
            'forward' : data['forward']
        }
        
        if D.get('zones'):
            D['zones'][data['zone'].encode("ascii", "replace")] = defaultZone
        else:
            D['zones'] = {
                data['zone'].encode("ascii", "replace"): defaultZone
            }
        self.sysconf.General = D

        def next(_):
            return url.root.child('DNS')
        return WebUtils.restartService('bind').addBoth(next)

    def render_content(self, ctx, data):
        Utils.log.msg('%s opened Tools/DNS' % (self.avatarId.username))

        # Try fix up our zones
        ourBase = self.sysconf.Domain
        if ourBase not in self.sysconf.General.get('zones', {}).keys():
            try:
                sc = self.sysconf.General.get('zones', {})
                sc[ourBase] = {
                    'update': ['127.0.0.1'], 
                    'options': ['type master', 'notify no'], 
                    'ns': ["%s.%s" % (self.sysconf.Hostname, ourBase)],
                    'records': []
                }
                fi = open('/etc/bind/pri/%s.zone' % ourBase)
                for i in fi:
                    n = i.strip().split()
                    if n[0] == "A" and i[0] == " ":
                        sc[ourBase]['records'].append("%s.    %s" % (ourBase, i.strip().strip('\n')))
                        continue 
                    if " CNAME " in i:
                        sc[ourBase]['records'].append(i.strip('\n').strip())
                    if " A " in i:
                        sc[ourBase]['records'].append(i.strip('\n').strip())

                G = self.sysconf.General
                G['zones'] = sc
                self.sysconf.General = G
            except Exception, e :
                print "Error parsing zone", e
        
        zones = []
        for i in self.sysconf.General.get('zones', {}).keys():
            if self.sysconf.General['zones'][i]:
                if "type master" in self.sysconf.General['zones'][i].get('options', []):
                    ztype = "Master"
                elif "type slave" in self.sysconf.General['zones'][i].get('options', []):
                    ztype = "Slave"
                elif "type forward" in self.sysconf.General['zones'][i].get('options', []):
                    ztype = "Forward to " + self.sysconf.General['zones'][i].get('forward', '')

                zones.append([
                    i, 
                    ztype, 
                    self.sysconf.General['zones'][i]['ns'][0], 
                    [
                        tags.a(href="Edit/%s/"%i)["Edit"],
                        " ",
                        tags.a(href="Delete/%s/" % (i,) ,
                            onclick="return confirm('Are you sure you want to delete this entry?');")[
                                tags.img(src="/images/ex.png")
                            ]
                    ]
                ])
 
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " DNS"],
            PageHelpers.TabSwitcher((
                ('DNS Servers', 'panelDNSServ'),
                ('DNS Zones', 'panelDNSZone'),
                ('Dynamic DNS', 'panelDynDNS'), 
            )),
            tags.div(id="panelDynDNS", _class="tabPane")[
                tags.h3["Dynamic DNS"], 
                self.DynDNS.applyTable(self)
            ], 
            tags.div(id="panelDNSServ", _class="tabPane")[
                tags.h3["DNS Servers"], 
                tags.directive('form nameservers')
            ], 
            tags.div(id="panelDNSZone", _class="tabPane")[
                tags.h3["DNS Zones"],
                PageHelpers.dataTable(["Zone", "Type", "NS", ''],zones, sortable = True),
                tags.h3["Add Zone"],
                tags.directive('form addZone')
            ],
            PageHelpers.LoadTabSwitcher()
        ]
        
