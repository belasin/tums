from nevow import rend, loaders, tags, athena, static
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import defer
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings
import email, html5lib, sha, base64, os, traceback, time
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.Utils import COMMASPACE, formatdate

from html5lib import treebuilders
from Core import PageHelpers, AuthApacheProxy, MailClient

from Mail import Calendar

try:
    from twisted.web import http
except ImportError:
    from twisted.protocols import http


# Special file handler
class MailFile(static.File):
    def __init__(self, filename, avatarId, *a, **kw):
        """ This special file handler takes an avatarId, huzza """
        static.File.__init__(self, filename, *a, **kw)
        self.avatarId = avatarId

    def createSimilarFile(self, path):
        f = self.__class__(path, self.avatarId, self.defaultType, self.ignoredExts, self.registry)
        # refactoring by steps, here - constructor should almost certainly take these
        f.processors = self.processors
        f.indexNames = self.indexNames[:]
        return f


    def directoryListing(self):
        return rend.NotFound

    def renderHTTP(self, ctx):
        """You know what you doing. Not particularly..."""

        self.fp.restat()

        if self.type is None:
            self.type, self.encoding = static.getTypeAndEncoding(self.fp.basename(),
                                                          self.contentTypes,
                                                          self.contentEncodings,
                                                          self.defaultType)

        if not self.avatarId.username in self.fp.path:
            return rend.FourOhFour()

        if not self.fp.exists():
            return rend.FourOhFour()

        request = inevow.IRequest(ctx)

        if self.fp.isdir():
            return self.redirect(request)

        # fsize is the full file size
        # size is the length of the part actually transmitted
        fsize = size = self.getFileSize()

        request.setHeader('accept-ranges','bytes')

        if self.type:
            request.setHeader('content-type', self.type)
        if self.encoding:
            request.setHeader('content-encoding', self.encoding)

        try:
            f = self.openForReading()
        except IOError, e:
            import errno
            if e[0] == errno.EACCES:
                return error.ForbiddenResource().render(request)
            else:
                raise

        if request.setLastModified(self.fp.getmtime()) is http.CACHED:
            return ''

        try:
            range = request.getHeader('range')

            if range is not None:
                # This is a request for partial data...
                bytesrange = string.split(range, '=')
                assert bytesrange[0] == 'bytes',\
                       "Syntactically invalid http range header!"
                start, end = string.split(bytesrange[1],'-')
                if start:
                    f.seek(int(start))
                if end:
                    end = int(end)
                else:
                    end = fsize-1
                request.setResponseCode(http.PARTIAL_CONTENT)
                request.setHeader('content-range',"bytes %s-%s/%s" % (
                    str(start), str(end), str(fsize)))
                #content-length should be the actual size of the stuff we're
                #sending, not the full size of the on-server entity.
                size = 1 + end - int(start)

            request.setHeader('content-length', str(size))
        except:
            traceback.print_exc(file=log.logfile)

        if request.method == 'HEAD':
            return ''

        # Strip our UUID from the filename and reset the content disposition header
        name = self.fp.path.split('/')[-1]
        realName = name.split('-', 1)[-1]
        request.setHeader('content-disposition', 'attachment; filename="%s"' % realName)

        # return data
        static.FileTransfer(f, size, request)
        # and make sure the connection doesn't get closed
        return request.deferred



def mailHeaderDecoder(payload):
    # Sanitise the payload and split it up
    hdrs = payload.replace('\r', '').strip('\n').split('\n')
    hdrs.sort()

    headers = {}

    for h in hdrs:
        # pass rubish lines
        if not ':' in h:    
            continue
        field, data = h.split(':',1)
        field = field.lower().capitalize()

        headers[field] = unicode(data.strip())

    return headers
   

class MailFragment(athena.LiveFragment):
    jsClass = u'mailbox.PS'

    docFactory = loaders.xmlfile('mail-fragment.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, avatarId, imap, *a, **kw):
        super(MailFragment, self).__init__(*a, **kw)
        self.avatarId = avatarId
        self.imap = imap # MailClient.IMAPClient(self.avatarId)

    @athena.expose
    def deleteMail(self, folder, mailList):
        print "Deleting", mailList
        def gotFolder(_):
            def final(a):
                print a
                self.imap.disconnect()
                return 

            dl = [self.imap.delete(mail) for mail in mailList]

            return defer.DeferredList(dl).addBoth(final)
        return self.imap.connect().addBoth(lambda _ :self.imap.getFolder(folder).addBoth(gotFolder))

    @athena.expose
    def getMail(self, folder, page):
        def gotFolder(f):
            mailCount = f['EXISTS']

            if mailCount >  25:
                start = mailCount - (page*25)
                if start < 1:
                    start = 1
            else:
                start = 1

            end = mailCount - ((page-1)*25)

            print mailCount, start, page, end
            
            def gotMails(mails):
                res = []
                keys = mails.keys()
                keys.sort()
                for i in reversed(keys):
                    if len(mails[i][0]) < 3:
                        # Weird issue
                        continue
                    payload = mails[i][0][-1]
                    flags = mails[i][0][1]
                    heads = mailHeaderDecoder(payload)

                    if "<" in heads['From']:
                        fromm = unicode(heads['From'].split('<')[0].strip())
                    else:
                        fromm = unicode(heads['From'])
                    
                    date = ' '.join(heads['Date'].split()[1:-1])
                    sub = heads['Subject']

                    read = True
                    
                    if '\\Seen' in flags:
                        read = False
                    
                    res.append([i, fromm, sub, date, read])
                self.imap.disconnect()
                return mailCount, res

            def noMails(_):
                print "No Mail"
                self.imap.disconnect()
                return [0, []]

            return self.imap.getMail(
                start, 
                end, 
                headerType='HEADER.FIELDS',
                headerArgs=['FROM', 'SUBJECT', 'DATE']
            ).addCallbacks(gotMails, noMails)

        return self.imap.connect().addBoth(lambda _ :self.imap.getFolder(folder).addBoth(gotFolder))

class MailMixin(object):
    def flatDirs(self, d, bigcnt=1, start = True, chain = ""):
        bigcnt *= 10
        if not d:
            return 

        stack = []
        try:
            keys = d.keys()
        except:
            return ""
        keys.sort()
        for k in keys:
            v = d[k]
            bigcnt +=1
            chainc = chain + "." + k

            if k == "INBOX":
                k = "Inbox"
                fclass = "mail-inbox.png"
            elif k.lower() == "sent":
                k = "Sent"
                fclass = "mail-sent.png"
            else:
                fclass = "mail-folder.png"

            node = [tags.a(href="#", _class="treeNode %s" % chainc.strip('.'), id="node_%s"%bigcnt)[k]]

            rec = self.flatDirs(v, bigcnt, False, chainc)
            if rec:
                node.append(rec)

            stack.append(
                tags.li(_class=fclass)[
                    node
                ]
            )
        
        if start:
            return tags.ul(id="tree", _class="ctree")[stack]

        else:
            return tags.ul[stack]

    def render_sideMenu(self, ctx, data):
        def gotFolders(r):
            self.imap.disconnect()
            return ctx.tag[
                tags.div(id="TreeCont")[
                    self.flatDirs(r)
                ]
            ]

        return self.imap.getFolders().addBoth(gotFolders)

    def htmlParse(self, data):
        # quick check
        if not ("body" in data.lower()):
            # wtf?
            return data

        parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))

        minidom = parser.parse(data)

        data = ""

        # Erm, recursive hax for minidom - this is really nasty
        def itrTree(point):
            data = ""
            if "body" in point.nodeName:
                for nd in point.childNodes:
                    data += nd.toxml()
                return data
            else: 
                for c in point.childNodes:
                    dt = itrTree(c)
                    if dt:
                        return dt

        data = itrTree(minidom)

        # Replace cid's from mapper
        print self.contentMapper
        for k,v in self.contentMapper.items():
            print "CID MAPPER", k, v
            data = data.replace('cid:%s' % k, '/mail/mdata/%s/%s' % (self.avatarId.username, v))

        return data

    def getMail(self, folder, mailNum):

        def gotMail(mails):
            mail = email.message_from_string(mails[mailNum][0][4])

            headers = dict(mail._headers)

            uFrom = headers['From']
            uDate = ' '.join(headers['Date'].split()[1:-1])
            uSubject = headers['Subject']

            data = ""
            dtType = ""
            attachments = {} 

            lastWas = ''

            itr = 0 
            for part in mail.walk():
                content = part.get_content_type()
                main, sub = content.split('/')
                print content
                if main == "multipart":
                    continue
                itr += 1

                if (main == 'text') and (itr == 1):
                    # First text part 
                    data = part.get_payload()
                    dtType = sub
                    lastWas = sub
                elif (main=='text') and (lastWas == 'plain'):
                    lastWas = sub
                    data = part.get_payload()
                    dtType = sub

                # Store our mail content somewhere temporarily  # XXX Implement cleaner for attachments
                else:
                    hdr = dict(part._headers)
                    print hdr
                    disp = hdr.get('Content-Disposition')
                    if not disp:
                        # We can't do anything with this part
                        continue 

                    if not 'filename' in disp:
                        # No filename
                        continue

                    filename = ""
                    for ct in disp.replace('\n', '').split(';'):
                        if not "=" in ct:
                            continue 
                        segs = ct.split('=')
                        field = segs[0].strip().lower()
                        val = segs[1].replace('"', '')
                        if field == "filename":
                            filename = val

                    if not filename:
                        continue

                    # Decode binary data
                    binData = base64.b64decode(part.get_payload())
                    # Write a file
                    f = open(self.static + self.avatarId.username +'/' + self.mailUID + '-' + filename, 'wb')
                    f.write(binData)
                    f.close()

                    if hdr.get('Content-ID'):
                        cid = hdr['Content-ID'].lstrip('<').rstrip('>')
                        self.contentMapper[cid] = self.mailUID + '-' + filename
                        print "CID MAPPER CR", cid, self.contentMapper[cid]

                    attachments[filename] = (self.mailUID + '-' + filename, len(binData))

            if dtType == "html":
                data = self.htmlParse(data)
            else:
                data = "<pre>%s</pre>" % data

            self.imap.disconnect()

            return attachments, (uFrom, uDate, uSubject), data

        def gotFolder(_):
            print "GF", _
            return self.imap.getMail(mailNum, mailNum).addBoth(gotMail)

        def getFolder(_):
            print "Connected"
            return self.imap.getFolder(folder).addBoth(gotFolder)

        return self.imap.connect().addBoth(getFolder)

class MailPage(MailMixin, PageHelpers.DefaultAthena):

    docFactory  = loaders.xmlfile('mail.xml', templateDir=Settings.BaseDir+'/templates')

    moduleName = 'mailbox'
    moduleScript = 'mailbox.js'

    def __init__(self, *a, **kw):
        PageHelpers.DefaultAthena.__init__(self, *a, **kw)
        self.imap = MailClient.IMAPClient(self.avatarId)

    def render_thisFragment(self, ctx, data):
        """ Renders MailFragment instance """
        f = MailFragment(self.avatarId, self.imap)
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_content(self, ctx, data):
        toolbar = [
            ("/mail/New/", 'New', "/images/inbox.png", "newmail"),
            ("#", 'Delete', "/images/inbox.png", "deletesel"),
        ]

        return ctx.tag[
            tags.ul(id="mailTools")[
                [
                    tags.li(id=id)[
                        tags.a(href=link)[
                            tags.div[tags.img(src=image)], 
                            name
                        ]
                    ]
                for link, name, image, id in toolbar]
            ],
            tags.invisible(render=tags.directive('thisFragment'))
        ]

class ComposeFragment(athena.LiveFragment, MailMixin):
    jsClass = u'mailbox.PS'

    docFactory = loaders.xmlfile('compose-fragment.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, avatarId, imap, *a, **kw):
        super(ComposeFragment, self).__init__(*a, **kw)
        self.avatarId = avatarId
        self.imap = imap
        self.static = '/usr/local/tcs/tums/Mail/StaticTemp/'
        self.contentMapper = {}
        self.attachments = {}
        self.mailUID = sha.sha("%s%s" % (time.ctime(), self.avatarId.username)).hexdigest()

    @athena.expose
    def getUsername(self):
        return unicode(self.avatarId.username)

    @athena.expose
    def updateAttachments(self, locname, orig):
        self.attachments[orig] = (locname, )

    @athena.expose
    def sendMail(self, rcpt, subject, text):
        send_from = "%s@%s" % (self.avatarId.username, self.avatarId.dom)

        send_to = []
        rcpt.replace(';', ',')
        for r in rcpt.split(','):
            n = r.strip()
            if '@' in n:
                send_to.append(n)

        msg = MIMEMultipart()
        msg['From'] = send_from
        msg['To'] = COMMASPACE.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        # Figure out our multi-part id's 

        idmapper = {}
        isinline = []
        cnt = 0 
        for filename, real in self.attachments.items():
            cnt += 1
            
            # RFC 2111 wins the retard prize!
            id = "%s@%s" % (sha.sha(str(cnt) + real[0]).hexdigest(), self.avatarId.dom)
            
            idmapper[filename] = id
            mpath = '/mail/mdata/%s/%s' % (self.avatarId.username, real[0])
            if mpath in text:
                isinline.append(filename)
                text = text.replace(mpath, 'cid:%s' % id)

        msg.attach(MIMEText("""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html><head></head><body>
%s
</body></html>""" % text, 'html'))

        for filename, real in self.attachments.items():
            f = self.static + self.avatarId.username +'/' + real[0]
            
            if filename in isinline:
                part = MIMEImage(open(f,"rb").read())
            else:
                part = MIMEBase('application', "octet-stream")

                part.set_payload( open(f,"rb").read() )
                email.Encoders.encode_base64(part)
            
            part.add_header('Content-ID', '<%s>' % idmapper[filename])
            if filename in isinline:
                part.add_header('Content-Disposition', 'inline; filename="%s"' % filename)
            else:
                part.add_header('Content-Disposition', 'attachment; filename="%s"' % filename)
                
            msg.attach(part)

        from twisted.mail import smtp

        def finished(_):
            print "Mail sent", _
            return True

        # Clean realFrom
        if "<" in send_from:
            realFrom = send_from.split('<')[-1].split('>')[0]
        else:
            realFrom = send_from

        return smtp.sendmail('127.0.0.1', realFrom, [send_to], msg.as_string()).addBoth(finished)

    @athena.expose
    def getIMail(self, path):

        mail = path.split('.')[-1]
        folder = '.'.join(path.split('.')[:-1])

        def handleMail(data):
            fr, date, sub = data[1]
            self.attachments = data[0]
            
            mcont = """<br/>
            <p>On %s, %s wrote:</p>
            <blockquote style="border-left: 2px solid #1010ff; padding-left: 5px; margin-left: 5px; width: 100%%;">
                %s
            </blockquote>
            """ % ( 
                date, 
                fr.replace('<', '&lt;').replace('>', '&gt;'),
                data[-1]
            )

            if "re:" not in sub.lower()[:3]:
                sub = "Re: %s" % sub
            return unicode(sub), unicode(mcont)

        return self.getMail(folder, int(mail)).addBoth(handleMail)

class ComposeMail(MailMixin, PageHelpers.DefaultAthena):
    docFactory  = loaders.xmlfile('mail-compose.xml', templateDir=Settings.BaseDir+'/templates')

    moduleName = 'mailbox'
    moduleScript = 'mail-compose.js'

    def __init__(self, avatarId, db, *a, **kw):
        PageHelpers.DefaultAthena.__init__(self, avatarId, db, *a, **kw)
        self.imap = MailClient.IMAPClient(self.avatarId)

    def render_thisFragment(self, ctx, data):
        """ Renders MailFragment instance """
        f = ComposeFragment(self.avatarId, self.imap)
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_hashkey(self, ctx, data):
        return ctx.tag[
            tags.input(id="hashKey", name="hashKey", type="hidden", value="%s%s" % (int(time.time()), self.avatarId.username))
        ]

    def render_content(self, ctx, data):
        toolbar = [
            ("#", 'Send', "/images/inbox.png", "sendBtn")
        ]

        return ctx.tag[
            tags.ul(id="mailTools")[
                [
                    tags.li[
                        tags.a(id=id, href=link)[
                            tags.div[tags.img(src=image)], 
                            name
                        ]
                    ]
                for link, name, image,id in toolbar]
            ],
            tags.invisible(render=tags.directive('thisFragment'))
        ]

class ViewMail(MailMixin, PageHelpers.DefaultPage):
    docFactory  = loaders.xmlfile('mail-view.xml', templateDir=Settings.BaseDir+'/templates')

    def __init__(self, avatarId, db, params=[], *a, **kw):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **kw)
        self.imap = MailClient.IMAPClient(self.avatarId)
        self.params = params
        self.static = '/usr/local/tcs/tums/Mail/StaticTemp/'
        self.contentMapper = {}
        if params:
            self.mailUID = sha.sha("%s%s%s" % (self.params[0], self.params[1], self.avatarId.username)).hexdigest()

    def render_content(self, ctx, data):
        mailNum = int(self.params[1])
        folder = self.params[0]

        def gotMail(mail):
            print mail
            attachments, hdrs, data = mail
            uFrom, uDate, uSubject = hdrs

            toolbar = [
                ("/mail/Mail/##%s" % self.params[0], 'Inbox', "/images/inbox.png"), 
                ("/mail/New/##%s.%s" % self.params, 'Reply', "/images/inbox.png")
            ]

            return ctx.tag[
                tags.div(id="mailViewHolder")[
                    tags.ul(id="mailTools")[
                        [
                            tags.li[
                                tags.a(href=link)[
                                    tags.div[tags.img(src=image)], 
                                    name
                                ]
                            ]
                        for link, name, image in toolbar]
                    ],
                    tags.table(id="mailViewHeaders")[
                        tags.tr[tags.td["From:"], tags.td[uFrom]],
                        tags.tr[tags.td["Date:"], tags.td[uDate]],
                        tags.tr[tags.td["Subject:"], tags.td[uSubject]],
                        tags.tr[tags.td["Attachments:"], tags.td[
                            [[
                                tags.a(href="/mail/mdata/%s/%s" % (self.avatarId.username, v[0]))[
                                    tags.img(src="/images/attachment.png"), " ", 
                                    k
                                ], " (%0.2f KB)" % (v[1]/1024.0), tags.br
                            ]
                            for k,v in attachments.items()]
                        ]],
                    ],
                    tags.div(id="mailViewContentBox")[
                        tags.xml(data)
                    ], 
                ]
            ]

        def next(_):
            self.imap.disconnect()
            return self.getMail(folder, mailNum).addBoth(gotMail)

        def gotFolder(_):
            return self.imap.markRead(mailNum).addBoth(next)

        def getFolder(_):
            return self.imap.getFolder(folder).addBoth(gotFolder)

        return self.imap.connect().addBoth(getFolder)



    def locateChild(self, ctx, segs):
        if len(segs) > 2:
            return ViewMail(self.avatarId, self.db, segs[:-1]), ()

        return PageHelpers.DefaultPage.locateChild(self, ctx, segs)

class StoreFile(PageHelpers.DefaultPage):
    def renderHTTP(self, ctx):
        basedir = '/usr/local/tcs/tums/Mail/StaticTemp/' + self.avatarId.username + '/'

        req = inevow.IRequest(ctx)
        data = req.fields['fileFile']

        if "\\" in data.filename:
            filename = data.filename.split('\\')[-1]
        else:
            filename = data.filename

        hashkey = req.args['hashKey'][0]

        filetype = filename.split('.')[-1].lower()

        if int(req.getAllHeaders()['content-length']) > 20000000:
            return '<p id="rcode">File too large</p>'

        f = open(os.path.join(basedir, hashkey+filename), 'wt')
        for i in data.file:
            f.write(i)
        f.close()

        return '<p id="rcode">Complete</p>'

class Page(PageHelpers.DefaultPage):
    childPages = {
        'Mail': MailPage, 
        'View': ViewMail, 
        'New': ComposeMail, 
        'Calendar': Calendar.Page, 
        'storeFile' : StoreFile
    }

    #docFactory  = loaders.xmlfile('default-mail.xml', templateDir=Settings.BaseDir+'/templates')


    def __init__(self, avatarId, *a, **kw):
        PageHelpers.DefaultPage.__init__(self, avatarId, *a, **kw)
        self.child_mdata = MailFile('/usr/local/tcs/tums/Mail/StaticTemp/', avatarId)
        self.child_cke = static.File('/usr/local/tcs/tums/lib/ckeditor')

    def childFactory(self, ctx, seg):
        if seg in self.childPages.keys():
            return self.childPages[seg](self.avatarId, self.db)

        return PageHelpers.DefaultPage.childFactory(self, ctx, seg)

    def render_head(self, ctx, data):
        # Clear out the users temporary crap
        if os.path.exists('/usr/local/tcs/tums/Mail/StaticTemp/%s' % self.avatarId.username):   
            for f in os.listdir('/usr/local/tcs/tums/Mail/StaticTemp/%s' % self.avatarId.username): 
                os.remove('/usr/local/tcs/tums/Mail/StaticTemp/%s/%s' % (self.avatarId.username, f))
        else:
            os.mkdir('/usr/local/tcs/tums/Mail/StaticTemp/%s' % self.avatarId.username)

        return ctx.tag[
            tags.xml('<meta http-equiv="refresh" content="0;url=/mail/Mail/"/>')
        ]

    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.title["Vulani"],
                tags.invisible(render=tags.directive('head'))
            ],
        ]
    )

