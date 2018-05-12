from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, WebUtils
from Pages import Tools
import formal

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def getMaps(self):
        # Read out the drive shares script and create a list of mappings
        try:
            logon = open('/var/lib/samba/netlogon/drives.kix', 'rt')
        except:
            logon = [""]

        groups = {}
        maps = []
        group = ""
        for l in logon:
            line = l.strip('/n').strip()
            if "IF INGROUP" in line:
                group = line.split('\\')[-1].split('"')[0] # Group between \ and "
            elif "ENDIF" in line:
                group = None
            elif "USE" in line:
                sp = line.split()
                maps.append([group, sp[1].strip(':'), sp[2].strip('"')])
        return maps

    def kixMap(self, group, drive, share):
        """ Constructs a ScriptLogic block for the drive mapping, returns a string """
        map = "IF INGROUP(\"@DOMAIN\\%s\")\n" % (group,)
        map += "    USE %s: \"%s\"\n" % (drive, share)
        map += "ENDIF\n\n"
        return map

    def form_addDrive(self, data):
        form = formal.Form()

        # Make a list of drive letters F - Z
        AvailLetters = [chr(i) for i in range(70,91)]
        # Remove letters that are used already
        for letter in [i[1] for i in self.getMaps()]:
            del AvailLetters[AvailLetters.index(letter)]

        # Get groups on system
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(Settings.defaultDomain), Settings.LDAPBase)

        groups = LDAP.getGroups(l, dc)
        groups.sort()

        form.addField('sharepath', formal.String(required=True), label = "Share Path", 
            description = "Network path to the share, for example \\\\tcs\\Public\\")
            
        form.addField('loginGroup', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i[1],i[1]) for i in groups]), label = "Login Group", 
            description = "Requred login group for this network drive")

        form.addField('driveletter', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in AvailLetters]), label = "Drive Letter")

        form.data['driveletter'] = AvailLetters[0]
        form.data['loginGroup']  = "Domain Users"

        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        logon = open('/var/lib/samba/netlogon/drives.kix', 'at')

        domain = "TESTDOM" # Get this from somewhere :/
        
        if data['loginGroup']:
            logon.write(self.kixMap(data['loginGroup'], data['driveletter'], data['sharepath']))

        WebUtils.system('/etc/init.d/samba reload')
        
        return url.root.child('Netdrive')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        drives = self.getMaps()
        return ctx.tag[
                tags.h2[tags.img(src="/images/netdrive.png"), " Network Drives"],
                tags.table(cellspacing=0, width="95%", _class='listing')[
                    tags.thead(background="/images/gradMB.png")[
                        tags.tr[
                            tags.th["Login Group"],
                            tags.th["Drive Letter"],
                            tags.th["Share Path"],
                            tags.th[""],
                        ]
                    ],
                    tags.tbody[
                    [   
                        tags.tr[
                            tags.td[i[0]],
                            tags.td[i[1]],
                            tags.td[i[2]],
                            tags.td[
                                tags.a(
                                    href="Delete/%s/" % i[1],
                                    onclick="return confirm('Are you sure you want to delete this drive?');"
                                )[tags.img(src="/images/ex.png")]
                            ]
                        ]
                    for i in drives],
                    ]
                ], tags.br,
                tags.h3["Add Network Drive"], 
                tags.directive('form addDrive')
            ]

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            maps = self.getMaps()
            logon = open('/var/lib/samba/netlogon/drives.kix', 'wt')
            keep = []
            for i in maps:
                if i[1] != segs[1]:
                    logon.write(self.kixMap(*i))
            WebUtils.system('/etc/init.d/samba reload')
            return url.root.child('Netdrive'), ()
        return rend.Page.locateChild(self, ctx, segs)
            
