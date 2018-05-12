from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import time, formal, LDAP, os
import Tree, Settings

from Core import PageHelpers, Utils, WebUtils
from Pages import Tools

from twisted.python import log

from twisted.internet.defer import deferredGenerator, waitForDeferred as wait


class Page(Tools.Page):

    def form_addComputer(self, data):
        form = formal.Form()

        form.addField('name', formal.String(required=True), label = self.text.compName)

        form.addAction(self.submitCompForm)

        return form

    def submitCompForm(self, ctx, form, data):
        Utils.log.msg('%s added computer %s' % (self.avatarId.username, repr(data)))
        
        name = data['name'].encode()
        
        def returnPage(result):
            Utils.log.msg(result)
            return url.root.child('Domain')

        return WebUtils.system('smbldap-useradd -w %s$; smbpasswd -a -m %s$' % (name, name)).addBoth(returnPage)

    def reloadSamba(self):
        WebUtils.system(Settings.BaseDir+'/configurator --samba')
        WebUtils.system("/etc/init.d/samba restart");

    def form_configSamba(self, data):
        form = formal.Form()

        form.addField('pdc', formal.Boolean(), label = "Domain controller")
        form.addField('profileroam', formal.Boolean(), label = "Roaming profiles")
        form.addField('logscript', formal.Boolean(), label = "Login script", 
            description = "Enable the kixstart login script for drive mapping")

        form.addAction(self.submitConfForm)

        smbcfg = self.sysconf.SambaConfig

        if smbcfg.get('logon script'):
            form.data['logscript'] = True

        if smbcfg.get('logon path', None):
            if smbcfg['logon path']:
                form.data['profileroam'] = True
        if smbcfg.get('domain logons', None):
            if smbcfg['domain logons'] == 'yes':
                form.data['pdc'] = True
        return form

    def submitConfForm(self, ctx, form, data):
        smbcfg = self.sysconf.SambaConfig

        if data['logscript']:
            smbcfg['logon script']= 'STARTUP.BAT'
        else:
            smbcfg[';logon script']= 'STARTUP.BAT'
            try:
                del smbcfg['logon script']
            except Exception, e:
                pass

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
        
        return url.root.child('Domain')

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

        form.addAction(self.submitDriveForm)
        return form

    def submitDriveForm(self, ctx, form, data):
        logon = open('/var/lib/samba/netlogon/drives.kix', 'at')

        if data['loginGroup']:
            logon.write(self.kixMap(data['loginGroup'], data['driveletter'], data['sharepath']))

        def returnPage(_):
            return url.root.child('Domain')
        return WebUtils.system('chmod a+r /var/lib/samba/netlogon/drives.kix; /etc/init.d/samba reload').addBoth(returnPage)

    def render_computers(self, ctx, data):
        def rendt(proc):
            comps = []
            for i in proc.split('\n'):
                if i.strip('\n'):
                    name = i.split(':')[0].strip('$')
                    comps.append([name, tags.a(href=url.root.child("Domain").child("DeleteComp").child(name), 
                    onclick="return confirm('%s');" % self.text.compConfirm)[tags.img(src="/images/ex.png")]])
            
            Utils.log.msg('%s opened Tools/Computers' % (self.avatarId.username))

            return ctx.tag[
                tags.h3[tags.img(src='/images/srvman.png'), self.text.compHeading], 
                tags.h3[self.text.compHeadingList],
                PageHelpers.dataTable([self.text.compName, ''], comps, sortable=True),
                tags.h3[self.text.compHeadingAdd],
                tags.directive('form addComputer'),
            ]
        return WebUtils.system('getent passwd | grep Computer').addBoth(rendt)


    def render_drives(self, ctx, data):
        drives = self.getMaps()
        return ctx.tag[
                tags.h3[tags.img(src="/images/netdrive.png"), " Network Drives"],
                PageHelpers.dataTable(["Login Group", "Drive Letter", "Share Path", ""],
                    [   
                        [
                            i[0],
                            i[1],
                            i[2],
                            tags.a(
                                    href="DeleteMap/%s/" % i[1],
                                    onclick="return confirm('Are you sure you want to delete this drive?');"
                                )[tags.img(src="/images/ex.png")]
                        ]
                    for i in drives], sortable=True
                ),
                tags.h3["Add Network Drive"], 
                tags.directive('form addDrive')
        ]

    def render_content(self, ctx, data):

        return ctx.tag[
            PageHelpers.TabSwitcher((
                ('Configuration', 'panelConf'), 
                ('Mapping', 'panelMap'), 
                ('Computers', 'panelComp')
            )),
            tags.div(id="panelConf", _class="tabPane")[
                tags.h3[tags.img(src="/images/sharefold.png"), " Domain configuration"],
                tags.directive('form configSamba')
            ],
            tags.div(id="panelMap", _class="tabPane")[
                tags.invisible(render=tags.directive('drives'))
            ],
            tags.div(id="panelComp", _class="tabPane")[
                tags.invisible(render=tags.directive('computers'))
            ],
            PageHelpers.LoadTabSwitcher()
        ]


    def locateChild(self, ctx, segs):
        if segs[0]=="DeleteMap":
            maps = self.getMaps()
            logon = open('/var/lib/samba/netlogon/drives.kix', 'wt')
            keep = []
            for i in maps:
                if i[1] != segs[1]:
                    logon.write(self.kixMap(*i))
            
            return WebUtils.system('chmod a+r /var/lib/samba/netlogon/drives.kix; /etc/init.d/samba reload').addBoth(lambda _: url.root.child('Domain')), ()

        if segs[0]=="DeleteComp":
            # Deletes Computer. 
            Utils.log.msg('%s deleted computer %s' % (self.avatarId.username, segs[1]))
            name = segs[1]
            def returnPage(_):
                return url.root.child('Domain'), ()
            return WebUtils.system('smbldap-userdel %s$' % (name, )).addBoth(returnPage)
            
        return rend.Page.locateChild(self, ctx, segs)


