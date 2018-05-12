from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, os
import Tree, Settings
from Core import PageHelpers, WebUtils
from Pages import Reports

def error(_):
    print "Ooops" , _
    return [[None for i in xrange(30)]]

class Page(Reports.Page):
    def locateChild(self, ctx, segs):
        if segs[0] == "Delete":
            id = segs[1]
            def ret(_):
                return url.root.child('MailQueue')
            return WebUtils.system('exim -Mrm %s' % id).addBoth(ret), ()

        if segs[0] == "Flush":
            domain = segs[1]
            def ret(_):
                return url.root.child('MailQueue')
            return WebUtils.system('exim -Rff %s' % domain).addBoth(ret), ()

        return Reports.Page.locateChild(self, ctx, segs)

    def render_exiqsum(self, ctx, seg):
        def eximq(stdout):
            table = []
            for l in stdout.split('\n'):
                line = l.strip().split()
                if line:
                    num, vol, old, new, domain = tuple(line)
                    table.append((domain, num, vol, old, new, tags.a(href="/auth/MailQueue/Flush/%s/" % domain)["Resend"]))

            return ctx.tag[
                tags.h3["Domain queue"], 
                PageHelpers.dataTable(('Domain', 'Number', 'Volume', 'Oldest', 'Newest', ''), table, sortable = True)
            ]
        
        return WebUtils.system('mailq | exiqsumm | head -n -3 | tail -n +5').addBoth(eximq)
    
    def render_content(self, ctx, seg):
        def processMailq(res):
            lastHead = ""
            destinations = {}
            stat = {}
            # Create a sensible list
            for j in res.split('\n'):
                l = j.strip()

                if not l:
                    lastHead = ""
                    continue

                if not lastHead:
                    lastHead = l.split()
                    destinations[lastHead[2]] = []
                    stat[lastHead[2]] = (lastHead[0], lastHead[1])
                else:
                    destinations[lastHead[2]].append(l)

            data = []

            # Deconstruct our input queue
            flist = {}
            for d, n, v in os.walk('/var/spool/exim4/input'):
                sub = d
                for f in v:
                    if (f[-1] == "D") and (len(f) > 10):
                        id = f[:-2]
                        flist[id] = sub


            for id, d in stat.items():
                mailstat = stat[id]
                fi = "%s/%s-H" % (flist[id], id)
                try:
                    fip = open(fi)
                except:
                    #Was unable to open the file
                    continue
                to = "Unknown"
                fromm = "Unknown"
                subject = "Unknown"

                for ln in fip:
                    try:
                        l = ln.strip('\n').strip()
                        if "To:" in ln:
                            if ln.split()[1] == 'To:':
                                to = ln.split(': ')[-1]
                        if "Subject:" in ln:
                            if ln.split()[1] == 'Subject:':
                                subject = ln.split(': ')[-1]
                        if "From:" in ln:
                            if ln.split()[1] == 'From:':
                                fromm = ln.split(': ')[-1]
                    except Exception, e:
                        print "Processing error", e
                    
                data.append([
                    id, to, fromm, subject, [[i, tags.br] for i in destinations[id]],mailstat[0], mailstat[1], 
                    tags.a(href=url.root.child('MailQueue').child('Delete').child(id))[
                        tags.img(src='/images/ex.png')
                    ]
                ])

            return ctx.tag[
                tags.invisible(render=tags.directive('exiqsum')),
                tags.h3["Mail Queue"],
                PageHelpers.dataTable(('ID', 'To', 'From', 'Subject', 'Pending', 'Delay', 'Size', ''), 
                    data, sortable = True
                )
            ]
        return WebUtils.system('mailq').addBoth(processMailq)
