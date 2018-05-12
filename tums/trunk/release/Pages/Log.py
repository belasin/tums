from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, formal, sha, time, os
from Core import PageHelpers
from Pages import Reports

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
        ('/var/log/exim4/mainlog',       'Mail Server'),
        ('/var/log/auth.log',       'Authentication'),
        ('/var/log/ppp.log',        'ADSL/Dialup Logs'),
        ('/var/log/tums-audit.log',        'Vulani user logs'),
        #('/var/log/exim/exim_reject.log', 'Mail Rejected'),
    ]

class Page(Reports.Page):
    addSlash = True
    #docFactory  = loaders.xmlfile('framed.xml', templateDir=Settings.BaseDir+'/templates')
    def __init__(self, avatarId=None, db=None, logfile="/var/log/user.log", cnt=['', 1], *a, **kw):
        Reports.Page.__init__(self, avatarId, db, *a, **kw)
        self.logfile=logfile
        self.cnt = list(cnt) + ["", None, None]
        self.vlogs = [i[0] for i in logs]

    def form_selectLog(self, ctx):
        form = formal.Form()
        
        form.addField('log', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = logs),
            label = "Log to view")

        form.addAction(self.selectLog)
        return form

    def selectLog(self, ctx, form, data):
        return url.root.child('Logs').child(data['log'].replace('/', '+')).child('1')

    def form_filterLog(self, ctx):
        form = formal.Form()
        form.addField('filter', formal.String(), label = "Filter", description = "Filter log file. Append '--' to the start of the filter to invert")

        form.data['filter'] = self.cnt[2] or ""

        form.addAction(self.filterLog)
        return form

    def filterLog(self, ctx, form, data):
        
        return url.root.child('Logs').child(self.logfile.replace('/', '+')).child('1').child(data['filter'] or "")

    def locateChild(self, ctx, seg):
        if seg[0]:
            return Page(self.avatarId, self.db, seg[0].replace('+', '/'), seg), ()

        return Page(self.avatarId, self.db), ()

    def render_content(self, ctx, seg):
        if self.logfile in self.vlogs:
            # Get file size
            sz = os.stat(self.logfile).st_size
            f = open(self.logfile)
            # Don't read more than 1MB
            if sz > 1024000:
                # Seek to 1MB quick
                f.seek(sz - 1024000)
                # Throw this line away. 
                _ = f.readline()
        else:
            return ctx.tag["Invalid log"]

        cnt = 1
        entries = []
        for l in f:
            line = l.strip('\n')

            if line and 'exim4' in self.logfile:
                parts = line.split()
                date = ' '.join(parts[:2])
                mid = parts[2]
                message = ' '.join(parts[2:])
                if cnt%2:
                    back = "#DDDDDD"
                else:
                    back = "#EEEEEE"
                if entries and 'mailsvr'==entries[-1][1] and date==entries[-1][0]:
                    # Merge items
                    entries[-1][2].extend([tags.br, message])
                else:
                    cnt+=1
                    entries.append([date, 'mailsvr', [message], back])

            elif line:
                if 'tums-audit' in self.logfile:
                    parts = line.split()
                    date = ' '.join(parts[:4])
                    host = ""
                    service = parts[4]
                    message = ' '.join(parts[5:])
                else:
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
                    # Merge line items
                    entries[-1][2].extend([tags.br, message])
                else:
                    cnt+=1
                    entries.append([date, service, [message], back])

        # Filter the log
        if self.cnt[2]:
            oldEntries = entries
            entries = []
            for i in oldEntries:
                skip = False
                
                messages = i[2]
                msg = ''.join(messages)
                    
                if "--" == self.cnt[2][:2]:
                    if self.cnt[2][2:] in msg:
                        # Filter line found
                        skip = True
                else:
                    if not (self.cnt[2] in msg):
                        # Filter line not found
                        skip = True

                if not skip:
                    entries.append(i)
                else:
                    pass
                    #print messages, "SKIPPED"
 
        # Paginate the returned log.
        count = int(self.cnt[1])*-1
        pages = len(entries)/20
        thisPage = int(count/-20)
        pageSelect = []
        for i in range(pages):
            if i == thisPage:
                pageSelect.append(tags.strong[str(i+1)])
            else:
                if self.cnt[2]:
                    childLink = url.root.child("Logs").child(self.logfile.replace('/', '+')).child(str((i*20)+1)).child(self.cnt[2])
                else:
                    childLink = url.root.child("Logs").child(self.logfile.replace('/', '+')).child(str((i*20)+1))
                    
                pageSelect.append(
                    tags.a(
                        href=childLink
                    )[str(i+1)]
                )
            
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
                ], 
                tags.br, 
                tags.h3["Apply filter"], 
                tags.directive('form filterLog')
        ]
        
