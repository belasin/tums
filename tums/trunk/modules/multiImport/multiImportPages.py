"""
Vulani Fetchmail plugin
Copyright (c) 2009, Thusa Business Support (Pty) Ltd.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Thusa Business Support (Pty) Ltd. nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY Thusa Business Support (Pty) Ltd. ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Thusa Business Support (Pty) Ltd. BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import Settings, LDAP, formal, ldap, os, random, sha, copy
from Core import PageHelpers, Utils

from nevow import tags, rend, loaders, url
from twisted.python import log

from Pages.Users import Add, Edit, Base
import re

class aliasImporter(PageHelpers.ToolsPage):
    """Facilitates the import of user aliases file directly into vulani"""

    cleanupData = re.compile("""[#*]+.*|\s""", re.I) #Strip comments and space chars

    ldap = None

    def form_importAliases(self, data):
        """Form presented to the users"""

        form = formal.Form(self.submitForm)
        form.addField('domain', formal.String(required=True, strip=True), label = "Domain for Addresses")
        form.addField('createUser', formal.Boolean(), label = "Create User(s)", description = "You may find that you need to create a holding user account for the forwards to be set up, checking this will create user accounts when they do not exist, mail will not be stored locally and passwords will be randomised")
        form.addField('upload', formal.File(), label = "Upload file")
        form.addAction(self.submitForm)#Set the method to handle the submit action
        return form

    def submitForm(self, ctx, form, data):
        """Submit callback hook"""
        def buildAliasMap(fdata):
            """Builds a usable map of forwards and aliases"""
            mapsOutput = {}
            for line in fdata.readlines():
                line = line.strip()
                if ':' in line:
                    line = self.cleanupData.sub("", line)
                    if len(line) > 0:
                        #Something is left so lets see what we can do
                        source, dest = line.split(":")
                        destList = dest.split(",")
                        if '@' in source: #Invalid entry
                            continue
                        for dest in destList:
                            if not '@' in dest:
                                dest += "@"+data['domain']
                            if source not in mapsOutput:
                                mapsOutput[source] = []
                            mapsOutput[source].append(dest)
            return mapsOutput

        banUsers = ["root", "administrator", "nobody", "ftp"] #List of users we should rather ignore

        fdata = data['upload'][1]
        forwardMaps = buildAliasMap(fdata)

        adder = Add.addPage(self.avatarId, self.db, data['domain'].encode())
        adder.domain = data['domain'].encode()
        
        userAddQueue = self.createUsersQueue(adder,ctx)
        
        for user in forwardMaps:
            if len(forwardMaps[user]) > 10:
                print "ERRRR: NO NO NO don't create an alias to anything more than 10 users use a mailing list skipping", user
                continue
            if user not in banUsers:
                self.setUser(ctx, userAddQueue, user, data["domain"], forwardMaps[user], data["createUser"])
        if self.ldap:
            self.ldap.unbind_s()
            self.ldap = None

        userAddQueue.runQueue()

        return url.root.child('aliasImporter')

    def setUser(self, ctx, userAddQueue, username, domain, forwardList, createUser=False):
        if not self.ldap:
            self.ldap = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "%s,%s,o=%s" % (Settings.LDAPPeople, LDAP.domainToDC(domain), Settings.LDAPBase)
        userData = LDAP.getUsers(self.ldap, dc, 'uid='+username)
        if userData:
            print "User %s exists updating" % username
            oldData = copy.deepcopy(userData[0])
            if "mailForwardingAddress" in userData[0]:
                for forwardAddress in forwardList:
                    if not forwardAddress in userData[0]["mailForwardingAddress"]:
                        if len(userData[0]["mailForwardingAddress"]) >= 10:
                            continue
                        userData[0]["mailForwardingAddress"].append(forwardAddress)
            else :
                userData[0]["mailForwardingAddress"] = forwardList
            try:
                LDAP.modifyElement(self.ldap, 'uid='+username+','+dc, oldData, userData[0])
            except:
                print "Failed to import ", username
        else:
            if not createUser:
                return
            submitData = {
                    'userSettings.uid': unicode(username),
                    'userPermissions.employeeType': False,
                    'userPermissions.tumsUser': None,
                    'userSettings.userPassword': "a%sa100" % username,
                    'mailSettings.vacation': None,
                    'userPermissions.tumsAdmin': False,
                    'userPermissions.accountStatus': True,
                    'userSettings.sn': unicode(username),
                    'userSettings.givenName': unicode(username),
                    'userAccess.ftpEnabled': None,
                    'userAccess.ftpGlobal': None,
                    'userAccess.vpnEnabled': None,
                    'userPermissions.copyto': None
            }
            #print "Adding User", username
            for i in range(10):
                try:
                    addr = unicode(forwardList[i])
                except:
                    addr = u""

                submitData['mailSettings.mailAlternateAddress%s' % i] = addr

                submitData['mailSettings.mailForwardingAddress%s' % i] = u""

            #print submitData

            #res = self.adder.submitForm(ctx, None, submitData)
            userAddQueue.add(submitData)

            #def spam(_):
            #    print _
            #    print '/'.join([i for i in url.URLOverlaySerializer(_, ctx).next()])

            #try:
            #    res.addBoth(spam)
            #except:
            #    pass


            #print res

    class createUsersQueue(object):
        domain = None

        dataQueue = []

        ctx = None

        currentIndex = 0

        maxDefers = 50

        adder = None

        def __init__(self, adder, ctx):
            self.ctx = ctx
            self.adder = adder

        def add(self, submitData):
            if len(self.dataQueue) < self.currentIndex+1:
                print "Indexing to ",self.currentIndex
                self.dataQueue.append([])
            
            if len(self.dataQueue[self.currentIndex]) >= self.maxDefers:
                self.currentIndex += 1
                self.add(submitData)
                return
            self.dataQueue[self.currentIndex].append(submitData)

        def runQueue(self):
            def nextChain(res):
                if len(self.dataQueue[self.currentIndex]) > 0:
                    submitData = self.dataQueue[self.currentIndex].pop()
                    #self.adder.domain = domain.encode()
                    print "Adding User ",submitData['userSettings.uid']
                    res = self.adder.submitForm(self.ctx, None, submitData)
                    res.addBoth(nextChain)
                    return res
                else:
                    if self.currentIndex > 0:
                        self.currentIndex -= 1
                        nextChain(None)
            nextChain(None)

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3["Aliases Import"],
            tags.directive('form importAliases'),
            tags.div(id="helpimport")[
                tags.p["""
                    This page allows you to upload a linux alias file in it's standard format
                    each of the aliases will result in the updating of the currently set aliases for each of the users
                    and potentially creating new users when they do not exist
                    """,
                    tags.br
                ]
            ]
        ]

