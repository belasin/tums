from nevow import rend, loaders, tags, athena
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import reactor, utils
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP, time, stat
from Core import PageHelpers, AuthApacheProxy, Utils, confparse, WebUtils
from Pages import Tools
import formal, copy

CLIP_COPY = 1
CLIP_CUT = 2

class browserFragment(athena.LiveFragment):
    jsClass = u'fileBrowser.PS'
    docFactory = loaders.xmlfile('fileBrowser.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, *a, **kw):
        super(browserFragment, self).__init__(*a, **kw)
        self.nodes = []
        self.startPath = '/home'
        self.lastFolder = ""
        self.lastFile = ""
        self.clipboard = ""
        self.clipAction = None
        reactor.callLater(2, self.callRemote, 'renderFolders')
        reactor.callLater(2, self.callRemote, 'addEvents')

    def getUSB(self):
        try:
            storageNodes = os.listdir('/proc/scsi/usb-storage/')
        except:
            storageNodes = []
        AvailLetters = []
        for s in storageNodes:
            l = open('/proc/scsi/usb-storage/%s' % s)
            for i in l:
                ln = i.strip()
                if "Vendor" in ln:
                    vendor = ln.split(':')[-1].strip()
                if "Serial Number" in ln:
                    sn = ln.split(':')[-1].strip().split()[0]
            AvailLetters.append((sn, vendor))
        return AvailLetters

    def getLocations(self):
        locs = []
        locs.append(("home", "Home Directories"))
        locs.append(("samba", "Fileserver Data"))
        locs.extend(self.getUSB())
        return locs

    def render_locations(self, ctx, data):
        return ctx.tag[
            tags.select(id="location", name="interface")[
                [tags.option(value=i)[j] for i,j in self.getLocations()]
            ]
        ]

    def changeLocation(self, loc):
        def returnt(_):
            self.callRemote('renderFolders')
            return True

        if "home" == loc:
            self.startPath = '/home'
            self.callRemote('renderFolders')
        if "samba" == loc:
            self.startPath = '/var/lib/samba'
            self.callRemote('renderFolders')
        else:
            # This is a usb drive so we must mount it first
            lp = os.listdir('/dev/disk/by-id/')
            device = ""
            for disk in lp:
                if loc in disk and "part" in disk:
                    device = disk
            if device:
                mount = "mkdir -p /mnt/backup; mount /dev/disk/by-id/%s /mnt/backup 2>&1" % (device,) 
                self.startPath = '/mnt/backup'
                return utils.getProcessOutput('/bin/sh', ['-c', mount], errortoo=1).addCallbacks(returnt, returnt)
            else:
                self.startPath = '/mnt'
                self.callRemote('renderFolders')
        return True
    athena.expose(changeLocation)

    def getFolders(self, path=""):
        #if not path:
        #    path = self.p
        self.lastFolder = path
        try:
            p = os.walk(str(self.startPath +'/'+ path))
            l = [unicode(i) for i in p.next()[1]]
        except:
            l = []
        l.sort()
        self.callRemote('updatePane', unicode(path))
        print l 
        return l
    athena.expose(getFolders)
    
    def getFiles(self, path=None):
        p = os.walk(str(self.startPath +'/'+ path))
        try:
            l = p.next()
            folders = [(u'folder', unicode(i), unicode("%.2f" % (os.stat(str(self.startPath +'/'+ path+'/'+i))[6]/1024))) for i in l[1]]
            files   = [(u'file', unicode(i), unicode("%.2f" % (os.stat(str(self.startPath +'/'+ path+'/'+i))[6]/1024))) for i in l[2]]
        except:
            # Could be blank directory..
            folders = []
            files = []
        folders.sort()
        files.sort()
        return folders, files
    athena.expose(getFiles)

    def statPath(self, path=None):
        if path:
            self.lastFile = path

        def failure(eek):
            print "FAILURE: ", eek
            return 0,0,0,0,0
        def afterFile(fAns):
            file = unicode(fAns.split(':', 1)[-1])
            print file
            stats = os.stat(str(self.startPath +'/'+ path))
            size   = unicode("%.2f" % (stats[6]/1024))
            mod    = unicode(time.ctime(stats[stat.ST_MTIME]))
            create = unicode(time.ctime(stats[stat.ST_CTIME]))

            return file, size, mod, create

        return utils.getProcessOutput('/usr/bin/file', [self.startPath + '/' + str(path)], errortoo=1).addCallbacks(afterFile, failure)

    athena.expose(statPath)

    def cutFile(self, path):
        self.clipAction = CLIP_CUT
        self.clipboard = str(self.startPath + '/' +path)
        return True
    athena.expose(cutFile)

    def copyFile(self, path):
        self.clipAction = CLIP_COPY
        self.clipboard = str(self.startPath + '/' +path)
        return True
    athena.expose(copyFile)

    def pasteFile(self):
        currentFolder = self.startPath + '/' + self.lastFolder
        def returnt(_):
            return True
        if self.clipAction == CLIP_COPY:
            # Copy file
            print "Copy", self.clipboard, currentFolder
            return utils.getProcessOutput('/bin/cp', ['-a', self.clipboard, currentFolder], errortoo=1).addCallbacks(returnt, returnt)
        elif self.clipAction == CLIP_CUT:
            # Move file
            print "Move", self.clipboard, currentFolder
            return utils.getProcessOutput('/bin/mv', [self.clipboard, currentFolder], errortoo=1).addCallbacks(returnt, returnt)
        else:
            # Huh?
            return False
        return True
    athena.expose(pasteFile)

    def renameFile(self, path):
        # Not sure how to implement this yet...
        return True
    athena.expose(renameFile)

    def deleteFile(self):
        # Delete the file!
        print "remove ", self.startPath + '/' + self.lastFile
        def returnt(_):
            print _
            return True
        return utils.getProcessOutput('/bin/rm', ['-rf', str(self.startPath+'/'+self.lastFile)], errortoo=1).addCallbacks(returnt, returnt)
    athena.expose(deleteFile)


class Page(PageHelpers.DefaultAthena):
    moduleName = 'fileBrowser'
    moduleScript = 'fileBrowser.js'
    docFactory = loaders.xmlfile('livepage.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, avatarId, db, *a, **kw):
        PageHelpers.DefaultAthena.__init__(self, avatarId, db, *a, **kw)

    def render_thisFragment(self, ctx, data):
        """ Renders liveGraphFragment instance """
        f = browserFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src='/images/tools-lg.py'), " Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/netdrive.png"), " File Browser"],
            tags.invisible(render=tags.directive('thisFragment'))
        ]

