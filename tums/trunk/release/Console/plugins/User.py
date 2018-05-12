import Console, Settings
import os, sys, copy, re, time
import Settings, LDAP, Tree, lang
from Core import WebUtils, Utils
from subprocess import call
#Cleanup

class Plugin(Console.AttrHooker):
    name = "user"    
    
    help = { 
            "__default__":"User Management",
            "service" : ""
           }   
    
    
    def udFromUname(self, uname):
        uname = uname.lower()
        if '@' in uname:
            domain = uname.split('@')[-1]
            user = uname.split('@')[0]
        else:
            user = uname
            domain = Settings.defaultDomain
        return user, domain


    def setUserAttr(self, uname, attrs):
        user, domain = self.udFromUname(uname)
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(domain), Settings.LDAPBase)
        userData =  LDAP.getUsers(l, dc, 'uid='+user)
        if not userData:
            print "No such user %s" % uname
            return 

        oldData = copy.deepcopy(userData[0])
        for k, v in attrs.items():
            userData[0][k] = v

        LDAP.modifyElement(l, 'uid='+user+','+dc, oldData, userData[0])
        l.unbind_s()
    
    def config_del(self, uname=None):
        """config user del: <username>"""
        if not uname:
            print "Please supply valid username"
            self.genAllDoc('config')
            return
        username, domain = self.udFromUname(uname)
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dn = "uid=%s,%s,%s,o=%s" % (username, Settings.LDAPPeople, LDAP.domainToDC(domain), Settings.LDAPBase)
        b = "%s,o=%s" % (LDAP.domainToDC(segments[0]), Settings.LDAPBase)

        # Remove user
        LDAP.deleteElement(l, dn)

        # Remove from group memberships
        for group in LDAP.getGroups(l, b):
            if LDAP.isMemberOf(l, b, segments[1], group[1]):
                LDAP.makeNotMemberOf(l, b, segments[1], group[1])

        l.unbind_s()

   
    def config_add(self, uname=None, password=None, *namesname):    
        """config user add: <username@domain> <password> <name and surname>
    Adds a basic user"""
        password = str(password)
        def genPasswordHash(password):
            return "{SHA}"+LDAP.hashPassword(password)

        # XXX XXX XXX
        # Tons of this is duplicate code from the web Users.py, if need be it should be broken out between LDAP opperations where possible
        # and have those moved into a generic class

        def addEntry(newRecord, user, domain, accountStatus=True, vpnEnabled=False):
            """Hi-jacked from Pages.Users.Add.py"""
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(domain), Settings.LDAPBase)

            # Send this to Thebe : TODO - Work out how to send update to Thebe from console
            #ser = WebUtils.serialiseUser(newRecord, domain) 
            #mail = "%s@%s" % (user, domain)
            #self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, ser))
            #print "User:%s:%s" % (mail, ser)
     
            try:
                LDAP.addElement(l, 'uid=%s,%s' % (user, dc), newRecord)
            except Exception, L:
                l.unbind_s()
                print "Error: Adding User:", user
                return
                
            # Send a mail to the luser to enable it...
            print "Successfully added", user
            if accountStatus:                
                print "Sending Welcome Message"
                myLang = lang.Text('en')                
                try:
                    retcode = call("echo '%s' | mail -s 'Welcome %s' %s" % 
                        (
                            myLang.userMailWelcomeMessage % newRecord['cn'][0],
                            newRecord['givenName'][0], 
                            newRecord['mail'][0]
                        ),
                    shell=True)

                    print "Sent"
                except OSError, e:
                    print "Execution failed:", e

            #if vpnEnabled:  
            #    vdata = {
            #        'name': "%s.%s" % (cid, domain),
            #        'mail': "%s@%s" % (user, domain),
            #        'ip':None,
            #        'mailKey': True
            #    }
            #    v = VPN.Page()
            #    v.text = self.text
            #    v.newCert(None, None, vdata)
            l.unbind_s()            
        

        if not (uname and password):
            print "Please provide at least a username and a password"            
            self.genAllDoc('config')
            return
        if '@' not in uname:
            user = uname
            domain = self.config.Domain
        else:
            user, domain = uname.split('@')
        
        emailAddress = user + '@' + domain
        givenName = ""
        sName = ""
        #Generate sane givenNamen and sName
        if len(namesname) > 0:
            givenName = str.join(' ',namesname[0:-1])
            sName = str.join('', namesname[-1:])

       
        #Generate LDAP Entry
        if Settings.sambaDN and domain==Settings.defaultDomain:            
            #Generate Samba Passwords
            LM = Utils.createLMHash(password) 
            NT = Utils.createNTHash(password) 
 
            # Acquire local SID
            l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
            dc = "%s,o=%s" % (LDAP.domainToDC(domain), Settings.LDAPBase)
            domainData =  LDAP.getDomInfo(l, dc, Settings.SMBDomain)
            
            SID = str(domainData['sambaSID'][0])


            # Acquire UID offset
            uidOffset =  int(domainData['uidNumber'][0])

            # Make RID
            SIDOffset = 2*uidOffset

            # Append user to Domain Users
            try:
                domainUsers = LDAP.getDomUsers(l, dc)
                newDomainUsers = copy.deepcopy(domainUsers)
                if not newDomainUsers.get('memberUid', None): # Very very new domain
                    newDomainUsers['memberUid'] = []
                newDomainUsers['memberUid'].append(user)
                LDAP.modifyElement(l, 'cn=Domain Users,ou=Groups,'+dc, domainUsers, newDomainUsers)
            except:
                pass # User already in group
            
            # Increment UID for domain
            newDom = copy.deepcopy(domainData)
            newDom['uidNumber'] = [str(uidOffset+1)]
            try: 
                LDAP.modifyElement(l, 'sambaDomainName=%s,%s,o=%s' % 
                    (Settings.SMBDomain, LDAP.domainToDC(self.domain), Settings.LDAPBase), domainData, newDom)
            except:
                pass # User has a uid or something
            
            timeNow = str(int(time.time()))
            # LDAP template for SAMBA
            shell = '/bin/false'
            #if enableFTP:
            #    shell = '/bin/bash'
            newRecord = {
                'sambaPrimaryGroupSID': [SID+"-"+str(1000+SIDOffset+1)],
                'sambaSID':             [SID+"-"+str(1000+SIDOffset)],
                'gidNumber':            ['513'],
                'uidNumber':            [str(uidOffset)],
                'sambaPasswordHistory': ['0000000000000000000000000000000000000000000000000000000000000000'],
                'sambaPwdMustChange':   ['2147483647'],
                'sambaPwdCanChange':    [timeNow],
                'sambaNTPassword':      [NT],
                'sambaLMPassword':      [LM],
                'gecos':                ['System User'],
                'sn':                   [ sName ],
                'givenName':            [ givenName],
                'cn':                   ["%s %s" % (givenName, sName)],
                'o':                    [Settings.LDAPOrganisation],
                'objectClass':          ['top', 'inetOrgPerson', 'posixAccount', 'shadowAccount',
                                         'SambaSamAccount', 'thusaUser'],
                'loginShell':           [shell],
                'sambaPwdLastSet':      [timeNow],
                'sambaAcctFlags':       ['[U          ]'],
                'mailMessageStore':     ['/var/spool/mail/' + emailAddress],
                'mail':                 [emailAddress],
                'homeDirectory':        ['/home/%s' % user],
                'uid':                  [user],
                'employeeType':         []
            }
            l.unbind_s()
        else:
            # LDAP Template for without samba
            newRecord = {
                'sn':                   [sName],
                'givenName':            [givenName],
                'cn':                   ["%s %s" % (givenName, sName)],
                'o':                    [Settings.LDAPOrganisation],
                'objectClass':          ['top', 'inetOrgPerson', 'thusaUser'],
                'mailMessageStore':     ['/var/spool/mail/' + emailAddress],
                'mail':                 [emailAddress],
                'uid':                  [user],
                'employeeType':         []
            }
        
        newRecord['employeeType'].append('squid')
        newRecord['userPassword'] = [ genPasswordHash(password) ]        
        #newRecord['employeeType'].append('tumsAdmin') If it should be a admin
        #newRecord['employeeType'].append('tumsReports')
        
        addEntry(newRecord, user, domain)       
        
        if Settings.sambaDN and domain==Settings.defaultDomain:
            try:
                retcode = call('/etc/init.d/nscd restart', shell=True)
                retcode = call('mkdir /home/%(user)s; chown %(user)s:Domain\ Users /home/%(user)s' % {'user':user}, shell=True)
            except OSError, e:
                print "Execution failed:", e


    def config_set_name(self, username, *a):
        """config user set name: <username> <name and surname>"""
        name = ' '.join(a)
        rec = {
            'cn' : name,
            'givenName' : a[0],
            'sn' : a[-1]
        }
        self.setUserAttr(username, rec)

    def config_set_password(self, username, password):
        """config user set password: <username> <new password>"""
        rec = {'userPassword': ["{SHA}" + LDAP.hashPassword(password)]}

        user, domain = self.udFromUname(username)

        if Settings.sambaDN and domain==Settings.defaultDomain:
            rec['sambaNTPassword'] = [Utils.createNTHash(password)]
            rec['sambaLMPassword'] = [Utils.createLMHash(password)]

        self.setUserAttr(username, rec)    
    
    def show_user(self, *a):
        """show user: <username>
    Shows the details for a user"""
        if not a:
            #Generate documents for Show user
            self.genAllDoc('show')            
            return 
        uname = a[0].lower()
        if '@' in uname:
            domain = uname.split('@')[-1]
            user = uname.split('@')[0]
        else:
            user = uname
            domain = Settings.defaultDomain
        
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(domain), Settings.LDAPBase)
        userData =  LDAP.getUsers(l, dc, 'uid='+user)

        if not userData:
            print "No such username\n"
            return 

        descr = [
            ('cn',            'Full Name      '),
            ('accountStatus', 'Email Enabled  '),
            ('mail',          'Email Address  '),
            ('employeeType',  'Priviledges    '),
        ]

        for i in descr:
            if userData[0].get(i[0], False):
                print i[1], ':', userData[0][i[0]][0]
        
    def show_list(self):
        """show user list
    Show a list of users"""
        l = Tree.retrieveTree(Settings.LDAPServer, Settings.LDAPManager, Settings.LDAPPass, 'o='+Settings.LDAPBase)
        tree = {}
        for i in l:
            domain = ""
            uid = ""
            if 'uid' in i:
                parts = i.split(',')
                for p in parts:
                    if 'dc' in p:
                        dompart = p.split('=')[-1]
                        domain = dompart+'.'+domain
                    if 'uid' in p:
                        uid = p.split('=')[-1]
                domain = domain.strip('.')
                
                if uid[-1] == "$":
                    continue
                if tree.get(domain, False):
                    tree[domain].append("%s@%s" % (uid, domain))
                else:
                    tree[domain] = ["%s@%s" % (uid, domain)]

        maxlen = 0
        for i in tree:
            if len(i) > maxlen:
                maxlen = len(i)

        for k,v in tree.items():
            print k, " " * (maxlen-len(k)), v[0]
            if len(v)>1:
                for i in v[1:]:
                    print " " * (maxlen+1), i
            print ""


