from enamel import authentication, deployment, pages, servers, storage, deferreds, tags, url
from enamel import sql, form
import enamel, sha

from custom import Widgets
from twisted.internet import utils, defer

from lib import PageBase

class Page(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('account.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def form_editUser(self, data):
        def gotUser(res):
            editUsers = form.Form()
            editUsers.addField('fullname', form.String(), label = "Name")
            editUsers.addField('company', form.String(), label = "Company")
            editUsers.addField('email', form.String(), label = "EMail")

            editUsers.addField('phone', form.String(), label = "Phone number")
            editUsers.addField('address0', form.String(), label = "Address")
            editUsers.addField('address1', form.String(), label = "Address")
            editUsers.addField('address2', form.String(), label = "Address")
            editUsers.addField('address3', form.String(), label = "Address")

            editUsers.addField('password', form.String(), label = "Password")
            editUsers.addAction(self.editUser)

            editUsers.data = {
                'fullname': res[3],
                'company':  res[5],
                'email':    res[4],
                'phone':    res[10],
                'address0': res[6],
                'address1': res[7],
                'address2': res[8],
                'address3': res[9]
            }

            return editUsers

        if (1 in self.avatarId.gids) and self.arguments:
            return self.enamel.storage.getUser(int(self.arguments[0])).addBoth(gotUser)
            
        return self.enamel.storage.getUser(self.avatarId.uid).addBoth(gotUser)

    def editUser(self, ctx, form, data):
        fullname = (data['fullname'] or u"").encode('ascii')
        company =  (data['company'] or u"").encode('ascii')
        email =    (data['email'] or u"").encode('ascii')
        phone =    (data['phone'] or u"").encode('ascii')
        address0 = (data['address0'] or u"").encode('ascii')
        address1 = (data['address1'] or u"").encode('ascii')
        address2 = (data['address2'] or u"").encode('ascii')
        address3 = (data['address3'] or u"").encode('ascii')

        password = (data['password'] or u"").encode('ascii')

        def goBack(_):
            if (1 in self.avatarId.gids) and self.arguments:
                return url.root.child('Thebe').child('Users')
            return url.root.child('Dashboard')

        
        if (1 in self.avatarId.gids) and self.arguments:
            uid = int(self.arguments[0])
        else:
            uid = self.avatarId.uid

        return self.enamel.storage.editUser(
            uid,
            fullname,
            company, 
            email,
            phone,
            address0,
            address1,
            address2,
            address3,
            password
        ).addCallbacks(goBack, goBack)


    def render_userForm(self, ctx, data):
        return ctx.tag[
            tags.directive('form editUser')
        ]

