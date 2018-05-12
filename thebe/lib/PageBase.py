from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql
import enamel

from twisted.internet import utils

def TabSwitcher(tabs, id="A"):
    tabNames = [i for j,i in tabs]
    tabLables = [i for i,j in tabs]

    closeTabs = ';\n'.join(["    hideElement('%s'); getElement('tab%s').style.color='#666666';" % (i,i) for i in tabNames])

    switchFunc = """
        tabSwitcher%s = function (tab) {
            %s
            getElement('tab'+tab).style.color='#E710D8';
            showElement(tab);
            createCookie('tabOpen%s', tab);
            return false;
        };
    """ % (id, closeTabs, id)

    return [
        tags.xml("""<script type="text/javascript">
        function createCookie(name,value) {
            var date = new Date();
            date.setTime(date.getTime()+(24*60*60*1000));
            var expires = "; expires="+date.toGMTString();
            document.cookie = name+"="+value+expires+"; path=/";
        }

        function readCookie(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }
        createTabSwitcher%s = function() {
            %s
            var firstTab = '%s';
            showElement(firstTab);
            getElement('tab'+firstTab).style.color='#E710D8';
            try {
                var tab = readCookie('tabOpen%s');
                if (tab) {
                    %s
                    showElement(tab);
                    getElement('tab'+tab).style.color='#E710D8';
                }
            } catch(dontCare){
                showElement(firstTab);
                getElement('tab'+ firstTab).style.color='#E710D8';
            }
        };
        %s
        </script>""" % (id, closeTabs, tabNames[0], id, closeTabs, switchFunc)),
        tags.br, tags.br,
        tags.table(cellspacing=0, cellpadding=0)[tags.tr[
            [
                tags.td(_class = "tabTab", style="padding:0;background-image: url(/images/tabcenter.png); background-repeat: repeat-x;" ,
                    onclick = "return tabSwitcher%s('%s');" % (id,j)
                    )[
                        tags.a(
                            id="tab"+j,
                            href="#",
                            style="color:#666666; text-decoration:none;",
                            title="Switch to the tab: %s" % i,
                            onclick = "return tabSwitcher%s('%s');" % (id,j)
                        )[
                            tags.img(src='/images/lefttab.png', align="absmiddle", style="border:none"),
                            tags.strong[i],
                            tags.img(src='/images/righttab.png', align="absmiddle", style="border:none")
                        ],
                ] for i,j in tabs]
        ]]
    ]

def LoadTabSwitcher(id="A"):
    return tags.script(type="text/javascript")["createTabSwitcher%s();" % id]


class Athena(pages.Athena):

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Dashboard"]]

    def __init__(self, *a, **kw):
        pages.Athena.__init__(self, *a, **kw)

    def document(self):
        return pages.template('default_athena.xml', templateDir='%s/themes/%s/templates/' % (baseDir, theme))

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]
    def render_userMenu(self, ctx, data):
        return ctx.tag[
            "Welcome, ", 
            tags.strong[self.avatarId.username], 
            ". ", 
            tags.a(href="/Password/")['Change Password'], 
            " / ",
            tags.a(href="/__logout__/")['Log out']
        ]

    def render_topMenu(self, ctx, data):
        m = [
            tags.td[
                tags.a(href="/Updates/")["Updates"]
            ],
            tags.td[
                tags.a(href="/Thebe/")["Thebe"]
            ]
        ]
        
        if 1 not in self.avatarId.gids:
            m = ""

        return ctx.tag[
            tags.table[
                tags.tr[
                    tags.td[
                        tags.a(href="/Dashboard/"  )["Dashboard"]
                    ],
                    tags.td[
                        tags.a(href="/ServerUsers/")["Users"]
                    ],
                    tags.td[
                        tags.a(href="/Servers/"    )["Servers"]
                    ],
                    tags.td[
                        tags.a(href="/DNS/"    )["DNS"]
                    ],
                    tags.td[
                        tags.a(href="/Tickets/"     )["Tickets"]
                    ], 
                    tags.td[
                        tags.a(href="/Orders/"      )["Orders"]
                    ],
                    m,
                    tags.td[
                        tags.a(href="/__logout__"    )["Logout"]
                    ],
                ]
            ]
        ]

class Page(pages.Standard):

    def dataTable(self, headings, content, sortable = False, width=""):
        """ Produces a tabular listing which is either sortable or not. Sortable expects headings to be a 
            list of tuples, but if it is not a list of tuples the 'string' type will be assumed for every cell """
        if sortable:
            if isinstance(headings[0], tuple):
                header = [ tags.th(colformat=j)[i] for j,i in headings ]
            else:
                header = [ tags.th(colformat='istr')[i] for i in headings ]
            tclass = 'sortable'
        else:
            header = [ tags.th[i] for i in headings ]
            tclass = 'listing'
        cont = [
            tags.thead(background="/images/gradMB.png")[
                tags.tr[
                    header
                ]
            ],
            tags.tbody[
            [   
                tags.tr[ [tags.td[col] for col in row] ]
            for row in content],
            ]
        ]
        if width:
            return tags.table(cellspacing=0,  _class=tclass, width=width)[cont]
        else:   
            return tags.table(cellspacing=0,  _class=tclass)[cont]


    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Dashboard"]]

    def __init__(self, *a, **kw):
        pages.Standard.__init__(self, *a, **kw)

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (baseDir, theme))

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_userMenu(self, ctx, data):
        return ctx.tag[
            "Welcome, ", 
            tags.strong[self.avatarId.username], 
            ". ", 
            tags.a(href="/Password/")['Change Password'], 
            " / ",
            tags.a(href="/__logout__/")['Log out']
        ]

    def render_topMenu(self, ctx, data):
        m = [
            tags.td[
                tags.a(href="/Updates/")["Updates"]
            ],
            tags.td[
                tags.a(href="/Thebe/")["Thebe"]
            ]
        ]
 
        if 1 not in self.avatarId.gids:
            m = ""

        return ctx.tag[
            tags.table[
                tags.tr[
                    tags.td[
                        tags.a(href="/Dashboard/"   )["Dashboard"]
                    ],
                    tags.td[
                        tags.a(href="/ServerUsers/" )["Users"]
                    ],
                    tags.td[
                        tags.a(href="/Servers/"     )["Server Manager"]
                    ],
                    tags.td[
                        tags.a(href="/DNS/"         )["DNS"]
                    ],
                    tags.td[
                        tags.a(href="/Tickets/"     )["Tickets"]
                    ], 
                    tags.td[
                        tags.a(href="/Orders/"      )["Orders"]
                    ],
                    m,
                    tags.td[
                        tags.a(href="/__logout__"    )["Logout"]
                    ],
 
                ]
            ]
        ]
