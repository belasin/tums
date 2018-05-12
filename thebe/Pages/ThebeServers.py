from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha, random

from custom import Widgets

from twisted.internet import utils

from lib import PageBase, system

class Edit(PageBase.Page):
    arbitraryArguments = True
    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Thebe Users"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def form_addServer(self, data):
        editServer = form.Form()
        editServer.addField('name', form.String(), label = "Server Name")
        editServer.addField('key', form.String(), label = "License Key", description="Leave blank to generate a new key")
        editServer.addField('hostname', form.String(), label = "Hostname", description="Hostname by which this server can be accessed")
        editServer.addAction(self.editServer)

        def gotData(result):
            
            editServer.data = {
                'name': result[1],
                'hostname': result[2],
                'key':  result[3]
            }
            return editServer
 
        return self.enamel.storage.getServer(int(self.arguments[0])).addCallbacks(gotData, gotData)

    def editServer(self, ctx, form, data):
        
        def added(_):
            return url.root.child('Thebe').child('Servers')

        return self.enamel.storage.updateServerDetail(
            int(self.arguments[0]), 
            data['name'].encode(),
            data['hostname'].encode(),
            data['key'].encode()
        ).addCallbacks(added,added)

    def locateChild(self, ctx, arguments):
        def serverUrl(_):
            return url.root.child('Thebe').child('Servers')

        if arguments[0] == "Delete":
            return self.enamel.storage.deleteServer(
                int(arguments[1]),
            ).addCallback(serverUrl), ()

        return PageBase.Page.locateChild(self, ctx, arguments)

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3["Edit server"],
            tags.directive('form addServer'),
        ]

class Page(PageBase.Page):
    childPages = {
            'Edit' : Edit
    }

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Thebe Users"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def form_addServer(self, data):
        addServer = form.Form()
        addServer.addField('name', form.String(), label = "Server Name")
        addServer.addField('key', form.String(), label = "License Key", description="Leave blank to generate a new key")
        addServer.addField('hostname', form.String(), label = "Hostname", description="Hostname by which this server can be accessed")
        addServer.addAction(self.addServer)

        return addServer

    def alphaOnly(self, text):
        badChars = "!@#$%^&*()_+-=[];'\\,./{}:\"|<>?`~"
        for i in badChars:
            text = text.replace(i, '')
        text = text.replace(' ', '-')
        return text

    def addServer(self, ctx, form, data):
        name = self.alphaOnly(data['name'].encode())
        if not data['key']:
            l = sha.sha(''.join([chr(ord(i)^random.randint(0, 128)) for i in name])).hexdigest()

            k = "%s-%s-%s-%s" % (l[:4], l[4:8], l[8:12], l[12:16])

            alphabet = [chr(i) for i in range(ord('a'), ord('z')+1)]
            rotAlpha = alphabet[15:] + alphabet[:15]

            rotDict = dict(zip(alphabet, rotAlpha))

            newStr = ""
            for x in k:
                if x in rotDict:
                    newStr += rotDict[x]
                else:
                    newStr += x
            data['key'] = unicode(newStr)


        l = open('/etc/smokeping/config', 'r').read()
        if "++ %s" % name in l:
            print "Already in smokeping.."
        else:
            l = open('/etc/smokeping/config', 'at')
            conf = """\n++ %(n)s
menu = %(n)s
title = %(n)s
host = %(h)s
alerts = bigloss,rttdetect\n\n""" % {'n': name, 'h': data['hostname'].encode()}
            l.write(conf)
            l.close()

        system.system('echo "New server: %s %s %s" | mail -s "New server %s" lis@thusa.co.za' % (
                name,
                data['hostname'].encode(),
                data['key'],
                name
            )
        )

        def returnPage(_):
            return url.root.child('Thebe').child('Servers')

        def addMember(svr):
            return self.enamel.storage.addServerMembership(1, svr[0]).addBoth(returnPage)

        def added(_):
            return self.enamel.storage.getServerByName(name).addBoth(addMember)

        return self.enamel.storage.addServer(
            name,
            data['hostname'].encode(),
            data['key'].encode(),
        ).addCallbacks(added, added)

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_content(self, ctx, data):
        def renderServers(server):
            servers = [(i[1], i[2], i[3], [
                tags.a(href="Edit/%s/" % i[0])["Edit"],
                " ",
                tags.a(href="Edit/Delete/%s/" % i[0])["Delete"]
            ]) for i in server]
            return ctx.tag[
                tags.h3["Server List"],
                self.dataTable(["Name", "Hostname", "Key", ""], servers, sortable=True),
                tags.br,
                tags.h3["Comission new server"],
                tags.directive('form addServer'),
            ]
        if 1==1 or 0 in self.avatarId.gids:
            # Member of the godlike Thusa group!
            return self.enamel.storage. getServers().addCallback(renderServers)
        else:
            return self.enamel.storage. getServersInGroup(self.avatarId.gids).addCallback(renderServers)


