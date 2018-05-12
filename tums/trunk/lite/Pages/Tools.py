from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings
from Core import PageHelpers, AuthApacheProxy

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[self.text.tools]]

    def sideMenu(self, ctx, data):
        return tags.div(id="sideCont")[
            #tags.a(_class="MenuOptionLink", href="http://%s/pma" % (str(url.URL.fromContext(ctx)).split('//')[-1].split(':')[0]), 
            #    target="display", title="MySQL database administration"
            #    )['MySQL Administration'],
            #tags.br,
            #B
            tags.a(_class="MenuOptionLink", href=url.root.child("Backup"), title = self.text.toolsMenuBackupsTooltip, onclick="showElement('loading');")[self.text.toolsMenuBackups],
            tags.br,
            #D
            tags.a(_class="MenuOptionLink", href=url.root.child("Dhcp"), title= self.text.toolsMenuDHCPTooltip, onclick="showElement('loading');")[self.text.toolsMenuDHCP], 
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("Computers"), title= self.text.toolsMenuComputersTooltip, onclick="showElement('loading');")[self.text.toolsMenuComputers],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("GroupMatrix"), title = self.text.toolsMenuDomainGroupsTooltip, onclick="showElement('loading');")[self.text.toolsMenuDomainGroups],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("SambaConfig"), title = self.text.toolsMenuDomainSetupTooltip, onclick="showElement('loading');")[self.text.toolsMenuDomainSetup],
            tags.br,
            #F
            tags.a(_class="MenuOptionLink", href=url.root.child("FileBrowser"), title = self.text.toolsMenuBrowserTooltip, onclick="showElement('loading');")[self.text.toolsMenuBrowser],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("Samba"), title = self.text.toolsMenuFileSharesTooltip, onclick="showElement('loading');")[self.text.toolsMenuFileShares],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("Firewall"), title = self.text.toolsMenuFirewallTooltip, onclick="showElement('loading');")[self.text.toolsMenuFirewall],
            tags.br,
            #M
            tags.a(_class="MenuOptionLink", href=url.root.child("Mailserver"), title = self.text.toolsMenuMailTooltip, onclick="showElement('loading');")[self.text.toolsMenuMail],
            tags.br,
            #N
            tags.a(_class="MenuOptionLink", href=url.root.child("Network"), title = self.text.toolsMenuNetconfTooltip, onclick="showElement('loading');")[self.text.toolsMenuNetconf],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("Netdrive"), title = self.text.toolsMenuNetdriveTooltip, onclick="showElement('loading');")[self.text.toolsMenuNetdrive],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("PPP"), title = self.text.toolsMenuPPPTooltip, onclick="showElement('loading');")[self.text.toolsMenuPPP],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("Profiles"), title = self.text.toolsMenuProfilesTooltip, onclick="showElement('loading');")[self.text.toolsMenuProfiles],
            tags.br,
            tags.a(_class="MenuOptionLink", title = self.text.toolsMenuQOSTooltip, href=url.root.child("Qos"))[self.text.toolsMenuQOS],
            tags.br,
            tags.a(_class="MenuOptionLink", title = self.text.toolsMenuPolicyTooltip, href=url.root.child("Policy"))[self.text.toolsMenuPolicy],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("VPN"), title = self.text.toolsMenuVPNTooltip, onclick="showElement('loading');")[self.text.toolsMenuVPN],
            tags.br,
            tags.a(_class="MenuOptionLink", href=url.root.child("Squid"), title= self.text.toolsMenuWebProxyTooltip, onclick="showElement('loading');")[self.text.toolsMenuWebProxy],
        ]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[
            self.sideMenu(ctx, data)
        ]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h2[tags.img(src="/images/toolsman.png",alt="Tools"), self.text.tools],
            tags.p[self.text.toolsInstruction]
        ]
