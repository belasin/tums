from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, datetime
import Tree, Settings, Database
from Core import PageHelpers, Utils
from Pages import Users, Reports

class Page(PageHelpers.DefaultPage):
    docFactory  = loaders.xmlfile('overview.xml', templateDir=Settings.BaseDir+'/templates')

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def roundedBlock(self, title, content):
        return tags.div(_class="roundedBlock")[tags.h1[title],tags.div[content]]

    def render_content(self, ctx, seg):
        ci = open('/proc/cpuinfo')
        cpuInfo = {}
        numCPU = 0
        for i in ci:
            l = i.strip('\n').strip().split(':')
            if "processor" in l[0]:
                numCPU += 1
            else:
                try:
                    cpuInfo[l[0].strip()] = l[1].strip()
                except:
                    pass

        pmi = open('/proc/meminfo')
        memDetail = {}
        for i in pmi:
            l = i.strip('\n').strip()
            if l:
                key, val = tuple(l.split(':'))
                val = val.split()[0]
                
                memDetail[key] = int(val)

        return ctx.tag[
            tags.h3[tags.img(src="/images/system.png"), " System Details"],
            tags.br,
            tags.table(width="100%")[tags.tr[
                tags.td(width="50%",valign="top")[
                    self.roundedBlock("CPU", [
                        tags.table[
                            tags.tr[
                                tags.td["Processors:"],
                                tags.td[numCPU]
                            ],
                            tags.tr[
                                tags.td["Model:"],
                                tags.td[cpuInfo['model name']]
                            ],
                            tags.tr[
                                tags.td["CPU Speed:"],
                                tags.td["%0.2fGhz" % (float(cpuInfo['cpu MHz'])/1024.0)]
                            ]
                        ],
                        tags.a(href=url.root.child("Graphs").child("load"))[tags.img(src="/images/graphs/graph-loadFS.png")]
                    ]),
                    self.roundedBlock("Memory Usage", [
                        tags.table[
                            tags.tr[
                                tags.td["Total Active:"],
                                tags.td[PageHelpers.progressBar(memDetail['Active']/float(memDetail['MemTotal']))],
                            ]
                        ],
                        tags.a(href=url.root.child("Graphs").child("io"))[tags.img(src="/images/graphs/ioFS.png")],
                    ]),
                ],
                tags.td(width="50%",valign="top")[
                   self.roundedBlock("Network Usage", [
                        tags.h3["Traffic routed"],
                        tags.a(href=url.root.child("Graphs").child("totals"))[tags.img(src="/images/graphs/totalsFS.png")]
                    ])
                ]
            ]]
        ]
