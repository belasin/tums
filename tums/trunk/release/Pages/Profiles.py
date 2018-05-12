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

class Page(Tools.Page):
    addSlash = True

    def form_rename(self, data):
        form = formal.Form()
        form.addField('source', formal.String(), label = self.text.profileSource)
        form.addField('dest', formal.String(), label = self.text.profileDest)
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        source = data['source'].lower().replace(' ', '_') + '.py'
        dest = data['dest'].lower().replace(' ', '_') + '.py'

        def ret(_):
                if Utils.runningProfile()[1] == source:
                    run = open(Settings.BaseDir + '/runningProfile', 'wt')
                    run.write(dest)
                    run.close()
                if Utils.currentProfile()[1] == source:
                    cur = open(Settings.BaseDir + '/currentProfile', 'wt')
                    cur.write(dest)
                    cur.close()

                return url.root.child('Profiles')
                
        return WebUtils.system("mv /usr/local/tcs/tums/profiles/%s /usr/local/tcs/tums/profiles/%s" % (source, dest)).addCallback(ret)

    def render_content(self, ctx, data):
        dir = os.listdir('/usr/local/tcs/tums/profiles/')
        dir.sort()
        tab = []
        for l in dir:
            if l[-3:] == ".py":
                name = l[:-3].replace('_', ' ').capitalize()
                tab.append(
                    (name,[
                        tags.a(href="copy/%s" % l)["Copy"],
                        " ",
                        tags.a(href="#", onclick="showElement('ren'); getElement('rename-source').value = '%s'; return false;" % name)["Rename"],
                        " ",
                        tags.a(
                            href="delete/%s"%(l),
                            onclick="return confirm('Are you sure you want to delete this profile?');",
                            title="Delete this profile"
                        )[tags.img(src="/images/ex.png")]
                    ])
                )

        return ctx.tag[
            tags.h3[tags.img(src="/images/cluster.png"), " Configuration Profiles"],
            PageHelpers.dataTable(['Profile Name',""], tab),
            tags.br, 
            tags.div(id="ren", style="display:none;")[
                tags.directive('form rename')
            ]
        ]

    def locateChild(self, ctx, segs):
        def ret(_):
            return url.root.child('Profiles'), ()

        if segs[0] == "copy":
            dest = "copy_of_" + segs[1]
            return WebUtils.system("cp /usr/local/tcs/tums/profiles/%s /usr/local/tcs/tums/profiles/%s; chmod a+r /usr/local/tcs/tums/profiles/%s" % (segs[1], dest, dest)).addCallback(ret)

        if segs[0] == "delete":
            return WebUtils.system("rm /usr/local/tcs/tums/profiles/%s" % (segs[1])).addCallback(ret)

        if segs[0] == "switch":
            newProfile = segs[1]
            l = open(Settings.BaseDir + '/runningProfile', 'wt')
            l.write(newProfile)
            l.close()
            WebUtils.system("cp %s/%s %s/config.py; /usr/local/tcs/tums/configurator -r" % (Settings.BaseDir, newProfile, Settings.BaseDir)) 
            return url.root.child('Status'), ()
        return rend.Page.locateChild(self, ctx, segs)

