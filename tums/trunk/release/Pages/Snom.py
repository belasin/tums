from nevow import rend, loaders, tags, url, stan, inevow
from Core import confparse, Utils, PBXUtils, PageHelpers
from Pages import Asterisk
import Settings

from random import choice
import string

def GenPasswd():
    chars = string.letters + string.digits
    for i in range(8):
        newpasswd = newpasswd + choice(chars)
    return newpasswd

def GenPasswd2(length=8, chars=string.letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])


snomDevConf = """
subscription_delay: 5
subscription_expiry: 30
advertisement: off

%(fkeys)s

user_name1: %(user)s
user_pass1: %(password)s
user_realname1: %(user_realname)s
user_idle_text1: %(user_idletext)s
user_subscription_expiry1: 30
user_ringer1: Ringer6

update_policy: auto_update
firmware_interval: 24
%(firmwareurl)s
"""

snomGeneralDev = """language: English
time_server: %(myIp)s
ntp_server: %(myIp)s
timezone: CAT+2
tone_scheme: GBR
update_policy: auto_update

active_line: 1
display_method: full_contact 
date_us_format: false
time_24_format: true

advertisement: false

call_completion: false
peer_to_peer_cc: false

challenge_response: false
call_waiting: true
call_join_xfer: false
guess_number: false

admin_mode: true
admin_mode_password: 0000

mwi_dialtone: stutter
mwi_notification: reminder

show_call_status: on

user_host1: %(myIp)s
user_outbound: %(myIp)s 
user_mailbox1: *96
user_ringer1: Ringer6
user_expiry1: 3600

rtp_port_start: 10000
rtp_port_end: 15000

user_phone: false

filter_registrar: false

refer_brackets: false

syslog_server: %(myIp)s 

key_tones: true
intercom_enabled: true

user_name1: guesthandset
user_pass1: guest
user_ringer1: 6

use_backlight: on

dkey_help: keyevent F_HELP
dkey_snom: keyevent F_SNOM
dkey_conf: keyevent F_CONF
dkey_transfer: keyevent F_TRANSFER
dkey_hold: keyevent F_R
dkey_dnd: keyevent F_DND
dkey_record: keyevent F_REC
dkey_retrieve: keyevent F_RETRIEVE
dkey_redial: keyevent F_REDIAL
dkey_directory: keyevent F_ADR_BOOK

gui_fkey1!: F_REGS
gui_fkey2!: F_CALL_LIST
gui_fkey3!: F_ADR_BOOK
gui_fkey4!: F_SPEED_DIAL
dkey_menu!: keyevent F_MENU

"""

class Page(rend.Page):
    """Generates the necessary renders for snom auto config"""

    butMat = { #Buttons memory support 136 buttons
        '360':[[0,6,1,7,2,8,3,9,4,10,5,11]],
        '320':[[6,0,7,1,8,2,9,3,10,4,11,5]],
    }

    firmware = {
        '360': {'6':'snom360-6.5.18-SIP-j.bin'},
        '320': {
            '6': 'snom320-6.5.20-SIP-j.bin',
            '6.5.20': 'snom320-from6to7-7.3.14-bf.bin', #Upgrade 320's from 6 to 7
            '7': 'snom320-7.3.30-SIP-f.bin',
        },
    }

    def __init__(self, db, file = None, *a, **kw):
        self.db = db
        self.file = file
        self.sysconf = confparse.Config()
        rend.Page.__init__(self,*a, **kw)

    def locateChild(self, ctx, segs):
        if segs:
            if segs[0] != 'snom.htm' and segs[0][0:4] != "snom":
                return None, ()
            if len(segs) > 1:
                return None, ()
                
        print segs[0]
        return Page(self.db,segs[0]),()
        #super(Page, self).locateChild(ctx,segs)

    def getPhoneVersion(self, ctx):
        request = inevow.IRequest(ctx)
        agent = request.received_headers.get('user-agent', None)

        aSplit = agent.split()

        type = '320'
        version = ("7","0","0")

        if len(aSplit) > 3:
            if 'snom' in aSplit[2]:
                type = aSplit[2].split('-')[0][4:]
                version = aSplit[3].replace(';','').split('.')
                print "%s %s" %(type, version)


        """Typical Useragent for SNOM
        Mozilla/4.0 (compatible; snom320-SIP 7.3.14 1.1.3-s)
        Mozilla/4.0 (compatible; snom320-SIP 6.5.19; snom320 jffs2 v3.36; snom320 linux 3.38)
        """
        return type, version

    def getPhoneEntry(self, macAddr):
        """Gets the phone dict for the provided macAddr"""
        for user,phoneent in self.sysconf.PBX.get('phones', {}).items():
            phone = phoneent['phone']
            if 'mac' not in phone:
                continue
            if macAddr.upper() == phone['mac'].upper():
                return phoneent

    def genSnomFkeys(self, fkeys, type="360", ext=0):
        """Generates function keys for each user"""
        output = []
        #for k, user in enumerate(fkeys):
        for k, butNum in enumerate(self.butMat[type][ext]):
            buttonText = 'fkey%s'% butNum
            if k < len(fkeys):
                key = fkeys[k]
            else:
                key = None
            dial = ""
            keyDet = PBXUtils.resolveKeyNumber(key)
            butType = "dest"
            pickup = ""
            if keyDet:
                dial = keyDet[0]
                if 'ext/' == key[0:4]:
                    pickup = "|*8"
                    butType = "blf"

            if dial:
                output.append('%s: %s <sip:%s@%s>%s' % (
                    buttonText,
                    butType,
                    dial,
                    self.lanIP,
                    pickup
                ))
            else:
                output.append('%s: ' % buttonText)
        return str.join('\n', output)

    def generateHandsetConfig(self, macAddr):
        """Generates the handset config from the mac address"""
        #snomMAC = self.sysconf.PBX.get('snomMAC', [])
        #if macAddr not in snomMAC:
        #    snomMAC.append(macAddr) #So it shows in the interface
        #    PBX = self.sysconf.PBX
        #    PBX['snomMAC'] = snomMAC
        #    self.sysconf.PBX = PBX
        phoneEnt = self.getPhoneEntry(macAddr)
        
        d = None
        data = {}
        def returnEntry(ret=None):
            print data
            if data:
               return stan.raw(snomDevConf % data)
            return ""



        if not phoneEnt: #Generate a blank Phone entry
            PBX = self.sysconf.PBX
            phones = PBX.get('phones', {})
            cblock = {
                'callerid': macAddr,
                'username': macAddr,
                'fullcallerid': macAddr,
                'phone':{
                    'type': 'Snom ' + self.phoneVer[0],
                    'fkeys': [],
                    'mac': macAddr,
                    'autogen': True, #This was autogenerated
                },
                'secret': GenPasswd2(),
                'outgoinglimit': 1 
            }
            phones[macAddr] = cblock
            PBX['phones'] = phones
            self.sysconf.PBX = PBX
            d = Asterisk.restartAsterisk()
            phoneEnt = self.getPhoneEntry(macAddr)
            print phoneEnt

        if phoneEnt:
            type = phoneEnt['phone']['type'].lower().split()[1]
            ptype = phoneEnt['phone']['type'].lower().split()[0]
            if self.phoneVer[0]:
                type = self.phoneVer[0].lower()

            if ptype == 'snom':
                ext = PBXUtils.getDeviceExtension('Phone/' + phoneEnt['username'])
                callerid = phoneEnt['username'] 
                displayName = phoneEnt['username']
                fkeys = self.genSnomFkeys([], type)
                if ext: #If there is a user extension bound to this phone then we need to work out a few things
                    if ext[1]['enabled']:
                        callerid = ext[1].get('fullcallerID', ext[1].get('callerID','Unknown'))
                        displayName = "%s-%s" % (ext[1].get('callerID','Unknown'), ext[0])
                        if 'fkeys' in ext[1]: #Resolve Function Keys
                            fkeys = self.genSnomFkeys(ext[1]['fkeys'], type)
                fwurl = 'firmware_status: http://%s:9682/snom/snom-firmware.htm' % self.lanIP
                data = {
                    'fkeys': fkeys,
                    'user': phoneEnt['username'],
                    'user_realname': callerid,
                    'user_idletext': displayName,
                    'password': phoneEnt['secret'],
                    'firmwareurl': fwurl,
                }

        if d: #If there is a defer then lets wait for it to end
            return d.addBoth(returnEntry)
        else:
            return returnEntry()

    def render_content(self, ctx, data):
        self.phoneVer = self.getPhoneVersion(ctx)
        try:
            self.lanDev = self.sysconf.LANPrimary[0]
        except:
            self.lanDev = self.sysconf.EthernetDevices.keys()[0]

        self.lanIP = self.sysconf.EthernetDevices[self.lanDev]['ip'].split('/')[0]

        snomGenConf = {
            'myIp': self.lanIP,
        }

        if self.file == 'snom-firmware.htm':
            if self.phoneVer[0]:
                phoneFWs = self.firmware.get(self.phoneVer[0], {})
                firmwareFile = phoneFWs.get(str.join('.',self.phoneVer[1]),
                    phoneFWs.get(self.phoneVer[1][0], "")
                )
                print "Snom of type %s requested firmware for version %s sending %s" % (
                    self.phoneVer[0],
                    str.join('.',self.phoneVer[1]),
                    firmwareFile
                )
                output = "\nfirmware: http://%s:9682/files/snom/%s\n" % (
                    self.lanIP,
                    firmwareFile,
                )

                return output
            else:
                return ""

        if self.file[0:5] == "snom-":
            macAddr = self.file.split('-')[-1].split('.')[0]
            return self.generateHandsetConfig(macAddr)

        if self.file == 'snom.htm':
            return snomGeneralDev % snomGenConf
        else:
            return ""

    docFactory = loaders.stan(
        tags.html[
            tags.pre[
                tags.invisible(render=tags.directive('content'))
            ]
        ]
    )

