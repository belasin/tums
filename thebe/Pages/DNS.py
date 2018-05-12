from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha

from custom import Widgets

from twisted.internet import utils
from twisted.internet.defer import deferredGenerator, waitForDeferred as wait
from twisted.internet import defer


from lib import system, log, PageBase

from LdapDNS import DNS

class dnsFragment(pages.AthenaFragment):    
    dns = DNS.DNS('o=THUSA', 'thusa')

    def document(self):
        return pages.template('domain_live.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    @pages.exposeAthena
    def getDomains(self):
        def returnDomains(data):
            # data = self.dns.getDomains()
            # We need our results in unicode lists
            newData = [unicode(i[1]) for i in data]
            # ok that was easy...
            return newData

        if 1 in self.avatarId.gids:
            return [unicode(i) for i in self.dns.getDomains()]
        
        return self.enamel.storage.getDomainsInGroup(self.avatarId.gids).addCallback(returnDomains)

    @pages.exposeAthena 
    def deleteRecord(self, domain):
        # Delete the real record
        print "Deleting", domain
        tr = self.dns.getSubs(domain.encode())
        for dom in tr:
            print "removing subdomain", dom
            self.dns.deleteDomain(dom)
        self.dns.deleteDomain(domain.encode())
        def done(_):
            return True

        # Delete the DB reference
        def deleteMem(did):
            # Get the ID for the domain we just added
            return defer.DeferredList([
                self.enamel.storage.deleteDomainMembership(did[0]),
                self.enamel.storage.deleteDomain(did[0]),
                system.system('echo "User %s deleted domain %s." | mail -s "Domain deleted %s" support@thusa.co.za' % (
                    self.avatarId.username,
                    domain.encode(),
                    domain.encode()
                ))
            ]).addBoth(done)
        return self.enamel.storage.getDomainByName(domain.encode()).addBoth(deleteMem)

    @pages.exposeAthena
    def getDomainDetail(self, dom):
        data = self.dns.printableFlatRecords(dom.encode())

        # Build our JSON
        newData = []
        for i in data:
            for j in i[2]:
                if i[1] != "MX":
                    newData.append({
                        u'domain':unicode(i[0]), 
                        u'type':unicode(i[1]), 
                        u'data':unicode(j)
                    })

        return newData

    @pages.exposeAthena
    def getDomainDetailMX(self, dom):
        data = self.dns.printableFlatRecords(dom.encode())

        # Build our JSON
        newData = []
        for i in data:
            for j in i[2]:
                if i[1] == "MX": 
                    newData.append({
                        u'domain':unicode(i[0]), 
                        u'type':unicode(i[1]), 
                        u'priority':unicode(j.split()[0]),
                        u'host':unicode(j.split()[1])
                    })  

        return newData


    @pages.exposeAthena
    def changeDomainDetail(self, before, after):
        # Frist thing we need to do is figure out where this record will come from
        """{u'type': u'NS', u'domain': u'adstation.co.za', u'data': u'ns1.thusa.net'} 
        {u'type': u'NS', u'domain': u'adstation.co.za', u'data': u'ns2.thusa.net'}"""

        if not after:
            after = {}

        data = before.get(u'data', None)
        if data:
            afterData = after.get(u'data', u'')
        else:
            data = "%s %s" % (before[u'priority'], before[u'host'])
            if not after.get(u'data', None):
                afterData = u''
            else:
                # Try pull end data from the before segment if we an't do anything else
                afterData = "%s %s" % (after.get(u'priority', before[u'priority']), after.get(u'host', before[u'host']))

        data = data.encode()
       
        dn = before[u'domain']
        self.dns.updateDNSRecord(dn.encode(), before[u'type'].encode(), data.encode(), afterData.encode())
        return True

    @pages.exposeAthena
    def createNewZone(self, domain):
        records = [
            ('A', '74.53.87.74'),
            #('NS', 'ns11.thusa.net'), # Already added
            ('NS', 'ns10.thusa.net'),
            ('MX', '1 mx3.thusa.net')
        ]
        sOA = ('ns11.thusa.net', 'dns-admin.thusa.net', '2008042301', '3600', '600', '86400', '3600')

        print "Adding domain"
        print domain.encode()

        dz = domain.encode().strip('.')
        
        self.dns.addDNSRecord(dz, 'NS', 'ns11.thusa.net', soa=sOA)

        for type, data in records:
            self.dns.addDNSRecord(dz, type, data)

        self.dns.addDNSRecord('www.'+dz, 'CNAME', 'webhost.thusa.net')
        self.dns.addDNSRecord('mail.'+dz, 'CNAME', 'mailhost.thusa.net')

        def done(_):
            return True

        def addMembers(did):
            # Create group membership
            if 1 in self.avatarId.gids:
                addMems = []
            else:
                addMems = [self.enamel.storage.addDomainMembership(1, did[0])]

            for n in self.avatarId.gids:
                addMems.append(
                    self.enamel.storage.addDomainMembership(n, did[0])
                )
            
            # Send off a mail to invoicing
            addMems.append(
                system.system('echo "User %s created a new domain %s." | mail -s "New domain %s" support@thusa.co.za' % (
                    self.avatarId.username,
                    dz,
                    dz
                ))
            )
            
            return defer.DeferredList(addMems).addBoth(done)

        def getDid(res):
            # Get the ID for the domain we just added
            return self.enamel.storage.getDomainByName(domain.encode()).addBoth(addMembers)

        # ^^ Code logic goes backwards from here ^^
        return self.enamel.storage.addDomain(
            domain.encode(),
        ).addBoth(getDid)

    @pages.exposeAthena
    def storeNewRecord(self, record):
        """ {u'data': u'1 foo.com', u'domain': u'accountantsa.co.za', 
            u'type': u'MX', u'primary': u'accountantsa.co.za', u'ttl': u'300'}"""
        print "Store new!", record
        primary = record[u'primary'].encode()
        name = record[u'domain'].encode()
        type = record[u'type'].encode()
        data = record.get(u'data', False)
        if not data:
            data = "%s %s" % (record[u'priority'], record[u'host'])
        data = data.encode()

        dom = ""
        if primary in name:
            dom = name
        else:
            dom = '.'.join([name,primary])

        self.dns.addDNSRecord(dom, type, data)

        return True

class Page(PageBase.Athena):
    arbitraryArguments = True # Enable REST style arguments to the page

    elements = {
        'dnsFragment': (dnsFragment, 'dnsFragment.js', './js/dnsFragment.js')
    }

    def document(self):
        return pages.template('domain_main.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["DNS"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[tags.h1[title],tags.div[content]]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3["DNS Manager"],
            self.element_dnsFragment,
        ]

    def render_ncontent(self, ctx, data):
        dom = None
        if len(self.arguments) > 0:
            dom = self.arguments[0]

        dns = DNS.DNS('o=THUSA', 'thusa')
        
        if dom:
            data = dns.printableFlatRecords(dom)
            tab = [
                [
                    tags.tr[
                        tags.td[i[0]],
                        tags.td[i[1]],
                        tags.td[j]
                    ]
                    for j in i[2]
                ] 
                for i in data
            ]
        else:
            tab = [
                tags.tr[
                    tags.td[
                        tags.a(href="%s/" % i)[i]
                    ]
                ]
                for i in data
            ]

        return ctx.tag[
            tags.table[ tab ]
        ]


