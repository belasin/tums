import config, os
from Core import Utils

class Plugin(object):
    """ Configures everything needed for Debian RADIUS. """
    parameterHook = "--cfilter"
    parameterDescription = "Reconfigure content filtering"
    parameterArgs = ""
    autoRun = True
    required = "debian"
    configFiles = [ 
        "/etc/dansguardian/dansguardian.conf",
    ]

    def reloadServices(self):
        os.system('/etc/init.d/dansguardian restart')

    def writeConfig(self, *a):
        if config.ProxyConfig.get('contentfilter', None):
            os.system('update-rc.d dansguardian start 89 2 3 4 5 . stop 19 0 1 6 .')
        else:
            # Dansguardian is not enabled!
            os.system('update-rc.d -f dansguardian remove')
            return 

        if not os.path.exists('/etc/dansguardian'): 
            print "ERROR: Dansguardian is not installed!"
            return 

        filterSets = {
            'porn':"""
.Include</etc/dansguardian/phraselists/pornography/weighted>
.Include</etc/dansguardian/phraselists/pornography/weighted_danish>
.Include</etc/dansguardian/phraselists/pornography/weighted_dutch>
.Include</etc/dansguardian/phraselists/pornography/weighted_french>
.Include</etc/dansguardian/phraselists/pornography/weighted_german>
.Include</etc/dansguardian/phraselists/pornography/weighted_italian>
.Include</etc/dansguardian/phraselists/pornography/weighted_portuguese>
.Include</etc/dansguardian/phraselists/pornography/weighted_spanish> 
.Include</etc/dansguardian/phraselists/nudism/weighted>
""",
            'profanity':"""
.Include</etc/dansguardian/phraselists/badwords/weighted_dutch>
.Include</etc/dansguardian/phraselists/badwords/weighted_french>
.Include</etc/dansguardian/phraselists/badwords/weighted_german>
.Include</etc/dansguardian/phraselists/badwords/weighted_portuguese>
.Include</etc/dansguardian/phraselists/badwords/weighted_spanish> 
""",
            'drugs':"""
.Include</etc/dansguardian/phraselists/drugadvocacy/weighted>
.Include</etc/dansguardian/phraselists/illegaldrugs/weighted>
""",
            'hate':"""
.Include</etc/dansguardian/phraselists/intolerance/weighted>
.Include</etc/dansguardian/phraselists/gore/weighted>
.Include</etc/dansguardian/phraselists/violence/weighted>
.Include</etc/dansguardian/phraselists/weapons/weighted>
""",
            'gambling':"""
.Include</etc/dansguardian/phraselists/gambling/weighted>
""",
            'hacking':"""
.Include</etc/dansguardian/phraselists/warezhacking/weighted>
""",
            'p2p':"""
.Include</etc/dansguardian/phraselists/peer2peer/weighted>
""",
            'webmail':"""
.Include</etc/dansguardian/phraselists/webmail/weighted>
""",
            'chat':"""
.Include</etc/dansguardian/phraselists/chat/weighted>
""",
            'news':"""
.Include</etc/dansguardian/phraselists/news/weighted>
""",
            'dating':"""
.Include</etc/dansguardian/phraselists/personals/weighted>
""",
            'sport':"""
.Include</etc/dansguardian/phraselists/sport/weighted>
""",
            'games':"""
.Include</etc/dansguardian/phraselists/games/weighted>
"""
        }
    
        
        weightFilter = """# Vulani weightedphraselist
#Good Phrases (to allow medical, education, news and other good sites)
.Include</etc/dansguardian/phraselists/goodphrases/weighted_general>
.Include</etc/dansguardian/phraselists/goodphrases/weighted_news>
.Include</etc/dansguardian/phraselists/goodphrases/weighted_general_danish>
.Include</etc/dansguardian/phraselists/goodphrases/weighted_general_portuguese>
"""
    
        for item in config.ProxyConfig.get('blockedcontent', []):
            weightFilter += filterSets[item]

        phraseList = config.ProxyConfig.get('blockedcontent', [])

        bannedPhrase = "# Banned phrases list\n"
        
        if "porn" in phraseList:
            bannedPhrase += ".Include</etc/dansguardian/phraselists/pornography/banned>\n"
        if "drugs" in phraseList:
            bannedPhrase += ".Include</etc/dansguardian/phraselists/illegaldrugs/banned>\n"
        if "gambling" in phraseList:
            bannedPhrase += ".Include</etc/dansguardian/phraselists/gambling/banned>\n"

        l = open('/etc/dansguardian/bannedphraselist', 'wt')
        l.write(bannedPhrase)
        l.close()

        l = open('/etc/dansguardian/weightedphraselist', 'wt')
        l.write(weightFilter)
        l.close()

        # Create exceptions for TUMS proxying
        l = open('/etc/dansguardian/exceptionurllist', 'wt')
        l.write('# URL Exceptions \n\n127.0.0.1:9682/updates/\n')
        for i in config.ProxyConfig.get('cfilterurlwhitelist', []):
            l.write(i+'\n')
        l.close()

        # Create exceptions for IP 
        l = open('/etc/dansguardian/exceptioniplist', 'wt')
        l.write('# IP Exceptions \n\n127.0.0.1\n')
        for i in config.ProxyConfig.get('cfilterhostwhitelist', []):
            l.write(i+'\n')
        l.close()

        blockTemplate = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Vulani Proxy Error: Access Denied</title>
  </head>
  <body>
    <table width="100%" height="100%"><tr height="100%"><td>
      <div id="centerBox" valign="middle">
        <div id="blockTop"></div>
          <div id="menuBlock">
            <h2>Access Denied</h2>
            <p>Content filtered as harmful (<a href="-URL-">-URL-</a>): -REASONGIVEN-. Please contact your support representative for more information.</p>
          </div>
        </div>
      </td></tr>
    </table>
  </body>
</html>\n"""
        l = open('/etc/dansguardian/languages/ukenglish/template.html', 'wt')
        l.write(blockTemplate)
        l.close()

        messages = """
"1","Access Denied"

"100","Your IP address is not allowed to web browse: "
"101","Your IP address is not allowed to web browse."
"102","Your username is not allowed to web browse: "
"200","The requested URL is malformed."
"300","Banned Phrase found: "
"301","Banned phrase found."
"400","Banned combination phrase found: "
"401","Banned combination phrase found."
"402","Weighted phrase limit of "
"403","Too many bad phrases."
"500","Banned site: "
"501","Banned URL: "
"502","Blanket Block is active and that site is not on the white or grey list."
"503","Banned Regular Expression URL: "
"504","Banned Regular Expression URL found."
"505","Blanket IP Block is active and that address is an IP only address."
"600","Exception client IP match."
"601","Exception client user match."
"602","Exception site match."
"603","Exception URL match."
"604","Exception phrase found: "
"605","Combination exception phrase found: "
"606","Bypass URL exception."
"607","Bypass cookie exception."
"700","Web upload is banned."
"701","Web upload limit exceeded."
"800","Banned MIME Type: "
"900","Banned extension: "
"1000","PICS labeling level exceeded on the above site."
"1100","Virus infected content found."
"""
    
        l = open('/etc/dansguardian/languages/ukenglish/messages', 'wt')
        l.write(blockTemplate)
        l.close()

        dansconfig = """# Dansguardian config for Vulani 
reportinglevel = 3
languagedir = '/etc/dansguardian/languages'
language = 'ukenglish'
loglevel = 3
logexceptionhits = on
logfileformat = 1
filterip = 127.0.0.1
filterport = 8081
proxyip = 127.0.0.1
proxyport = 8080
accessdeniedaddress = 'http://YOURSERVER.YOURDOMAIN/cgi-bin/dansguardian.pl'
nonstandarddelimiter = on
usecustombannedimage = 1
custombannedimagefile = '/etc/dansguardian/transparent1x1.gif'
filtergroups = 1
filtergroupslist = '/etc/dansguardian/filtergroupslist'
bannediplist = '/etc/dansguardian/bannediplist'
exceptioniplist = '/etc/dansguardian/exceptioniplist'
banneduserlist = '/etc/dansguardian/banneduserlist'
exceptionuserlist = '/etc/dansguardian/exceptionuserlist'
showweightedfound = on
weightedphrasemode = 2
urlcachenumber = 3000
urlcacheage = 900
phrasefiltermode = 2
preservecase = 0
hexdecodecontent = 0
forcequicksearch = 0
reverseaddresslookups = off
reverseclientiplookups = off
createlistcachefiles = on
maxuploadsize = -1
maxcontentfiltersize = 256
usernameidmethodproxyauth = on
usernameidmethodntlm = off # **NOT IMPLEMENTED**
usernameidmethodident = off
preemptivebanning = on
forwardedfor = on
usexforwardedfor = on
logconnectionhandlingerrors = on
maxchildren = 120
minchildren = 8
minsparechildren = 4
preforkchildren = 6
maxsparechildren = 32
maxagechildren = 500
ipcfilename = '/tmp/.dguardianipc'
urlipcfilename = '/tmp/.dguardianurlipc'
nodaemon = off
nologger = off
softrestart = off
virusscan = on
virusengine = 'clamav'
tricklelength = 32768
forkscanlength = 32768
firsttrickledelay = 10
followingtrickledelay = 10
maxcontentscansize = 41904304
virusscanexceptions = on
urlcachecleanonly = on
virusscannertimeout = 60
notify = 0
emaildomain = 'your.domain.com'
postmaster = 'postmaster@your.domain.com'
emailserver = '127.0.0.1:25'
downloaddir = '/tmp/dgvirus'
clmaxfiles = 1500
clmaxreclevel = 3
clmaxfilesize = 10485760
clblockencryptedarchives = off
cldetectbroken = off
clamdsocket = '/tmp/clamd'
avesocket = '/var/run/aveserver'
trophiesocket = '/var/run/trophie'
sophiesocket = '/var/run/sophie'
icapsocket = 'localhost:1344'
icapservice = 'icap://localhost/avscan'
"""
    
        l = open('/etc/dansguardian/dansguardian.conf', 'wt')
        l.write(dansconfig)
        l.close()

        # Set group policy 
        dansgroup = """# DansGuardian filter group config file for version 2.8.0

# Content filtering files location
bannedphraselist = '/etc/dansguardian/bannedphraselist'
weightedphraselist = '/etc/dansguardian/weightedphraselist'
exceptionphraselist = '/etc/dansguardian/exceptionphraselist'
bannedsitelist = '/etc/dansguardian/bannedsitelist'
greysitelist = '/etc/dansguardian/greysitelist'
exceptionsitelist = '/etc/dansguardian/exceptionsitelist'
bannedurllist = '/etc/dansguardian/bannedurllist'
greyurllist = '/etc/dansguardian/greyurllist'
exceptionurllist = '/etc/dansguardian/exceptionurllist'
bannedregexpurllist = '/etc/dansguardian/bannedregexpurllist'
bannedextensionlist = '/etc/dansguardian/bannedextensionlist'
bannedmimetypelist = '/etc/dansguardian/bannedmimetypelist'
picsfile = '/etc/dansguardian/pics'
contentregexplist = '/etc/dansguardian/contentregexplist'

naughtynesslimit = 100

bypass = 0

bypasskey = ''

virusscan = on

exceptionvirusextensionlist = '/etc/dansguardian/exceptionvirusextensionlist'
exceptionvirusmimetypelist = '/etc/dansguardian/exceptionvirusmimetypelist'
exceptionvirussitelist = '/etc/dansguardian/exceptionvirussitelist'
exceptionvirusurllist = '/etc/dansguardian/exceptionvirusurllist'
dlmgrextensionlist = '/etc/dansguardian/dlmgrextensionlist'
"""
        l = open('/etc/dansguardian/dansguardianf1.conf', 'wt')
        l.write(dansgroup)
        l.close()

        #Undo insane security - Might implement this later in life...
        fgconfig = "#Banned extension list\n"
        l = open('/etc/dansguardian/bannedextensionlist', 'wt')
        l.write(fgconfig)
        l.close()

        fgconfig = "#Banned MIME types\n"
        l = open('/etc/dansguardian/bannedmimetypelist', 'wt')
        l.write(fgconfig)
        l.close()

        fgconfig = "#URLs in banned list\n"
        l = open('/etc/dansguardian/bannedurllist', 'wt')
        l.write(fgconfig)
        l.close()

        fgconfig = "#Banned sites/domains\n"
        l = open('/etc/dansguardian/bannedsitelist', 'wt')
        l.write(fgconfig)
        l.close()
