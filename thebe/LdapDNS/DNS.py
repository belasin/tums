#!/usr/bin/python
if __name__== "__main__":
    import LDAP
else:
    from LdapDNS import LDAP

import copy

class DNS:
    def __init__(self, o, password):
        self.o = o
        self.host = '127.0.0.1'
        self.password = password
        self.attrToDescr = {
            'nSRecord': "NS",
            'aRecord':  "A",
            'aAAARecord': "AAAA",
            'mXRecord': "MX",
            'cNAMERecord': "CNAME",
            'dNSTTL': 'TTL',
        }
        # Create a reverse of that too..
        self.descrToAttr = dict([(v,k) for k,v in self.attrToDescr.items()])

    def getDomains(self):
        l = LDAP.ldapQueryMaker(self.host, self.o, 'cn=Manager', self.password)
        res =  l.cleanSearch('ou=DNS', 'associatedDomain', '(sOARecord=*)')
        res.sort()
        return res

    def domainToDc(self, dom):
        l = dom.split('.')
        domdn = 'dc=%s' % ',dc='.join(l)
        return "%s,ou=DNS" % (domdn)#, self.o)


    def getRecords(self, dom):
        dn = self.domainToDc(dom)

        attributes = ['sOARecord', 'nSRecord', 'aRecord', 'mXRecord', 'cNAMERecord', 'aAAARecord', 'dNSTTL']

        l = LDAP.ldapQueryMaker(self.host, self.o, 'cn=Manager', self.password)
        result = l.executeSearch(dn, attributes + ['associatedDomain'], '(objectClass=domainRelatedObject)')
        records = {}
        # Turn the result of all associated records into a more useful structure 
        # of {'record type' : ('subdomain', [list of datas, ...]), ...}

        for i in result:
            dta = i[1]
            associated = dta['associatedDomain'][0]
            for k,v in i[1].items():
                if k in attributes:
                    if records.get(k, False):
                        records[k].append((associated, v))
                    else:
                        records[k] = [(associated, v)]
        return records

    def printableFlatRecords(self, dom):
        recs = self.getRecords(dom)
        
        recSubList = []
        for k, v in recs.items():
            descr = self.attrToDescr.get(k, False)
            if descr:
                for i in v:
                    name, data = i
                    recSubList.append((name, descr, data))
        recSubList.sort()
        return recSubList

    def getSubs(self, dom):
        recs = self.printableFlatRecords(dom)
        dn = []
        for name,type,data in recs:
            if name not in dn:
                if name != dom:
                    dn.append(name)

        return dn

    def getDNSRecord(self, dom):
        dn = self.domainToDc(dom)
        l = LDAP.ldapQueryMaker(self.host, self.o, 'cn=Manager', self.password)
        try:
            result = l.executeSearch(dn, ['*'], '(associatedDomain=%s)' % dom)
        except Exception, e:
            # No such record
            if e[0]['desc'] == "No such object":
                return None
            else:
                print e
                return None
        try:
            return result[0]
        except Exception, e:
            print "Hmm Empty List"
            return None

    def updateDNSRecord(self, dom, type, prev, data):
        """ Data comes as a single data var of 'type' for dom. 
            prev gives us an idea of what it replaces """
        # Convert our type name into a useful attribute
        attribute = self.descrToAttr[type]
        
        # Get the old data to compare
        dn, oldData = self.getDNSRecord(dom) #[type]

        # We must now delete prev from oldData and add data.
        newData = []
        for i in oldData.get(attribute, []):
            if i != prev:
                newData.append(i)
        if data:
            newData.append(data)

        newRec = copy.deepcopy(oldData)
        newRec[attribute] = newData
        # Now we update our record 
        l = LDAP.ldapQueryMaker(self.host, self.o, 'cn=Manager', self.password)
        l.modifyElement(dn, oldData, newRec)

    def createPath(self, dnList):
        """ Expects a dn list to follow and create. """
        dnPath = "ou=DNS"
        l = LDAP.ldapQueryMaker(self.host, self.o, 'cn=Manager', self.password)
        for dn in reversed(dnList):
            dnPath = ','.join([dn, dnPath]) # Construct a trail
            dom = dnPath.split(',ou')[0].replace('dc=','').replace(',','.')
            recBase = {
                'objectClass': ['dNSDomain2', 'domainRelatedObject'],
                'associatedDomain': [dom],
                'dc': [dn.replace('dc=', '')]
            }
            # Create a record in this dn path
            try:
                result = l.executeSearch(dnPath, ['dc'], '(associatedDomain=%s)' % dom)
            except:
                l.addElement(dnPath, recBase)

    def addDNSRecord(self, dom, type, data, soa=None):
        dn = self.domainToDc(dom)
        attribute = self.descrToAttr[type]

        if self.getDNSRecord(dom):
            # Domain already exists... We are adding a new attribute 
            # so we recycle our update mechanism 
            self.updateDNSRecord(dom, type, '', data)
        else:
            # No domain, we need a whole new record

            recBase = {
                'objectClass': ['dNSDomain2', 'domainRelatedObject', 'top'],
                'associatedDomain': [dom],
                'dc': [dom.split('.')[0]]
            }

            recBase[attribute] = [data]
            
            # Before we do that, we need to trace the dn path, and try create each node
            smallDn = dn.split(',ou')[0].split(',')[1:]
            self.createPath(smallDn)

            if soa:
                # Define the SOA record - should be sent as a tuple like:
                #   ('ns1.thusa.net', 'dns-admin.thusa.net', '2007083001', '3600', '600', '86400', '3600')
                recBase['sOARecord'] = [' '.join(soa)]
            
            # Add the record.
            l = LDAP.ldapQueryMaker(self.host, self.o, 'cn=Manager', self.password)
            l.addElement(dn, recBase)

        return True

    def deleteDomain(self, dom):
        dn = self.domainToDc(dom)
        l = LDAP.ldapQueryMaker(self.host, self.o, 'cn=Manager', self.password)
        l.deleteElement(dn)

if __name__== "__main__":
    d = DNS('o=THUSA', 'thusa')

    # Test domain retreival
    print d.getSubs('thusa.net')


