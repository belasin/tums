from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, log
from twisted.internet import defer

from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os, datetime, sha
import Tree, Settings
from Core import PageHelpers, confparse, Utils, WebUtils
from Pages import Reports

class Page(Reports.Page):
    docFactory  = loaders.xmlfile('overview.xml', templateDir=Settings.BaseDir+'/templates')

    daymap = {
        'M':'Monday',
        'T':'Tuesday',
        'W':'Wednesday',
        'H':'Thursday',
        'F':'Friday',
        'A':'Saturday',
        'S':'Sunday',
    }

    def render_updates(self, ctx, data):
        def gotDetails(dlcache, totals):
            
            cache = {
                'linux'     : dlcache[0][1],
                'microsoft'   : dlcache[1][1],
            }

            update = {}

            print totals

            data = [
                ("Linux", 1 + int(totals.get('linux', [0,1000])[1])/1000),
                ("Windows", 1 + int(totals.get('microsoft', [0,1000])[1])/1000),
            ]

            pie = tags.img(src = "/chart?type=pie&width=500&height=250&%s" %
                (   
                    '&'.join(["lables=%s&data=%s" % (l, d) for l,d in data])
                )
            )

            def statSet(type):
                saving = 0
                for t, n, hit, size in cache[type]:
                    h = hit or 0
                    s = size or 0 
                    saving += (h * s)

                return [
                    tags.strong["Hits vs Downloads"],
                    tags.br,
                    tags.img(src='/chart?type=pie&width=500&height=250&lables=Downloads&data=%s&lables=Hits&data=%s' % (
                        len(cache[type]) or 1,
                        totals[type][0] or 1
                    )),
                    tags.br,
                    tags.strong["Efficiency ratio: "], "%.2f" % (len(cache[type])/float(totals[type][0]+1)),
                    tags.br,
                    tags.strong["Saving: "], Utils.intToH(saving),
                    tags.br, tags.br
                ]

            def overallSavings():
                savings = {}
                totalSaving = 1
                for i in ['microsoft', 'linux']:
                    saving = 1
                    for t,n, hit, size in cache[i]:
                        h = hit or 0
                        s = size or 0 
                        saving += (h * s)
                    savings[i] = saving
                    totalSaving += saving

                savingCon = []
                for i in ['microsoft', 'linux']:
                    size = Utils.intToH(savings[i])
                    savingCon.append(("%s%%20[%s]" %(i.capitalize(), size), savings[i]))

                l = '&'.join(["lables=%s&data=%s" % (i,j) for i,j in savingCon])
                return tags.img(src='/chart?type=pie&width=500&height=250&%s' % l)

            tabCols = [
                ('str', 'Filename'), 
                #('isodate', 'Last Accessed'), 
                #('isodate', 'First Downloaded'), 
                ('int', 'Hits'), 
                ('int', 'Size'), 
            ]

            return ctx.tag[
                PageHelpers.TabSwitcher((
                    ('Stats', 'panelStats'),
                    ('Windows', 'panelWindows'),
                    ('Linux',   'panelLinux'),
                    #('AntiVirus', 'panelAntivirus')
                ), id="update"),
                tags.div(id='panelStats', _class='tabPane')[
                    tags.h3["Stats"],
                    tags.strong["Disk utilisation"],tags.br,
                    pie,
                    tags.br,
                    tags.strong["Overall savings"],tags.br,
                    overallSavings(),
                    tags.br,
                    tags.strong["Total Use:"], Utils.intToH(totals['total'][1])
                ],
                tags.div(id='panelWindows', _class='tabPane')[
                    tags.h3[tags.img(src="/images/windows.png"), "Windows update cache"],
                    statSet('microsoft'),
                    tags.h3["Most signficant updates"], 
                    PageHelpers.dataTable(tabCols,
                        [(
                            i[1], 
                            i[2] or 0, 
                            Utils.intToH(i[3] or 0),
                        ) for i in cache.get('microsoft',[])[-10:]], sortable = True
                    )
                ],
                tags.div(id='panelLinux', _class='tabPane')[
                    tags.h3[tags.img(src="/images/penguin.png"), "Linux update cache"],
                    statSet('linux'),
                    tags.h3["Most signficant updates"], 
                    PageHelpers.dataTable(tabCols,
                        [(
                            i[1], 
                            i[2] or 0, 
                            Utils.intToH(i[3] or 0),
                        ) for i in cache.get('linux',[])[-10:]], sortable = True
                    )
                ],
                #tags.div(id='panelAntivirus', _class='tabPane')[
                #    ""
                #],
                PageHelpers.LoadTabSwitcher(id="update")
            ]

        def getFiles(totals):
            tots = {
                'microsoft': (0,0),
                'adobe': (0,0),
                'linux': (0,0),
            }
            todata = 0
            tohit = 0
            for i in totals:
                todata += i[2]
                tohit += i[1]
                tots[i[0].encode()] = (i[1], i[2])
            tots['total'] = (tohit, todata)

            print tots
            
            return defer.DeferredList([
                self.db[4].getFilesByType('linux'),
                self.db[4].getFilesByType('microsoft'),
                self.db[4].getFilesByType('adobe')
            ]).addBoth(gotDetails, tots)

        return self.db[4].getTotals().addBoth(getFiles)

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src='/images/proxy.png'), " Update cache"],
            tags.invisible(render=tags.directive('updates'))
        ]
