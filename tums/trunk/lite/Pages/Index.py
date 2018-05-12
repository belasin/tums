from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static, twcgi
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import Tree, Settings, LDAPDir
from Core import PageHelpers
from Pages import ConfWiz

class Page(rend.Page):
    db = None

    def __init__(self, db, *a, **kw):
        rend.Page.__init__(self, *a, **kw)
        self.db = db

    def childFactory(self, ctx, seg):
        if seg=="Wizard":
            return ConfWiz.Page()
        else:
            return rend.Page.childFactory(self, ctx, seg)

    addSlash = True
    child_css = static.File(Settings.BaseDir+'/css/')
    child_scripts = static.File(Settings.BaseDir+'/scripts/')
    child_images = static.File(Settings.BaseDir+'/images/')
    child_php = static.File('/var/www/localhost/htdocs/')
    
    def render_content(self, ctx, data):
        if self.db[0] == "FIRSTRUN":
            return ctx.tag[
                tags.table(height="100%", width="100%")[
                    tags.tr(height="100%")[
                        tags.td[
                            tags.div(id="centerBox", valign="middle")[
                                tags.div(id="blockTop")[""],
                                tags.div(id="centerBlock")[
                                    tags.h1(style="color:#fff;font-family:arial;")["TUMS Installation Wizard"]
                                ],
                                tags.div(id="menuBlock")[
                                    tags.div(style="margin-top:-5em; text-align:left; font-family:arial; color:#786D38;")[
                                        tags.h3["Welcome to the TUMS installation wizard."],
                                        """This wizard will guide you through an initial configuration of the host system.
                                        This should be carried out by a Thusa employee. If your server has arrived unconfigured it
                                        is recommended that you contact Thusa support for this to be carried out. 
                                        """, tags.br,
                                        """Click the NEXT button bellow to continue with the installation""",tags.br,tags.br,
                                        tags.a(href="Wizard/1/")[tags.img(src='/images/next.png')]
                                    ]
                                ]
                            ]
                        ]
                    ]
                ]
            ]
        return ctx.tag[
            tags.a(href="/auth/")["Login"]
        ]

    def render_head(self, ctx, data):
        if self.db[0] == "FIRSTRUN":
            return ctx.tag[
                tags.link(rel="stylesheet", type="text/css", href="/css/login.css")
            ]
        return ctx.tag[
            tags.xml('<meta http-equiv="refresh" content="0;url=auth/"/>')
        ]

    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.title["TUMS"],
                tags.invisible(render=tags.directive('head'))
            ],
            tags.body[
                tags.invisible(render=tags.directive('content'))
            ]
        ]
    )

