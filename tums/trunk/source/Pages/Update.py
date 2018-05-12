from nevow import rend, loaders, tags, athena
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from twisted.internet.protocol import ProcessProtocol
from twisted.internet import reactor
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
import formal, socket, struct

# aptitude update
class AptUpdater(ProcessProtocol):
    def __init__(self, fragment):
        self.fragment = fragment

    def outReceived(self, data):
        cs = data.split()
        for i in cs:
            if "%" in i:
                # Clean up the percentage
                percent = int(i.split('%')[0].strip().replace('[', ''))
                self.fragment.progressUpdate(percent)
                # Only take the first on a line 
                break
        #self.fragment.progressUpdate(self.file, self.linesTotal)

    def processEnded(self, status):
        print "Completed with status %s" % (status.value.exitCode)
        self.fragment.updateComplete()

def aptitudeUpdate(fragment):
    rproc = AptUpdater(fragment)
    reactor.spawnProcess(rproc, "/usr/bin/aptitude", args = ("aptitude", "update"), usePTY=1)

# aptitude -d -y safe-upgrade (Downloads packages)
class AptDownloadUpgrade(AptUpdater):
    def processEnded(self, status):
        self.fragment.doUpgrade()

def aptitudeUgradeDownload(fragment):
    rproc = AptDownloadUpgrade(fragment)
    reactor.spawnProcess(rproc, "/usr/bin/aptitude", args = ("aptitude", "-d", "-y", "safe-upgrade"), usePTY=1)

# aptitude -y safe-upgrade (Perform package installation)
class AptUpgrade(AptUpdater):
    def processEnded(self, status):
        self.fragment.upgradeComplete()

def aptitudeUpgrade(fragment):
    rproc = AptUpgrade(fragment)
    reactor.spawnProcess(rproc, "/usr/bin/apt-get", 
        args = ("apt-get", "-q", "--force-yes", "-y", '-o Dpkg::Options::="--force-confdef"', "upgrade"), 
        env={
            'DEBIAN_FRONTEND':"noninteractive", 
            'PATH':"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        }, 
        usePTY=1
    )

# COMET fragment for updater
class liveGraphFragment(athena.LiveFragment):
    jsClass = u'updates.PS'

    docFactory = loaders.xmlfile('update-fragment.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, *a, **kw):
        super(liveGraphFragment, self).__init__(*a, **kw)
        self.sysconf = confparse.Config()
        self.progress = 0

    def progressUpdate(self, percentage):
        if percentage != self.progress:
            self.callRemote('updateProgress', percentage)
        self.progress = percentage

    def updateComplete(self):
        # This means we have done 'aptitude update'. We now 
        # need to get the update size. 

        def gotUpdates(ans):
            an = ans.strip('\n').split()
            uSize = an[3]
            self.callRemote('updateTicker', u'')
            self.callRemote('updateProgress', 0)

            if uSize == "0B":
                self.callRemote('noUpdates')
            else:
                self.callRemote('newUpdates', unicode(uSize))

        WebUtils.system('aptitude -y -s safe-upgrade | grep "^Need to get"').addCallback(gotUpdates)
    athena.expose(updateComplete)

    def upgradeComplete(self):
        self.callRemote('updateTicker', u'System updated')
        self.callRemote('updateProgress', 100)
    athena.expose(upgradeComplete)

    def doUpgrade(self):
        aptitudeUpgrade(self)
        self.callRemote('updateTicker', u'Installing packages')
    athena.expose(doUpgrade)

    def doDownload(self):
        aptitudeUgradeDownload(self)
        self.callRemote('updateTicker', u'Downloading packages')
    athena.expose(doDownload)

    def doUpdate(self):
        aptitudeUpdate(self)
        self.callRemote('updateTicker', u'Updating package lists')
        self.callRemote('updateProgress', 0)
        return True
    athena.expose(doUpdate)

class Page(PageHelpers.DefaultAthena):
    moduleName = 'updates'
    moduleScript = 'update-page.js' 
    docFactory = loaders.xmlfile('update-page.xml', templateDir = Settings.BaseDir + '/templates')

    addSlash = True

    def form_updateSettings(self, data):
        form = formal.Form()
        form.addField('autoUpdate', formal.Boolean(), label = "Auto Update", 
            description = "Enable automatic updates of Vulani")

        form.addField('debupdate', formal.String(), label = "Update server", 
            description = ["The Debian mirror to use for platform updates. To find a closer mirror see ", 
                tags.a(href="http://www.debian.org/mirror/list")["http://www.debian.org/mirror/list"]
            ])

        form.addField('thusa', formal.Boolean(), label = "Thusa Managed", 
            description = "Enable remote management and support by Thusa")

        form.addAction(self.updateSettings)

        G = self.sysconf.General

        if G.get('aptprimary', ""):
            form.data['debupdate'] =  G['aptprimary']
        else:
            form.data['debupdate'] =  'http://debian.mirror.ac.za/debian/'

        if os.path.exists('/usr/local/tcs/tums/packages/autoup'):
            form.data['autoUpdate'] = True

        if os.path.exists('/usr/local/tcs/tums/packages/nomng'):
            form.data['thusa'] = False
            form.data['autoUpdate'] = True
        else:
            form.data['thusa'] = True
            
        return form

    def updateSettings(self, ctx, f, data):
        if data['debupdate']:
            mirror = data['debupdate'].encode('ascii').strip()
        else:
            mirror = ""
        autoUpdate = data['autoUpdate']

        # Store update settings
        G = self.sysconf.General
        if mirror:
            G['aptprimary'] = mirror
        else:
            G['aptprimary'] = ""
        self.sysconf.General = G
            
        
        if autoUpdate:
            ni = open('/usr/local/tcs/tums/packages/autoup', 'wt')
            ni.write('\x01\x01\n')
            ni.close()
        else:
            if os.path.exists('/usr/local/tcs/tums/packages/autoup'):
                os.remove('/usr/local/tcs/tums/packages/autoup')

        # Save management settings
        if data['thusa']:
            if os.path.exists('/usr/local/tcs/tums/packages/nomng'):
                os.remove('/usr/local/tcs/tums/packages/nomng')

                fw = self.sysconf.Shorewall
                for z in fw['zones'].keys():
                    if 'loc' in z:
                        continue

                    fw['rules'].insert(0, [1, 'ACCEPT %s:196.211.242.160/29   all' % z])
                    fw['rules'].insert(0, [1, 'ACCEPT %s:196.212.55.128/29    all' % z])
                    fw['rules'].insert(0, [1, 'ACCEPT %s:74.53.87.72/29       all' % z])
                    fw['rules'].insert(0, [1, 'ACCEPT %s:97.107.137.116       all' % z])
                self.sysconf.Shorewall = fw

        else:
            if not os.path.exists('/usr/local/tcs/tums/packages/nomng'):
                ni = open('/usr/local/tcs/tums/packages/nomng', 'wt')
                ni.write('\x01\x00\n')
                ni.close()

                # Remove firewall rules
                fw = self.sysconf.Shorewall
                newrules = []
                for i in fw['rules']:
                    if ":196.211.242.160/29" in i[1]:
                        continue
                    if ":74.53.87.72/29" in i[1]:
                        continue
                    if ":97.107.137.116" in i[1]:
                        continue
                    if ":196.212.55.128/29" in i[1]:
                        continue
                    newrules.append(i)
                fw['rules'] = newrules

                self.sysconf.Shorewall = fw

        # XXX Save base settings here. 

        return url.root.child('SystemUpdate')

    def render_thisFragment(self, ctx, data):
        """ Renders liveGraphFragment instance """
        f = liveGraphFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src='/images/tools-lg.png'), " Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Updates"],
            PageHelpers.TabSwitcher((
                ('Update', 'panelUpdate'),
                ('Settings', 'panelSettings'),
            )),
            tags.div(id="panelUpdate", _class="tabPane")[
                tags.div[
                    tags.invisible(render=tags.directive('thisFragment'))
                ]
            ],
            tags.div(id="panelSettings", _class="tabPane")[
                tags.directive('form updateSettings'),
            ],
            PageHelpers.LoadTabSwitcher()
        ]

