from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, datetime, os, sys
import Tree, Settings, Database
from Core import PageHelpers, Utils, WebUtils
from Pages import Reports

class Page(Reports.Page):
    #docFactory  = loaders.xmlfile('overview.xml', templateDir=Settings.BaseDir+'/templates')

    def pieChartImg(self, values):
        cstart = "/chart?type=pie&width=500&height=250&legright=y"

        for l, n in values.items():
            cstart += "&lables=%s&data=%s" % (l, n)

        return tags.img(src=cstart)

    def refilterTable(self, items, total):
        tab = []
        for k,v in items.items():
            tab.append((
                k, 
                Utils.intToH(int(v)*1024)
            ))

        tab.append(('Total', Utils.intToH(total*1024)))

        return tab

    def render_content(self, ctx, seg):
        try:
            stat = eval(open('/usr/local/tcs/tums/rrd/dindex.nid').read())
        except:
            return ctx.tag[
                tags.h3[tags.img(src="/images/system.png"), " Disk Utilisation"],
                tags.br,
                "No statistics have been generated."
            ]

        #unpack it
        home = stat['home']
        shares = stat['shares']
        mail = stat['mail']

        homeTotal   = sum([int(i) for i in home.values()])
        sharesTotal = sum([int(i) for i in shares.values()])
        mailTotal   = sum([int(i) for i in mail.values()])

        return ctx.tag[
            tags.h3[tags.img(src="/images/system.png"), " Disk Utilisation"],
            tags.br,
            tags.h3["Home folders"],
            tags.hr,
            self.pieChartImg(home), 
            PageHelpers.dataTable(['User', 'Utilisation'], self.refilterTable(home, homeTotal)),
            tags.h3["Shared folders"], 
            tags.hr,
            self.pieChartImg(shares), 
            PageHelpers.dataTable(['Folder', 'Utilisation'], self.refilterTable(shares, sharesTotal)),
            tags.h3["Mailboxes"], 
            tags.hr,
            self.pieChartImg(mail),
            PageHelpers.dataTable(['Mailbox', 'Utilisation'], self.refilterTable(mail, mailTotal)),

        ]
