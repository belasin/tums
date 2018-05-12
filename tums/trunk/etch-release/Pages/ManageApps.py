from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, filepath
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP, zipfile
from Core import PageHelpers, AuthApacheProxy, WebUtils
from Pages import Tools
import formal

class Page(Tools.Page):
    def form_addApp(self, data):
        form = formal.Form()
        
        form.addField('file', formal.File())
        
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        name, fi = data['file']

        if name[-4:] == ".wap":
            fi = zipfile.ZipFile(fi, 'r')
            
            basedir = "/usr/local/tcs/tums/Waps/"
            files = fi.namelist()

            # Confirm some integrity
            wapBase = ""
            baseFiles = []
            for f in files:
                n = f.split('/')
                baseFiles.append('/'.join(n[1:]))

                if not wapBase:
                    wapBase = n[0]
                    continue
                if n[0] != wapBase:
                    return url.root.child('ManageApps').child('Failed')

            if not "__init__.py" in baseFiles:
                return url.root.child('ManageApps').child('Failed')

            if not "main.py" in baseFiles:
                return url.root.child('ManageApps').child('Failed')

            for path in files:
                # Don't extract pyc files, because they may cause breakage
                if path[-4:] == ".pyc":
                    continue

                # If this is a path listing, just make it and do nothing else
                if '/' == path[-1]:
                    if not os.path.exists(os.path.join(basedir, path)):
                        os.makedirs(os.path.join(basedir, path))
                    continue

                # create our path for this file
                n = path.split('/')
                if not os.path.exists(os.path.join(basedir, '/'.join(n[:-1]))):
                    print "Making directory", '/'.join(n[:-1])
                    os.makedirs(os.path.join(basedir, '/'.join(n[:-1])))

                # Write the file
                print "Writing file", path
                n = open(os.path.join(basedir, path), 'wb')
                n.write(fi.read(path))
                n.close()

            # Reload our hooky
            self.db[5].pluginBootstrap()
            plugBase = os.path.join(Settings.BaseDir, 'Waps/%s/configurator' % wapBase)
            if os.path.exists(plugBase):
                for plug in os.listdir(plugBase):
                    try:
                        os.symlink(
                            os.path.join(plugBase, plug), 
                            os.path.join(Settings.BaseDir, 'plugins/Z%s-%s' % (wapBase, plug))
                        )
                    except Exception, e:
                        print "Error installing configurator plugin", plug 
                        print e 
        return url.root.child('ManageApps')

    def render_content(self, ctx, data):
        plugins = []
        for k,v in self.db[5].plugins.items():
            modPtr, name, version = v
            plugins.append([
                name, version, "Waps/"+k, 
                tags.a(title= "Uninstall %s" % name, href="Delete/%s/" % k)[tags.img(src="/images/ex.png")] 
            ])

        return ctx.tag[
                tags.h3[tags.img(src="/images/netdrive.png"), " Applications"],
                PageHelpers.dataTable(['Module Name', 'Version', 'Install Location', ''], plugins),
                tags.h3["Install Application"], 
                tags.directive('form addApp')
            ]

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            for root, dirs, files in os.walk(os.path.join(Settings.BaseDir, 'Waps/%s' % segs[1])):
                for fi in files:
                    path = os.path.join(root, fi)
                    os.remove(path)
            filepath.FilePath(os.path.join(Settings.BaseDir, 'Waps/%s' % segs[1])).remove()
            
            # We could actualy just create something to remove this object and delete the references instead of reloading the world
            self.db[5].unloadPlugin(segs[1])
            
            for plugin in os.listdir(os.path.join(Settings.BaseDir, 'plugins')):
                if plugin.startswith('Z%s-' % segs[1]):
                    print "Removing ", plugin
                    os.remove(os.path.join(Settings.BaseDir, 'plugins/%s' % plugin))
            return url.root.child('ManageApps'), ()

        return rend.Page.locateChild(self, ctx, segs)
            
