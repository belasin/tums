from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, formal
from Core import PageHelpers
from Pages import Users, Reports

logs = [
        ('/var/log/dhcpd.log',      'DHCP'),
        ('/var/log/imapd.log',      'IMAP'),
        ('/var/log/syslog',         'Syslog'),
        ('/var/log/messages',       'Messages'),
        ('/var/log/user.log',       'User log'),
        ('/var/log/shorewall.log',  'Firewall'),
        ('/var/log/cron.log',       'Scheduler'),
        ('/var/log/slapd.log',      'Directory'),
        ('/var/log/localproc.log',  'Local System'),
        ('/var/log/mail.log',       'Mail general'),
        ('/var/log/auth.log',       'Authentication'),
        ('/var/log/ppp.log',        'ADSL/Dialup Logs'),
        #('/var/log/exim/exim_reject.log', 'Mail Rejected'),
    ]

class Page(PageHelpers.DefaultPage):
    addSlash = True
    #docFactory  = loaders.xmlfile('framed.xml', templateDir=Settings.BaseDir+'/templates')
    def __init__(self, avatarId=None, db=None, logfile="/var/log/user.log", cnt=['', 1], *a, **kw):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **kw)
        self.logfile=logfile
        self.cnt = cnt

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def form_selectLog(self, ctx):
        form = formal.Form()
        
        form.addField('log', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = logs),
            label = "Log to view")

        form.addAction(self.selectLog)
        return form

    def selectLog(self, ctx, form, data):
        return url.root.child('Logs').child(data['log'].replace('/', '+')).child('1')

    def locateChild(self, ctx, seg):
        print seg
        if seg[0]:
            return Page(self.avatarId, self.db, seg[0].replace('+', '/'), seg), ()

        return Page(self.avatarId, self.db), ()
    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]

    def render_content(self, ctx, seg):
        f = open(self.logfile)
        blob = f.read().split('\n')
        cnt = 1
        entries = []
        for l in blob[-1000:]:
            line = l.strip('\n')
            if line:
                #Jan  4 11:05:21 lilith imapd: Disconnected, ip=[::ffff:172.31.0.254], time=0
                parts = line.split()
                date = ' '.join(parts[:3])
                host = parts[3]
                service = parts[4].strip(':')
                message = ' '.join(parts[5:])
                if cnt%2:
                    back = "#DDDDDD"
                else:
                    back = "#EEEEEE"
                if entries and service==entries[-1][1] and date==entries[-1][0]:
                    entries[-1][2].extend([tags.br, message])
                else:
                    cnt+=1
                    entries.append([date, service, [message], back])
        count = int(self.cnt[1])*-1
        pages = len(entries)/20
        thisPage = int(count/-20)
        print pages, thisPage, count, count-20
        pageSelect = []
        for i in range(pages):
            if i == thisPage:
                pageSelect.append(tags.strong[str(i+1)])
            else:
                pageSelect.append(tags.a(href=url.root.child("Logs").child(self.logfile.replace('/', '%2B')).child(str((i*20)+1)))[str(i+1)])
            
            if i < (pages-1):
                pageSelect.append(' | ')
        
        return ctx.tag[
                tags.h3["Select Log"],
                tags.directive('form selectLog'),
                tags.h3["Viewing %s"%(self.logfile,)],
                "[ ", pageSelect, " ]", tags.br,
                tags.table[
                    [ 
                        tags.tr(style="background: %s;" % i[3])[
                            tags.td[i[0]],
                            tags.td[i[1]],
                            tags.td[i[2]],
                        ]
                    for i in reversed(entries[count-20:count])]
                ]
        ]
        
