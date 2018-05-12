from nevow import rend, loaders, tags, athena, context, flat
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, log
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
from zope.interface import implements
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import time
import base64

def sendMail(send_from, send_to, subject, text, files=[], server="127.0.0.1", html=False, importance = None):
    """Sends an email"""
    assert type(send_to)==list
    assert type(files)==list

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    if importance:
        msg['Importance'] = importance

    if html:
        msg.attach(MIMEText(text, 'html'))
    else:
        msg.attach(MIMEText(text))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
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
    return smtp.sendmail(server, realFrom, [send_to], msg.as_string())
    #.addCallbacks(finished, finished)

def progressBar(percent):
    length = 200.0
    percentText = "%s%%" % int(percent*100)
    return tags.div(style='border:1px solid black; width: %spx; height:16px;' % (length+2))[
        tags.div(style='float:left; margin-left: %spx;' % int((length/2)-15))[percentText],

        tags.div(style='margin-top:1px; margin-left:1px; width:%spx; height:14px; background: #EC9600;' % int(length*percent))[''],
    ]

def TabSwitcher(tabs):
    tabNames = [i for j,i in tabs]
    tabLables = [i for i,j in tabs]

    closeTabs = ';\n'.join(["    hideElement('%s'); getElement('tab%s').style.color='#666666';" % (i,i) for i in tabNames])

    switchFunc = """
        tabSwitcher = function (tab) {
            %s
            getElement('tab'+tab).style.color='#E710D8';
            showElement(tab);
            createCookie('tabOpen', tab);
        };
    """ % closeTabs

    return [
        tags.xml("""<script type="text/javascript">
        function createCookie(name,value) {
            var date = new Date();
            date.setTime(date.getTime()+(24*60*60*1000));
            var expires = "; expires="+date.toGMTString();
            document.cookie = name+"="+value+expires+"; path=/";
        }

        function readCookie(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }

        createTabSwitcher = function() {
            %s

            var firstTab = '%s';
            showElement(firstTab);
            getElement('tab'+firstTab).style.color='#E710D8';
            try {
                var tab = readCookie('tabOpen');
                if (tab) {
                    %s
                    showElement(tab);
                    getElement('tab'+tab).style.color='#E710D8';
                }
            } catch(dontCare){
                showElement(firstTab);
                getElement('tab'+ firstTab).style.color='#E710D8';
            }
        };
        %s
        </script>""" % (closeTabs, tabNames[0], closeTabs, switchFunc)),
        tags.br, tags.br,
        tags.table(cellspacing=0, cellpadding=0, _class="tabSwitcher")[
            tags.tr[
                [
                tags.td(_class = "tabTab", onclick = "tabSwitcher('%s');" % j)[
                        tags.img(src='/images/lefttab.png', align="absmiddle"),
                        tags.a(
                            id="tab"+j,
                            href="#",
                            _class="tabSwitcherTabLink",
                            style="color:#666666; text-decoration:none;",
                            title="Switch to the tab: %s" % i
                        )[tags.strong[i]],
                        tags.img(src='/images/righttab.png', align="absmiddle")
                    ]
                for i,j in tabs]
            ]
        ]
    ]

def LoadTabSwitcher():
    return tags.script(type="text/javascript")["createTabSwitcher();"]

def dataTable(headings, content):
    return tags.table(cellspacing=0,  _class='listing')[
        tags.thead(background="/images/gradMB.png")[
            tags.tr[
                [ tags.th[i] for i in headings ]
            ]
        ],
        tags.tbody[
            [
                tags.tr[ [tags.td[col] for col in row] ]
            for row in content],
        ]
    ]


