from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, LDAP, formal, ldap, os, random, sha
from Core import PageHelpers, Utils, confparse, WebUtils
import copy, time
from Pages import VPN # Import the VPN module for making certs

from Pages.Users import Add, Edit, Group, Delete, Base

alpha = "LLPETUMS"

class bulkUsers(Base.Page):
    def form_addForm(self, data):
        form = formal.Form(self.submitForm)
        
        form.addField('upload', formal.File(), formal.FileUploadWidget, label = "Upload file")

        form.addAction(self.submitForm)

        return form

    def submitForm(self, ctx, form, data):
        adder = Add.addPage(self.avatarId,self.db, Settings.defaultDomain)
        editor = Edit.editPage(self.avatarId, self.db, Settings.defaultDomain) 
        deleter = Delete.deletePage(self.avatarId, self.db)
        groupSwitcher = Group.editGroups(self.avatarId, self.db)

        print data['upload']
        # My crufty CSV parser.
        type, fdata,name = data['upload']
        sepchar = None
        logs = []
        lineno = 0
        for l in fdata:
            lineno+= 1
            # Clean it up
            l = l.strip('\n').strip()
            # continue if we don't have anything left
            if not l:
                continue

            # Figure out the separation character, we accept a few to play nice
            if not sepchar:
                sepChars = [",",";",":","\t"]
                sepcnt, char = (0, None)
                # Find the most occurances
                for i in sepChars:
                    if l.count(i) > sepcnt:
                        char = i
                sepchar = char
                print "Using sepchar ", repr(sepchar)

            prefields = l.split(sepchar)
            # Clean the fields
            # [type, uid, name, surname, password, perm1, perm2, groups ->]
            fields = ["A", "", "", "", "", "", ""]
            off = 0 
            for i,n in enumerate(prefields):
                st = n.strip(' ').strip("'").strip('"')
                if i == 0:
                    if st not in ["A", "U", "D"]:
                        off += 1
                if len(fields) > (i+off):
                    fields[i+off] = st
                else:
                    if st:
                        fields.append(st)
            action = fields[0]
            email = fields[5].lower()
            web = fields[6].lower()
            groups = fields[7:]
            groups.append('Domain Users')
            if email in ["yes", "true", "1"]:
                email = True
            else:
                email = False

            if web in ["yes", "true", "1"]:
                web = True
            else:
                web = False
            
            submitData = {
                'userSettings.uid': unicode(fields[1].split('@')[0]),
                'userPermissions.employeeType': web, 
                'userPermissions.tumsUser': None,
                'userSettings.userPassword': fields[4] or "%s100" % fields[2], 
                'mailSettings.vacation': None,
                'userPermissions.tumsAdmin': False,
                'userPermissions.accountStatus': email,
                'userSettings.sn': unicode(fields[3]), 
                'userSettings.givenName': unicode(fields[2]),
                'userAccess.ftpEnabled': None,
                'userAccess.ftpGlobal': None,
                'userAccess.vpnEnabled': None,
                'userPermissions.copyto': None
            }
            for i in range(10):
                submitData['mailSettings.mailAlternateAddress%s' % i] = u""
                submitData['mailSettings.mailForwardingAddress%s' % i] = u""

            # Figure out the domain
            if '@' in fields[1]:
                domain = fields[1].split('@')[-1]
            else:
                domain = Settings.defaultDomain
        
            print action, domain, submitData['userSettings.uid'], groups
            if action == "A" or action == "U":
                if action == "A":
                    adder.domain = domain
                    adder.submitForm(ctx, None, submitData)
                if action == "U":
                    try:
                        editor.domain = domain
                        editor.cid = submitData['userSettings.uid'].encode()
                        editor.submitForm(ctx, None, submitData)
                    except:
                        logs.append("Unable to modify '%s' on line %s. Check that the user exists" % (
                            submitData['userSettings.uid'].encode(), lineno)
                        )
                        continue

                # If it's actualy a Samba domain..
                if domain == Settings.defaultDomain:
                    try:
                        # Assemble a mapping with spaces stripped 
                        groupDict = {}
                        for i in groups:
                            groupDict[i.replace(' ', '')] = True
                        groupSwitcher.domain = domain
                        groupSwitcher.cid = submitData['userSettings.uid'].encode()
                        # Update the permissions
                        groupSwitcher.submitForm(ctx, None, groupDict)
                    except:
                        logs.append("Unable to modify memberships for '%s' on line %s. Check that the user exists" % (
                            submitData['userSettings.uid'].encode(), lineno)
                        )
                        continue

            elif action == "D":
                deleter.locateChild(ctx, [domain, submitData['userSettings.uid']])
            else:
                logs.append("Unable to understand command '%s' on line %s" % (action, lineno))

        print logs
        return url.root.child('Users')

    def render_editContent(self, ctx, data):
        return ctx.tag[
            tags.h3["Bulk edit"],
            tags.directive('form addForm'),
            tags.div(id="helpbulk")[
                tags.p["""
                    This page allows you to upload a CSV file with bulk editing commands. 
                    To create a bulk editing file please follow this column format.
                    The first column must have one of A, D or U to show Add, Delete or Update. The username should follow this
                    then first name, last name, password, email permission (blank for none), browsing permission, and then group memberships should follow.
                    """,
                    tags.br,tags.br,
                    "For example:",tags.br,
                    tags.pre[
                        "A, steven.jones, Steven, Jones, sjones3, yes, , Staff, Accounting\n",
                        "U, bobb.stevens, Bobb, Stevens, bobbcat, yes, yes, Staff, HR\n"
                    ],
                    tags.br,
                    "This will create the user steve.jones with the Staff and Accounting groups, "
                    " the password 'sjones3', and give him email access. It will then update",
                    " bobb.stevens to match the given permissions, password and groups. Spaces near",
                    " commas will be removed as well as quotations, and TUMS will attempt to match various positive",
                    " responses for the boolean permissions ('1', 'true' or 'yes').",
                    " For deletion only the user name is required and any other columns will be ignored.",
                    tags.br,
                    "If the first column does not contain any of A, D or U then a new user will be assumed.",
                    " If the columns end after the surname then the default permissions will be assumed.",
                    " If the password column is not present it will be set to the first name with '100' appended",
                    " for example 'Steven100'.",
                ]
            ]
        ]


