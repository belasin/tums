from nevow import rend, loaders, tags as T, athena, inevow, guard, url 
from nevow.util import Expose
from nevow import static
from twisted.internet import reactor
import formal


#Shortcut pointers
template = loaders.xmlfile
stan = loaders.stan
exposeAthena = athena.expose

class Standard(formal.ResourceMixin, rend.Page):
    """A simple page with formal mixin.
    Methods: 
        head(self)
            defines content of the head tag in the page
        body(self)
            defines content of the body tag
    """
    arbitraryArguments = False
    addSlash = True
    childPages = {}
    title = ""

    def __init__(self, avatarId = None, enamel = None, arguments = [], *a, **k):
        formal.ResourceMixin.__init__(self, *a, **k)
        rend.Page.__init__(self, *a, **k)
        self.avatarId = avatarId
        self.enamel = enamel
        self.arguments = arguments
        self.docFactory = self.document()

    def document(self):
        return stan(
            T.html[
                T.head[
                    T.invisible(render=T.directive('head'))
                ],
                T.body[
                    T.invisible(render=T.directive('body'))
                ]
            ]
        )


    def childFactory(self, ctx, name):
        if name in self.childPages:
            return self.childPages[name](self.avatarId, self.enamel)

    def head(self):
        return ""

    def body(self):
        return ""

    def render_head(self, ctx, data):
        return ctx.tag[
            T.title[self.title], 
            self.head()
        ]

    def render_body(self, ctx, data):
        return ctx.tag[
            self.body()
        ]

    def locateChild(self, ctx, segs):
        page = rend.Page.locateChild(self, ctx, segs)
        if self.arbitraryArguments:
            # A dodgey hack for passing arguments as child segments to a page
            if page == (None, ()):
                # If we got NotFound return a new instance of myself
                return self.__class__(self.avatarId, self.enamel, arguments=segs), ()
        
        return page

    def logout(self):
        pass

class Login(Standard):
    """ Login this provides our authentication wrapper and login page.
    """
    def document(self):
        return stan(T.html[
        T.head[T.invisible(render=T.directive('head'))],
        T.body[
            T.form(action=url.root.child(guard.LOGIN_AVATAR), method="post", id="loginForm")[
                T.table(style="text-align: center")[
                    T.tr[
                      T.td[
                          T.label(_for="username")["Username:"]
                      ],
                      T.td[
                          T.input(type="text", id="username", name="username")
                      ]
                    ],
                    T.tr[
                      T.td[
                          T.label(_for="password")["Password:"]
                      ],
                      T.td[
                          T.input(type="password",id="password",name="password")
                      ]
                    ],
                    T.tr[
                      T.td(colspan="2", style="text-align:left")[
                        T.label(_for="rememberMe")["Remember Me"],
                        T.input(type="checkbox",id="rememberMe", name="rememberMe")
                      ]
                    ],
                    T.tr[
                      T.td(colspan="2", style="text-align: center")[
                          T.input(type="submit", value="Login")
                      ]
                    ]
                ]
            ]
        ]
    ])

    def render_head(self, ctx, data):
        return T.title['Login']


class Athena(athena.LivePage):
    addSlash = True

    elements = {}

    title = ''

    BOOTSTRAP_MODULES = ['Divmod', 'Divmod.Base', 'Divmod.Defer', 'Divmod.Runtime', 'Nevow', 'Nevow.Athena']

    def __init__(self, avatarId = None, enamel = None, *a, **k):
        print "Initialisation"
        mods = athena.jsDeps.mapping
        self.avatarId = avatarId
        self.enamel = enamel

        for moduleName, t in self.elements.items():
            fragment, fragmentClass, script = t
            mods[moduleName] = script
            setattr(self, 'render_%s' % moduleName, self.fragmentRenderer(fragment, unicode(fragmentClass), moduleName))
            setattr(self, 'element_%s' % moduleName, T.invisible(render=T.directive(moduleName)))

        athena.LivePage.__init__(self, jsModules = athena.JSPackage(mods) )
        self.docFactory = self.document()

    def document(self):
        return stan(T.html[
            T.head[T.invisible(render=T.directive('head'))],
            T.body[T.invisible(render=T.directive('body'))]
        ])


    def fragmentRenderer(self, fragment, jsClass, moduleName):
        def renderer(ctx, data):
            frag = fragment(self.avatarId, self.enamel, jsClass, moduleName)
            frag.setFragmentParent(self)
            return ctx.tag[frag]
        return renderer

    def head(self):
        return ""

    def body(self):
        return ""

    def render_head(self, ctx, data):
        return ctx.tag[
            T.title[self.title],
            self.head(),
            T.invisible(render=T.directive('liveglue'))
        ]

    def render_body(self, ctx, data):
        return ctx.tag[
            self.body()
        ]


class AthenaFragment(athena.LiveFragment):

    jsClass = u''

    kicks = []
    startDelay = 1

    def __init__(self, avatarId=None, enamel=None, jsClass=u'', moduleName='', *a, **kw):
        self.jsClass = jsClass
        self.avatarId = avatarId
        self.enamel = enamel
        athena.LiveFragment.__init__(self, *a, **kw)
        for kick in self.kicks:
            reactor.callLater(1, self.callRemote, kick)
        self.moduleName = moduleName
        self.docFactory = self.document()

    def document(self):
        return stan(T.div(render=T.directive('liveFragment'))[
            T.invisible(render=T.directive('element'))
        ])

    def element(self):
        return ""
    
    def render_element(self, ctx, data):
        return ctx.tag[self.element()]
