from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree

class Page(rend.Page):
    addSlash = True
    child_css = static.File('./css/')
    child_scripts = static.File('./scripts/')
    child_images = static.File('./images/')
    docFactory = loaders.stan(
        tags.html[
            tags.head[tags.title["Tabbed Page Example"],
                tags.link(rel="stylesheet", href="css/folder-tree-static.css", type="text/css"),
                tags.script(type="text/javascript", src="scripts/folder-tree-static.js")['']
            ],
            tags.body[
                tags.invisible(render=tags.directive('tree'))
            ]
        ]
    )

    def render_tree(self, c, d):
        Tr = Tree.Tree("r","Domains")
        l = Tree.retrieveTree("127.0.0.1", "cn=Manager", "wsthusa", "o=TRYPTOPHAN")
        
        flatL = Tree.flattenTree(l, 'o=TRYPTOPHAN')

        for node in flatL:
            Tree.addPath(node, Tr)

        return Tree.StanTree(Tr)

