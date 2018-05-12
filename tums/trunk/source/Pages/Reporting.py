from nevow import rend, loaders, tags
from twisted.internet import reactor, defer
from nevow import inevow, rend, url, stan

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, Utils, WebUtils
from Pages import Tools
import formal

class Page(Tools.Page):
    addSlashes = True

    def form_createMapping(self, ctx):
        def handleSubmit(ctx, form, data):
            if not data["userSelect"] and not data["user"]:
                raise formal.FormError("Please provide a valid user entry to map to")
            if not data["addrSelect"] and not data["addr"]:
                raise formal.FormError("Please provide a valid address to map")
            user = data["userSelect"] and data["userSelect"] or data["user"]
            addr = data["addrSelect"] and data["addrSelect"] or data["addr"]
            r = self.sysconf.Reporting
            mappings = r.get('userMappings', {})
            userEnt = mappings.get(user, [])
            userEnt.append(addr)
            mappings[user] = userEnt
            r["userMappings"] = mappings
            self.sysconf.Reporting = r

        def gotResolved(res):
            form = formal.Form()
            addr = []
            for address in entries:
                if address[0] in res:
                    nam = (address[1],res[address[0]])
                else:
                    nam = (address[1],address[0])
                addr.append((address[1], "%s(%s)" % nam))
            userWidgetFactory = formal.widgetFactory(formal.SelectChoice, options=self.getUsers())
            addressWidgetFactory = formal.widgetFactory(formal.SelectChoice, options=addr)
            form.addField('userSelect', formal.String(), userWidgetFactory, label="User")
            form.addField('user', formal.String(), label="")
            form.addField('addrSelect', formal.String(), addressWidgetFactory, label="Network Address")
            form.addField('addr', formal.String(), label="")
            form.addAction(handleSubmit)
            return form
        entries = [i for i in PageHelpers.getArp()]
        d = PageHelpers.resolveIP([i[0] for i in entries], True)
        d.addCallback(gotResolved)
        return d

    def getUsers(self):
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,o=%s" % (LDAP.domainToDC(Settings.defaultDomain), Settings.LDAPBase)
        # get users
        return [(i['uid'][0],i['cn'][0]) for i in LDAP.getUsers(l, "ou=People,"+dc)]

    def form_generalConfig(self, ctx):
        def handleSubmit(ctx, form, data):
            print data
        form = formal.Form()

        form.addAction(handleSubmit)
        return form
    
    def render_content(self, ctx, data):
        mappings = []
        for user,userMappings in self.sysconf.Reporting.get('userMappings',{}).items():
            for uMap in userMappings:
                mappings.append([user,uMap,''])
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Reporting Configuration"],
            PageHelpers.TabSwitcher((
                ('General Configuration', 'panelGenConfig'),
                ('User Mappings', 'panelUserMappings'),
            )),
            tags.div(id="panelGenConfig", _class="tabPane")[
                tags.h3["Configuration"],
                tags.directive('form generalConfig')
            ],
            tags.div(id="panelUserMappings", _class="tabPane")[
                tags.h3["User Mapping"],
                PageHelpers.dataTable(["User", "Mac Address or IP Address", ''], mappings, sortable = True),
                tags.h3["Add Mapping"],
                tags.directive('form createMapping')
            ],
            PageHelpers.LoadTabSwitcher()
        ]

