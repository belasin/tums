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

        os.system('mkdir -p /etc/dansguardian/lists/')

        filterSets = {
            'porn':"""
.Include</etc/dansguardian/lists/phraselists/pornography/weighted>
.Include</etc/dansguardian/lists/phraselists/pornography/weighted_danish>
.Include</etc/dansguardian/lists/phraselists/pornography/weighted_dutch>
.Include</etc/dansguardian/lists/phraselists/pornography/weighted_french>
.Include</etc/dansguardian/lists/phraselists/pornography/weighted_german>
.Include</etc/dansguardian/lists/phraselists/pornography/weighted_italian>
.Include</etc/dansguardian/lists/phraselists/pornography/weighted_portuguese>
.Include</etc/dansguardian/lists/phraselists/pornography/weighted_spanish> 
.Include</etc/dansguardian/lists/phraselists/nudism/weighted>
""",
            'profanity':"""
.Include</etc/dansguardian/lists/phraselists/badwords/weighted_dutch>
.Include</etc/dansguardian/lists/phraselists/badwords/weighted_french>
.Include</etc/dansguardian/lists/phraselists/badwords/weighted_german>
.Include</etc/dansguardian/lists/phraselists/badwords/weighted_portuguese>
.Include</etc/dansguardian/lists/phraselists/badwords/weighted_spanish> 
""",
            'drugs':"""
.Include</etc/dansguardian/lists/phraselists/drugadvocacy/weighted>
.Include</etc/dansguardian/lists/phraselists/illegaldrugs/weighted>
""",
            'hate':"""
.Include</etc/dansguardian/lists/phraselists/intolerance/weighted>
.Include</etc/dansguardian/lists/phraselists/gore/weighted>
.Include</etc/dansguardian/lists/phraselists/violence/weighted>
.Include</etc/dansguardian/lists/phraselists/weapons/weighted>
""",
            'gambling':"""
.Include</etc/dansguardian/lists/phraselists/gambling/weighted>
""",
            'hacking':"""
.Include</etc/dansguardian/lists/phraselists/warezhacking/weighted>
""",
            'p2p':"""
.Include</etc/dansguardian/lists/phraselists/peer2peer/weighted>
""",
            'webmail':"""
.Include</etc/dansguardian/lists/phraselists/webmail/weighted>
""",
            'chat':"""
.Include</etc/dansguardian/lists/phraselists/chat/weighted>
""",
            'news':"""
.Include</etc/dansguardian/lists/phraselists/news/weighted>
""",
            'dating':"""
.Include</etc/dansguardian/lists/phraselists/personals/weighted>
""",
            'sport':"""
.Include</etc/dansguardian/lists/phraselists/sport/weighted>
""",
            'games':"""
.Include</etc/dansguardian/lists/phraselists/games/weighted>
"""
        }
    
        
        weightFilter = """# Vulani weightedphraselist
#Good Phrases (to allow medical, education, news and other good sites)
.Include</etc/dansguardian/lists/phraselists/goodphrases/weighted_general>
.Include</etc/dansguardian/lists/phraselists/goodphrases/weighted_news>
.Include</etc/dansguardian/lists/phraselists/goodphrases/weighted_general_danish>
.Include</etc/dansguardian/lists/phraselists/goodphrases/weighted_general_portuguese>
"""
    
        for item in config.ProxyConfig.get('blockedcontent', []):
            weightFilter += filterSets[item]

        phraseList = config.ProxyConfig.get('blockedcontent', [])

        bannedPhrase = "# Banned phrases list\n"
        
        if "porn" in phraseList:
            bannedPhrase += ".Include</etc/dansguardian/lists/phraselists/pornography/banned>\n"
        if "drugs" in phraseList:
            bannedPhrase += ".Include</etc/dansguardian/lists/phraselists/illegaldrugs/banned>\n"
        if "gambling" in phraseList:
            bannedPhrase += ".Include</etc/dansguardian/lists/phraselists/gambling/banned>\n"

        l = open('/etc/dansguardian/lists/bannedphraselist', 'wt')
        l.write(bannedPhrase)
        l.close()

        l = open('/etc/dansguardian/lists/weightedphraselist', 'wt')
        l.write(weightFilter)
        l.close()

        # Create exceptions for TUMS proxying
        l = open('/etc/dansguardian/lists/exceptionurllist', 'wt')
        l.write('# URL Exceptions \n\n127.0.0.1:9682/updates/\n')
        for i in config.ProxyConfig.get('cfilterurlwhitelist', []):
            l.write(i+'\n')
        l.close()

        # Create exceptions for IP 
        l = open('/etc/dansguardian/lists/exceptioniplist', 'wt')
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

        messages = """# Vulani messages file in UK English

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
"403","Weighted phrase limit exceeded."

"500","Banned site: "
"501","Banned URL: "
"502","Blanket Block is active and that site is not on the white or grey list."
"503","Banned Regular Expression URL: "
"504","Banned Regular Expression URL found."
"505","Blanket IP Block is active and that address is an IP only address."
"506","Blanket SSL Block is active and that site is not on the white or grey list."
"507","Blanket SSL IP Block is active and that address is an IP only address."
"508","Banned Regular Expression HTTP header: ",
"509","Banned Regular Expression HTTP header found."

"600","Exception client IP match."
"601","Exception client user match."
"602","Exception site match."
"603","Exception URL match."
"604","Exception phrase found: "
"605","Combination exception phrase found: "
"606","Bypass URL exception."
"607","Bypass cookie exception."
"608","Scan bypass URL exception."
"609","Exception regular expression URL match: "

"700","Web upload is banned."
"701","Web upload limit exceeded."

"750","Blanket file download is active and this MIME type is not on the white list: "
"751","Blanket file download is active and this file is not matched by the white lists."

"800","Banned MIME Type: "

"900","Banned extension: "

"1000","PICS labeling level exceeded on the above site."

"1100","Virus or bad content detected."
"1101","Advert blocked"

"1200","Please wait - downloading file for scanning..."
"1201","Warning: file too large to scan. If you suspect that this file is larger than "
"1202",", then refresh this page to download directly."

"1210","Download Complete. Starting scan..."

"1220","Scan complete.</p><p>Click here to download: "
"1221","Download complete; file not scanned.</p><p>Click here to download: "
"1222","File too large to cache.</p><p>Click here to re-download, bypassing scan: "

"1230","File no longer available"
"""
    
        l = open('/etc/dansguardian/languages/ukenglish/messages', 'wt')
        l.write(messages)
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
custombannedimagefile = '/usr/share/dansguardian/transparent1x1.gif'
filtergroups = 1
filtergroupslist = '/etc/dansguardian/lists/filtergroupslist'
bannediplist = '/etc/dansguardian/lists/bannediplist'
exceptioniplist = '/etc/dansguardian/lists/exceptioniplist'
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

maxcontentramcachescansize = 2000
maxcontentfilecachescansize = 20000
scancleancache = on
logclienthostnames = off
filecachedir = '/tmp'
deletedownloadedtempfiles = on
initialtrickledelay = 20
trickledelay = 10
downloadmanager = '/etc/dansguardian/downloadmanagers/fancy.conf'
downloadmanager = '/etc/dansguardian/downloadmanagers/default.conf'
contentscannertimeout = 60
contentscanexceptions = off
recheckreplacedurls = off
logchildprocesshandling = off
maxips = 0
ipipcfilename = '/tmp/.dguardianipipc'
logadblocks = off
loguseragent = off
mailer = '/usr/sbin/sendmail -t'
"""
    
        l = open('/etc/dansguardian/dansguardian.conf', 'wt')
        l.write(dansconfig)
        l.close()

        # Set group policy 
        dansgroup = """# Vulani DansGuardian filter group config file for version 2.9
groupmode = 1
bannedphraselist = '/etc/dansguardian/lists/bannedphraselist'
weightedphraselist = '/etc/dansguardian/lists/weightedphraselist'
exceptionphraselist = '/etc/dansguardian/lists/exceptionphraselist'
bannedsitelist = '/etc/dansguardian/lists/bannedsitelist'
greysitelist = '/etc/dansguardian/lists/greysitelist'
exceptionsitelist = '/etc/dansguardian/lists/exceptionsitelist'
bannedurllist = '/etc/dansguardian/lists/bannedurllist'
greyurllist = '/etc/dansguardian/lists/greyurllist'
exceptionurllist = '/etc/dansguardian/lists/exceptionurllist'
exceptionregexpurllist = '/etc/dansguardian/lists/exceptionregexpurllist'
bannedregexpurllist = '/etc/dansguardian/lists/bannedregexpurllist'
picsfile = '/etc/dansguardian/lists/pics'
contentregexplist = '/etc/dansguardian/lists/contentregexplist'
urlregexplist = '/etc/dansguardian/lists/urlregexplist'
blockdownloads = off
exceptionextensionlist = '/etc/dansguardian/lists/exceptionextensionlist'
exceptionmimetypelist = '/etc/dansguardian/lists/exceptionmimetypelist'
bannedextensionlist = '/etc/dansguardian/lists/bannedextensionlist'
bannedmimetypelist = '/etc/dansguardian/lists/bannedmimetypelist'
exceptionfilesitelist = '/etc/dansguardian/lists/exceptionfilesitelist'
exceptionfileurllist = '/etc/dansguardian/lists/exceptionfileurllist'
headerregexplist = '/etc/dansguardian/lists/headerregexplist'
bannedregexpheaderlist = '/etc/dansguardian/lists/bannedregexpheaderlist'
naughtynesslimit = 100
categorydisplaythreshold = 0
embeddedurlweight = 0
enablepics = off
bypass = 0
bypasskey = ''
infectionbypass = 0
infectionbypasskey = ''
infectionbypasserrorsonly = on
disablecontentscan = off
deepurlanalysis = on
usesmtp = off
mailfrom = ''
avadmin = ''
contentadmin = ''
avsubject = 'dansguardian virus block'
contentsubject = 'dansguardian violation'
notifyav = off
notifycontent = off
thresholdbyuser = off
violations = 0
threshold = 0
"""
        l = open('/etc/dansguardian/dansguardianf1.conf', 'wt')
        l.write(dansgroup)
        l.close()

        #Undo insane security - Might implement this later in life...
        fgconfig = "#Banned extension list\n"
        l = open('/etc/dansguardian/lists/bannedextensionlist', 'wt')
        l.write(fgconfig)
        l.close()

        fgconfig = "#Banned MIME types\n"
        l = open('/etc/dansguardian/lists/bannedmimetypelist', 'wt')
        l.write(fgconfig)
        l.close()

        fgconfig = "#URLs in banned list\n"
        l = open('/etc/dansguardian/lists/bannedurllist', 'wt')
        l.write(fgconfig)
        l.close()

        fgconfig = "#Banned sites/domains\n"
        l = open('/etc/dansguardian/lists/bannedsitelist', 'wt')
        l.write(fgconfig)
        l.close()
