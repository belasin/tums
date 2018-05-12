from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.internet import reactor, defer, threads, utils, protocol
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, Utils, WebUtils
from Pages import Tools
import formal

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[self.text.tools]]

    def form_addBackup(self, data):
        form = formal.Form()
        try:
            storageNodes = os.listdir('/proc/scsi/usb-storage/')
        except:
            storageNodes = []
        AvailLetters = []
        usbStorage = {}
        for s in storageNodes:
            l = open('/proc/scsi/usb-storage/%s' % s)
            for i in l:
                ln = i.strip()
                if "Vendor" in ln:
                    vendor = ln.split(':')[-1].strip()
                if "Serial Number" in ln:
                    sn = ln.split(':')[-1].strip().split()[0]

            usbStorage[sn] = vendor
            AvailLetters.append((sn, vendor))

        form.addField('descrip', formal.String(), label = self.text.backupHeaderDescription)

        form.addField('backpath', formal.String(required=True), label = self.text.backupPath, 
            description = self.text.backupPathDescription)

        form.addField('destpath', formal.String(required=True), label = self.text.backupDestination,
            description = self.text.backupDestinationDescription)

        form.addField('notify', formal.String(), label = self.text.backupNotify, 
            description = self.text.backupNotifyDescription)
            
        form.addField('backupdrive', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = AvailLetters), label = self.text.backupDrive)

        form.addField('sched', formal.Boolean(), label = self.text.backupSchedule)
        form.addField('time', formal.Time(), label = self.text.backupTime)

        if AvailLetters: 
            form.data['backupdrive']  = AvailLetters[0]
        form.data['destpath'] = "backup"

        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        try:
            p = open(Settings.BaseDir+'/backup.dat')
        except:
            WebUtils.system('echo > %s/backup.dat' % Settings.BaseDir)
            p = open(Settings.BaseDir+'/backup.dat')
        maxid = 0
        for i in p:
            l = i.strip('\n').strip()
            if l:
                if int(l.split('|')[0]) > maxid:
                    maxid = int(l.split('|')[0])
        current = maxid + 1
        p.close()
        rec = [
            str(current), data['descrip'] or " ", data['notify'] or " ", data['backupdrive'].encode(), 
            data['backpath'].encode(), data['destpath'].encode(), str(data['sched']), str(data['time']) or "Never"
        ]

        p = open(Settings.BaseDir+'/backup.dat', 'a')
        p.write('|'.join([str(i.strip()) for i in rec])+"\n")
        p.close()

        if data['time']:
            time = data['time']
            cr = open('/etc/cron.d/backup%s' % current, 'wt')
            cr.write("%s %s  * * *     root   /usr/local/tcs/tums/runBackup.py %s\n" % (time.minute, time.hour, current))
            cr.close()
            
        return url.root.child('Backup')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        try:
            l = open(Settings.BaseDir+'/backup.dat')
        except:
            WebUtils.system('echo > %s/backup.dat' % Settings.BaseDir)
            l = []

        sets = []
        for i in l:
            if i.strip('\n'):
                dta = i.strip('\n').split('|')
                delmsg = "return confirm('%s');" % self.text.backupConfirmDelete
                if dta[6] =="True":
                    dta[6] = dta[7]
                    dta[7] = [
                        tags.img(src="/images/blankblock.png"), "  ",
                        tags.a(href="Delete/%s/" % (dta[0],), onclick = delmsg)[tags.img(src="/images/ex.png")]
                    ]

                else:
                    dta[6] = "No"
                    dta[7] = [
                        tags.a(href="Execute/%s/" % (dta[0],))[tags.img(src="/images/start.png")], "  ", 
                        tags.a(href="Delete/%s/" % (dta[0],), onclick = delmsg)[tags.img(src="/images/ex.png")]
                    ]

                dta[4] = [ [i, tags.br] for i in dta[4].split(';')]
                dta[2] = [ [i, tags.br] for i in dta[2].split(';')]

                del dta[0]
    
                sets.append(dta)
                
        return ctx.tag[
            tags.h2[tags.img(src="/images/netdrive.png"), self.text.backupSet],
            tags.table(cellspacing=0,  _class='listing')[
                tags.thead(background="/images/gradMB.png")[
                    tags.tr[
                        [ tags.th[i] for i in [
                            self.text.backupHeaderDescription, self.text.backupHeaderNotify, 
                            self.text.backupHeaderDevice, self.text.backupHeaderSource, 
                            self.text.backupHeaderDestination, self.text.backupHeaderAutomated, '']]
                    ]
                ],
                tags.tbody[
                [
                    tags.tr[ [tags.td[col] for col in row] ]
                for row in sets],
                ]
            ],
            tags.h3[self.text.backupCreateSet], 
            tags.directive('form addBackup')
        ]

    def care(self, _):
        print _

    def locateChild(self, ctx, segs):
        if segs[0]=="Execute":
            utils.getProcessOutput(Settings.BaseDir+'/runBackup.py', [segs[1]], errortoo=1).addCallbacks(self.care, self.care)
            return url.root.child('Backup'), ()
        if segs[0]=="Delete":
            p = open(Settings.BaseDir+'/backup.dat')
            backdict = {}
            for backl in p:
                line = backl.strip('\n').split('|')
                backdict[line[0]] = line[1:]
            del backdict[segs[1]]
            p.close()
            po = open(Settings.BaseDir+'/backup.dat', 'wt') 
            keys = backdict.keys()
            keys.sort()
            for backup in keys:
                po.write('|'.join([backup] + backdict[backup])+'\n')
            po.close()
            WebUtils.system('rm -f /etc/cron.d/backup%s' % segs[1])
            return url.root.child('Backup'), ()
        return rend.Page.locateChild(self, ctx, segs)
            
