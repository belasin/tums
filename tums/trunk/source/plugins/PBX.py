import config, os
import platform
from Core import PBXUtils, Utils
from datetime import datetime

class Plugin(object):
    parameterHook = "--pbx"
    parameterDescription = "Reconfigure PBX"
    parameterArgs = ""
    autoRun = False 

    dowSet = ['mon','tue','wed','thu','fri','sat','sun']

    monSet = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']

    region = 'za'

    configFiles = [
        #"/etc/asterisk/agents.conf", #not going to be used until later
        "/etc/asterisk/asterisk.conf",
        "/etc/asterisk/cdr.conf",
        "/etc/asterisk/cdr_custom.conf",
        "/etc/asterisk/codecs.conf",
        "/etc/asterisk/extensions.ael",
        "/etc/asterisk/features.conf",
        "/etc/asterisk/iax.conf",
        "/etc/asterisk/indications.conf",
        "/etc/asterisk/manager.conf",
        "/etc/asterisk/modules.conf",
        "/etc/asterisk/musiconhold.conf",
        "/etc/asterisk/queues.conf",
        "/etc/asterisk/sip.conf",
        "/etc/asterisk/sip_notify.conf",
        "/etc/asterisk/voicemail.conf",
        "/etc/asterisk/zapata.conf",
        "/etc/default/asterisk"]

    codecs = [['disallow',['all']],['allow',['ulaw','alaw','gsm','ilbc','g729']]]

    configContent = { 
    'asterisk':"""
        [global]
        astetcdir => /etc/asterisk
        astmoddir => /usr/lib/asterisk/modules
        astvarlibdir => /var/lib/asterisk
        astagidir => /usr/share/asterisk/agi-bin
        astspooldir => /var/spool/asterisk
        astrundir => /var/run/asterisk
        astlogdir => /var/log/asterisk
    """,
    'cdr':"""
        [general]
        enable=yes
    """,
    'cdr_custom':"""
        [mappings]
Master.csv => "${CDR(clid)}","${CDR(src)}","${CDR(dst)}","${CDR(dcontext)}","${CDR(channel)}","${CDR(dstchannel)}","${CDR(lastapp)}","${CDR(lastdata)}","${CDR(start)}","${CDR(answer)}","${CDR(end)}","${CDR(duration)}","${CDR(billsec)}","${CDR(disposition)}","${CDR(amaflags)}","${CDR(accountcode)}","${CDR(uniqueid)}","${CDR(userfield)}"
    """,
    'cdr_mysql':"""
        [global]
        hostname=localhost
        dbname=asteriskcdr
        password=asteriskcdr
        user=asteriskcdr
        userfield=1
    """,
    'codecs':"""
        [speex]
        quality => 3
        complexity => 2
        enhancement => true
        vad => true
        vbr => true
        abr => 0
        vbr_quality => 4
        dtx => false
        preprocess => false
        pp_vad => false
        pp_agc => false
        pp_agc_level => 8000
        pp_denoise => false
        pp_dereverb => false
        pp_dereverb_decay => 0.4
        pp_dereverb_level => 0.3

        [plc]
        genericplc => true
    """,
    'debDefault':"""
        RUNASTERISK=yes
        AST_REALTIME=yes
        #RUNASTSAFE=yes
        #ASTSAFE_CONSOLE=yes
        #ASTSAFE_TTY=9
        MAXFILES=16384
    """,
    'extensions':"""
        globals {
            GLOBALTIMEOUT=%(timeout)s;
            GLOBALQTIMEOUT=%(qtimeout)s;
        };
        //Vulani Configuration
        #include "/etc/asterisk/extensions/*.ael"
        #include "/etc/asterisk/extensions/macros/*.ael"
        #include "/etc/asterisk/extensions/routing/*.ael"
    """,
    'extensions_macro':"""
        //User Standard Extension Macro
        macro std-exten( ext , dev, user, monitor, timeout, fwdVoicemail, fwdOther) {
               if("${timeout}" = "") {
                   timeout=${GLOBALTIMEOUT};
               };
               Set(CDR(userfield)=dst\=${user});
               if(${monitor}) {
                   Set(GLOBAL(FROMNUM)=${CALLERID(num)});          
                   Set(RECFILE=inbound/${user}-${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)}-${CALLERID(num)});
                   Monitor(wav,/var/lib/samba/data/vRecordings/tmp_${RECFILE});
                   Set(CDR(userfield)=${CDR(userfield)}\;rec\=${RECFILE});
               };
               SET(GLOBAL(PICKUPMARK)=${ext});
               if ("${RETENTA}" = "") {
                   Noop("A is now set");
                   Set(__RETENTA=${ext});
               } else {
                   if ("${RETENTB}" = "") {
                       Noop("B is now set");
                       Set(__RETENTB=${ext});
                   } else {
                       if ("${RETENTC}" = "") {
                           Noop("C is now set");
                           Set(__RETENTC=${ext});
                       } else {
                           if ("${RETENTD}" = "") {
                               Noop("D is now set");
                               Set(__RETENTD=${ext});
                           };
                       };
                   };
               };
               Dial(${dev},${timeout});
               catch h {
                   if("${monitor}" == "1") {
                       System(/usr/local/tcs/tums/syscripts/mixrecordings.py ${RECFILE});
                   };
                };
               switch(${DIALSTATUS}) {
               case BUSY:
                       if ("${RETENTD}" != "") {
                           Set(BOUNCEB=${RETENTD});
                           Set(__RETENTD="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTC}" != "") {
                           Set(BOUNCEB=${RETENTC});
                           Set(__RETENTC="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTB}" != "") {
                           Set(BOUNCEB=${RETENTB});
                           Set(__RETENTB="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTA}" != "") {
                           Set(BOUNCEB=${RETENTA});
                           Set(__RETENTA="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if("${fwdVoicemail}" != "") {
                           Voicemail(b${ext});
                       } else { 
                           if("${fwdOther}" != "") {
                               Dial(${fwdOther},${timeout});
                           };
                       };
                       break;
               default:
                       if ("${RETENTD}" != "") {
                           Set(BOUNCEB=${RETENTD});
                           Set(__RETENTD="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTC}" != "") {
                           Set(BOUNCEB=${RETENTC});
                           Set(__RETENTC="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTB}" != "") {
                           Set(BOUNCEB=${RETENTB});
                           Set(__RETENTB="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTA}" != "") {
                           Set(BOUNCEB=${RETENTA});
                           Set(__RETENTA="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if("${fwdVoicemail}" != "") {
                           Voicemail(u${ext});
                       } else { 
                           if("${fwdOther}" != "") {
                               Dial(${fwdOther},${timeout});
                           };
                       };
               };
               catch a {
                       if ("${RETENTD}" != "") {
                           Set(BOUNCEB=${RETENTD});
                           Set(__RETENTD="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTC}" != "") {
                           Set(BOUNCEB=${RETENTC});
                           Set(__RETENTC="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTB}" != "") {
                           Set(BOUNCEB=${RETENTB});
                           Set(__RETENTB="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if ("${RETENTA}" != "") {
                           Set(BOUNCEB=${RETENTA});
                           Set(__RETENTA="");
                           if ("${BOUNCEB}" != "${ext}") { Dial(Local/${BOUNCEB}@userExtensions);};
                       };
                       if("${fwdVoicemail}" != "") {
                           Voicemail(${ext});
                       } else { 
                           if("${fwdOther}" != "") {
                               Dial(${fwdOther},${timeout});
                           };
                       };
                       return;
               };
        };
        //User Standard Extension Macro for Queue agents
        macro std-qexten( ext , dev, user, timeout) {
            if("${timeout}" == "") {
                timeout=${GLOBALQTIMEOUT};
            };
 
            Set(CDR(userfield)=dst\=${user};queue\=${QUEUENAME});
            if("${RECFILE}" != "") {
                Set(CDR(userfield)=${CDR(userfield)}\;rec\=${RECFILE});
            };
            SET(GLOBAL(PICKUPMARK)=${ext});
            Dial(${dev},${timeout});
        };

        //Queue Extension
        macro queue-exten(ext, queue, timeout, answer) {
            if("${timeout}" == "") {
                timeout=${GLOBALTIMEOUT};
            };
            Set(__RECFILE=inbound/q${queue}-${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)}-${CALLERID(num)});
            Set(__QUEUENAME=${queue});
            if("${answer}" != "") {
                Answer;
            };
            Monitor(wav,/var/lib/samba/data/vRecordings/tmp_${RECFILE});
            DevState(${ext},2);
            Queue(${queue});
            catch h {
                DevState(${ext},0);
            };
            DevState(${ext},0);
        };
        //Recieve Fax Extension Macro
        macro fax-exten(ext, faxname, email) {
            SET(FAXFILE=/var/lib/samba/data/vFaxing/${CALLERID(NUM)}-${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)});
            Set(CDR(userfield)=faxfile\=${FAXFILE});
            DevState(${ext},2);
            ReceiveFAX(${FAXFILE}.tif);
            catch h {
                System(/usr/bin/tiff2pdf ${FAXFILE}.tif -o ${FAXFILE}.pdf);
                System(echo "A Fax for you from ${CALLERID(num)} was recevied at ${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)} by the VulaniPBX fax system (${faxname})" | /usr/bin/biabam ${FAXFILE}.pdf -s "VulaniPBX: New Fax" ${email});
                DevState(${ext},0);
            };
            System(/usr/bin/tiff2pdf ${FAXFILE}.tif -o ${FAXFILE}.pdf);
            System(echo "A Fax for you from ${CALLERID(num)} was recevied at ${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)} by the VulaniPBX fax system (${faxname})" | /usr/bin/biabam ${FAXFILE}.pdf -s "VulaniPBX: New Fax" ${email});
            DevState(${ext},0);
        };
        //Router Extension(PinDialing)
        macro route-pin-provider(ext,dev,dev1,dev2,dev3,dev4,dev5,providerName,router,monitor,callerID,timeout) {
            NoOp("Pin Dialing via Provider ${providerName}");
            Answer();
            wait(2);
            if("${AUTHUSER}" == "") {
                AGI(agi://127.0.0.1:4573);
                NoOp(User has authed as ${AUTHUSER});
            };
            Set(CDR(accountcode)=${AUTHUSER});
            if("${AUTHUSER}" != "") {
                if("${timeout}" == "") {
                       timeout=${GLOBALTIMEOUT};
                   };
                   NoOp(Dialing Via Provider ${providerName});
                   Set(CDR(userfield)=dstProv\=${providerName};dstRouter=${router});
                   if(${monitor}) {
                       src=${CDR(accountcode)};
                       if(!${src}) {
                           src=${CALLERID(num)};
                       };
                       Set(RECFILE=outbound/${ext}-${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)}-${src});
                       Monitor(wav,/var/lib/samba/data/vRecordings/tmp_${RECFILE});
                       Set(CDR(userfield)=${CDR(userfield)}\;rec\=${RECFILE});
                   };
                   Set(CDR(provider)=${providerName});
                   Dial(${dev}/${ext},${timeout});
            };
            catch h {
               if("${monitor}" == "1") {
                   System(/usr/local/tcs/tums/syscripts/mixrecordings.py ${RECFILE});
               };
            };
        };
        //Router Extension
        //%(prefix)s${EXTEN%(ltrim)s},%(dev0)s,%(dev1)s,%(dev2)s,%(dev3)s,%(dev4)s,%(dev5)s,%(provider)s,,)
        macro route-provider(ext,dev,dev1,dev2,dev3,dev4,dev5,providerName,router,monitor,callerID,timeout) {
               if("${timeout}" == "") {
                   timeout=${GLOBALTIMEOUT};
               };
               NoOp(Dialing Via Provider ${providerName});
               Set(CDR(userfield)=dstProv\=${providerName};dstRouter=${router});
               if(${monitor}) {
                   src=${CDR(accountcode)};
                   if(!${src}) {
                       src=${CALLERID(num)};
                   };
                   Set(RECFILE=outbound/${ext}-${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)}-${src});
                   Monitor(wav,/var/lib/samba/data/vRecordings/tmp_${RECFILE});
                   Set(CDR(userfield)=${CDR(userfield)}\;rec\=${RECFILE});
               };
               Set(CDR(provider)=${providerName});
               Dial(${dev}/${ext},${timeout});
               catch h {
                   if("${monitor}" == "1") {
                       System(/usr/local/tcs/tums/syscripts/mixrecordings.py ${RECFILE});
                   };
               };
        };
    """,
    'extensions_recorder':"""
        context recorder-menu {
           s => {
              Answer;
              Set(TIMEOUT(digit)=5) ; // Set Digit Timeout to 5 seconds
              Set(TIMEOUT(response)=10);   //Set Response Timeout to 10 seconds
              Playback(custom/recorder-welcome);// Play Asterisk Recorder Welcome.
           enter-number:
              Read(PHRASEID|custom/recorder-enter-recording-number); //Please enter the the prompt number you wish to admimister followed by #    
              Wait(1);
              Playback(custom/recorder-current-recording);
              Wait(1);
              Playback(custom/${PHRASEID});
              Wait(1);
           recorder-menu:
              BackGround(custom/recorder-menu); //Press 1 to Accept, Press 2 to review, Press 3 to re-record
              //ResponseTimeout(3)
              goto s|recorder-menu;
           };
           
           // Recording Accept
           1 => { goto s|enter-number;};

           // recording review
           2 => {Wait(1);Playback(custom/recorder-current-recording);Playback(custom/recordings/${PHRASEID});wait(1);goto s|recorder-menu;};
           
           // re-record
           3 => { Playback(custom/recorder-record-after-beep);
              Wait(1); //give yourself a moment to take a breath and wait for beep
              Record(custom/${PHRASEID}:wav);
              Wait(1);
              Playback(custom/recorder-autoreview);
              Wait(1);                                                                                          
              Playback(custom/${PHRASEID});                                                        
              Wait(1);                                                                                                      
              goto s|recorder-menu;
           };

           t => { hangup;};
           i => { Playback(custom/recorder-invalid-option) ; goto s|1;};
        }; 
    """,
    #XXX XXX XXX
    #Future: Make call parking extensions dynamic
    'features':"""
        [general]
        ;Vulani Configuration
        parkext => 800                  ; What ext. to dial to park
        parkpos => 801-820              ; What extensions to park calls on
        context => features             ; Which context parked calls are in
        parkingtime => 120              ; Number of seconds a call can be parked for 
                                        ; (default is 45 seconds)
        ;transferdigittimeout => 3      ; Number of seconds to wait between digits when transfering a call
        ;courtesytone = beep            ; Sound file to play to the parked caller 
                                        ; when someone dials a parked call
        ;adsipark = yes                 ; if you want ADSI parking announcements
        pickupexten = ******8                ; Configure the pickup extension.  Default is *8

        [featuremap]
        blindxfer => ##
        automon => *9
    """,
    'iax':"""
        [general]
        bandwidth=low
        disallow=lpc10                  ; Icky sound quality...  Mr. Roboto.
        jitterbuffer=yes
        forcejitterbuffer=yes
        ; Register with remote server
        %(registrations)s
        ; QOS flag
        tos=ef
        autokill=yes
        trunktimestamps=yes
        #include peers/iax/*.conf
    """,
    'indications':"""
        [general]
        country=%(region)s              ; default location

        [us]
        description = United States / North America
        ringcadence = 2000,4000
        dial = 350+440
        busy = 480+620/500,0/500
        ring = 440+480/2000,0/4000
        congestion = 480+620/250,0/250
        callwaiting = 440/300,0/10000
        dialrecall = !350+440/100,!0/100,!350+440/100,!0/100,!350+440/100,!0/100,350+440
        record = 1400/500,0/15000
        info = !950/330,!1400/330,!1800/330,0
        stutter = !350+440/100,!0/100,!350+440/100,!0/100,!350+440/100,!0/100,!350+440/100,!0/100,!350+440/100,!0/100,!350+440/100,!0/100,350+440

        [za]
        description = South Africa
        ringcadence = 400,200,400,2000
        dial = 400*33
        ring = 400*33/400,0/200,400*33/400,0/2000
        callwaiting = 400*33/250,0/250,400*33/250,0/250,400*33/250,0/250,400*33/250,0/250
        congestion = 400/250,0/250
        busy = 400/500,0/500
        dialrecall = 350+440
        record = 1400/500,0/10000
        info = 950/330,1400/330,1800/330,0/330
        stutter = !400*33/100,!0/100,!400*33/100,!0/100,!400*33/100,!0/100,!400*33/100,!0/100,!400*33/100,!0/100,!400*33/100,!0/100,400*33
    """,
    'manager':"""
        [general]
        enabled = yes
        port = 5038
        bindaddr = 127.0.0.1
       
        [vulani]
        secret = vulanisecret553
        deny=0.0.0.0/0.0.0.0
        permit=127.0.0.1/255.255.255.0
        read = system,call,log,verbose,command,agent,user
        write = system,call,log,verbose,command,agent,user 
    """,
    'modules':"""
        [modules]
        autoload=yes
        preload => pbx_ael.so
        preload => pbx_lua.so
        preload => pbx_realtime.so
        preload => pbx_config.so
        preload => chan_local.so
        noload => pbx_gtkconsole.so
        noload => pbx_kdeconsole.so
        noload => app_intercom.so
        noload => chan_modem.so
        noload => chan_modem_aopen.so
        noload => chan_modem_bestdata.so
        noload => chan_modem_i4l.so
        noload => chan_capi.so
        load => res_musiconhold.so
        noload => chan_alsa.so
        noload => chan_oss.so
        noload => res_odbc.so
        noload => chan_phone.so
        noload => func_odbc.so
        load => cdr_sqlite.so
        load => cdr_addon_mysql.so
        noload => app_directory_odbc.so
        noload => app_voicemail_odbc.so
        noload => app_voicemail_imap.so
        noload => res_config_odbc.so
        noload => res_config_pgsql.so
        [global]
    """,
    #XXX XXX XXX File will likely be 100% generated
    'musiconhold':"""
        [%(musicclass)s]
        mode=files
        directory=%(holdmusic_dir)s
        random=%(random)s
    """,
    'queues':"""
        [general]
        music = default
        ;announce = queue-markq
        keepstats = yes
        strategy = ringall 
        timeout = 0
        retry = 5
        wrapuptime=0
        maxlen = 0
        announce-frequency = 0
        announce-holdtime = no
        queue-thereare  = queue-thereare                ;       ("There are")
        queue-youarenext = queue-youarenext
        queue-callswaiting = queue-callswaiting ;       ("calls waiting.")
        queue-holdtime = queue-holdtime         ;       ("The current est. holdtime is")
        queue-minutes = queue-minutes                   ;       ("minutes.")
        ;queue-seconds = queue-seconds                  ;       ("seconds.")
        queue-thankyou = queue-thankyou         ;       ("Thank you for your patience.")
        queue-lessthan = queue-less-than                ;       ("less than")
        leavewhenempty = yes
        eventwhencalled = yes
        monitor-format = wav49
        monitor-type = Monitor

        %(queues)s
    """,
    'meetme':"""
        [general]
        audiobuffers=32
        [rooms]
        %(meetme)s
    """,
    'sip':"""
        [general]
        context=%(context)s
        realm=%(domain)s
        useragent=VulaniPBX
        port=5060
        bindaddr=0.0.0.0
        srvlookup=no
        pedantic=yes
        maxexpirey=3600
        defaultexpirey=120
        videosupport=yes
        notifyhold=yes
        allowsubscribe=yes
        limitonpeers=yes
        %(codec)s
        musicclass=default
        tos_audio=ef
        tos_sip=cs3
        tos_video=af41

        %(registrations)s
        
        #include peers/sip/*.conf
    """,
    'sip_notify':"""
        [polycom-check-cfg]
        Event=>check-sync
        Content-Length=>0

        [sipura-check-cfg]
        Event=>resync
        Content-Length=>0

        [grandstream-check-cfg]
        Event=>sys-control

        [cisco-check-cfg]
        Event=>check-sync
        Content-Length=>0

        [reboot-snom]
        Event=>check-sync
        Content-Length=>0

        [snom-check-cfg]
        Event=>check-sync\;reboot=false
        Content-Length=>0
    """,
    'voicemail':"""
        [general]
        format=wav49
        serveremail=%(email)s
        attach=yes
        skipms=3000
        maxsilence=5
        silencethreshold=128
        maxlogins=6
        sendvoicemail=yes
        searchcontexts=yes
        [default]
        %(mailbox)s
    """,
    'zapata':"""
        [channels]
        #include peers/zap/*.conf
    """ }

    def reloadServices(self):
        """Reload asterisk depending on what has been altered, if hardware requires a full restart then do so
           so we will need to check the PBXHardware plugin to see if there is a requirement for a full restart"""
        pass

    def __init__(self):
        """Check if we have all the files required before we update the config"""
        if PBXUtils.enabled(): #Please leave this in here and enable at own risk
            self.iaxRegistrations = []
            if os.path.exists('/etc/asterisk/peers') and os.path.exists('/etc/asterisk/extensions') and os.path.exists('/etc/asterisk/VULANI'):
                pass
            else:
                self.prepareAsterisk()

    def writeConfig(self, *a):
        """Write the configuration files"""

        if PBXUtils.enabled():
            # Write PBX Hardware
            self.PBXHardware = PBXUtils.PBXHardware()
            self.PBXHardware.save()

            # Do incremental configs first
            self.writeProviders()

            # write the static files
            self.writeStatics()
            
            # Write Sip Config
            self.writeSipConf()
           
            # Write IAX Config
            self.writeIaxConf()
            
            # Write Indications
            self.writeIndications()

            # Write HoldMusic
            self.writeMusicOnHold()

            # Write Queues
            self.writeQueues()

            # Write MeetMe
            self.writeMeetMe()
            
            # Write Binding Extensions
            self.writeExtensions()
            
            # Write Voicemail Settings
            self.writeVoiceMail()

            # Write the Pin Authentication file
            self.writePinAuth()

            # Create CDR DB
            self.createCDRDB()

            if config.PBX.get('enablePCodec', False):
                self.installPCodec()

            #Reset permissions
            self.resetPerms()

    def checkFaxingModule(self):
        """Make sure that faxing module exists and is installed to enable faxing"""
        if os.path.exists('/usr/lib/asterisk/modules/app_fax.so'):
            return True
        else:
            print "Faxing module not installed attempting to install"
            os.system('dpkg -i /usr/local/tcs/tums/packages/astFax/asterisk-app-fax_0.0.3_i386.deb')
            os.system('asterisk -rx "module load app_fax" > /dev/null 2> /dev/null')
            return os.path.exists('/usr/lib/asterisk/modules/app_fax.so')

    def writeVoiceMail(self):
        """Generates Voicemail Configfile"""

        voiceMailConfig = []

        for user, extension in config.PBXExtensions.items():
            if extension.get('voiceMail', False):
                name = extension.get('fullcallerID', "")
                if '"' in name:
                    name = name.split('"')[1]
                email = user + '@' + config.Domain
                pin = extension.get('voiceMailPin', '1234')
                ext = extension.get('extensions', None)
                if not ext:
                    continue
                else:
                    ext = ext[0]
                voiceMailConfig.append('%s => %s,%s,%s' % (
                    ext,
                    pin.encode('ascii', 'replace'),
                    name.encode('ascii', 'replace'),
                    email.encode('ascii', 'replace')
                ))
                
        voicemailData = self.configContent['voicemail'] % {
            'email': 'vulani-vmail@' + config.Domain,
            'mailbox': str.join('\n        ', voiceMailConfig),
        }
        self.writeFile('/etc/asterisk/voicemail.conf',voicemailData,';')

    def writePinAuth(self):
        import hashlib
        """Generate the Authentication Database"""
        pinAuth = []
        for user, extension in config.PBXExtensions.items():
            if extension.get('voiceMailPin', False): #Going to hijack the voicemail pin number
                ext = extension.get('extensions', None)
                if not ext:
                    continue
                else:
                    passVal = "%s*%s" % (ext[0],extension["voiceMailPin"])
                    m = hashlib.md5()
                    m.update(passVal)
                    passVal = m.hexdigest()
                    pinAuth.append("        %s:%s" % (user,passVal))

        self.writeFile('/etc/asterisk/pinauth.passwd', "\n".join(pinAuth), ';')

    def writeQueues(self):
        """Generate the queue file"""
        queues = {}
        #Start by collecting setting for the queues
        for queueName, queueData in config.PBX.get('queues', {}).items():
            queues[queueName] = queueData
            queues[queueName]['members'] = []

        #Merge members into the dict entry for each queue
        for user, extension in config.PBXExtensions.items():
            userQueues = extension.get('queues', {})
            if type(userQueues) == list:
                n = {}
                for queue in userQueues:
                    n[queue] = 1
                userQueues = n

            for queue, penalty in userQueues.items():
                penalty = penalty - 1 
                if queue in queues:
                    #queues[queue]['members'].extend([
                    #    PBXUtils.resolveDevice(dev) for dev in extension['devices']
                    #])
                    queues[queue]['members'].append("LOCAL/queue-%s@userExtensions%s" % (user, penalty > 0 and "," + str(penalty) or ""))

        queueComp = ""

        #Loop through the queues and add members
        for queue, qDet in queues.items():
            members = ""
            for member in qDet['members']:
                members = members + """        member => %s\n""" % member
            queueComp = queueComp + """
        [%(name)s]
        strategy=%(strategy)s
        timeout=%(timeout)s
        announce-frequency=%(ann-freq)s
        announce-holdtime=%(ann-holdtime)s
        maxlen=0
        leavewhenempty=yes
        eventwhencalled=yes
        retry=5
        music=default
%(members)s
            """ % {
                'name': queue,
                'strategy': qDet.get('strategy', 'ringall'),
                'timeout': qDet.get('timeout', '0'),
                'ann-freq': qDet['announce'] and '30' or '0',
                'ann-holdtime': qDet['announce'] and 'yes' or 'no',
                'members': members,
            }


        queueData = self.configContent['queues'] % {
            'queues':queueComp
        }

        self.writeFile('/etc/asterisk/queues.conf',queueData,';')

    def writeMeetMe(self):
        pass
        meetmeComp = [] 
        for roomNo, mDet in config.PBX.get('meetme', {}).items():
            cDet = [roomNo]
            if mDet['pin']:
                cDet.append(mDet['pin'])
                if mDet['adminpin']:
                    cDet.append(mDet['adminpin'])
            confDet = str.join(',',cDet)
            meetmeComp.append('conf => %s' % confDet)
        meetmeData = self.configContent['meetme'] % {
            'meetme':str.join('\n        ',meetmeComp)
        }
        self.writeFile('/etc/asterisk/meetme.conf',meetmeData,';')

    def writeExtensions(self):
        #def cmpRoutExp(a,b):
        def compareNumExp(a,b):
            """Compares the number expresion priority and makes certain that when sort is applied that the values are in the correct order Highest value first"""
            #normalise
            try:
                vala = a[4]
            except:
                vala = 0
            if not vala:
                vala = 0
            try:
                valb = b[4]
            except:
                valb = 0
            if not valb:
                valb = 0
            if vala < valb:
                return 1
            if vala == valb:
                return 0
            else:
                return -1

        def clr(val):
            if not val:
                return ""
            else:
                return str(val)


        # Write Router Context
        #Create base routers for providers
        userRouters = {}
        routerContextNames = {}
        providerResolvedDevices = {}
        voipTypeResolve = { 
            'vulani':'IAX2',
            'iax2': 'IAX2',
            'sip': 'SIP',
            'vox': 'SIP',
            'worldchat': 'SIP',
        }
        #Resolve provider routing endpoints
        for providerName, provider in config.PBXProviders.items():
            if provider['type'] != 'hardware':
                ro = voipTypeResolve[provider['type']] + '/' + providerName
                providerResolvedDevices[providerName] = [ro]
                continue
            devDict = PBXUtils.resolveProviderDevice(provider)
            for dev in provider['device']:
                if dev in devDict:
                    if providerName not in providerResolvedDevices:
                        providerResolvedDevices[providerName] = [] 
                    providerResolvedDevices[providerName].append(devDict[dev])

        routerFile = """
            //PBX Router Extension Contexts"""
        for Router, routerConfig in config.PBXRouters.items():
            routerContextNames[Router] = "router-" + Router.replace(' ','_')
            routerContent = {}

            routerConfig.sort(compareNumExp)

            numberExpresion = []

            for num in routerConfig:
                if num[1] not in config.PBXProviders:
                    print "Invalid provider specified in Router Config %s" % str(num)
                    continue
                if num[1] not in providerResolvedDevices:
                    print "No availible resolved devices for provider %s" % num[1]
                    continue

                devs = providerResolvedDevices[num[1]]

                #Pad devs
                for pos in range(len(devs),6):
                    devs.append("")
                macro = "route-provider"
                try:
                    if num[5]:
                        macro = "route-pin-provider"
                except:
                    pass

                content = """&%(macro)s(%(prefix)s${EXTEN%(ltrim)s},%(dev0)s,%(dev1)s,%(dev2)s,%(dev3)s,%(dev4)s,%(dev5)s,%(provider)s,%(router)s,%(monitor)s,,);""" % {
                    'num': clr(num[0]),
                    'prefix': clr(num[2]),
                    'provider': clr(num[1]),
                    'router': Router,
                    'macro': macro,
                    'ltrim': num[3] and ":"+str(clr(num[3])) or "",
                    'dev0': devs[0],
                    'dev1': devs[1],
                    'dev2': devs[2],
                    'dev3': devs[3],
                    'dev4': devs[4],
                    'dev5': devs[5],
                    'monitor': config.PBX.get('recordAll', True) and '1' or '',
                }

                if num[0] not in routerContent:
                    routerContent[num[0]] = []
                    numberExpresion.append(num[0])
                routerContent[num[0]].append(content)
            
            compiledContext = ""
            
            for numExp in numberExpresion:
                expHandlers = routerContent[numExp]
                if len(expHandlers) == 1:
                    compiledContext = compiledContext + """
                %s => %s""" % (numExp, expHandlers[0])
                else:
                    compiledContext = compiledContext + """
                %s => {
                    %s
                };""" % (numExp,str.join('\n                    ',expHandlers))

            routerFile += """
            context %s {
            %s
            };""" % (routerContextNames[Router], compiledContext)


        self.writeFile('/etc/asterisk/extensions/routing/vulaniProviderRouting.ael',routerFile,'//',12)

        # Prepare User Contexts

        userContexts = ""

        contextSets = {}

        for user, userDet in config.PBXExtensions.items():
            userDet['outbound'].sort()
            kn = str.join('-', userDet['outbound'])
            if kn not in contextSets:
                contextSets[kn] = {
                    'context': 'userProv-' + kn,
                    'userList': [user],
                    'includeList': [
                        'userHints',
                        'userExtensions',
                        'systemExtensions',
                        'featureExtensions',
                        'customExtensions',
                    ],
                    'providers': userDet['outbound']
                }
            else:
                contextSets[kn]['userList'].append(user)

        

        # Write User Contexts

        for contextSet, data in contextSets.items():

            includeList = data['includeList']
            for provider in data['providers']:
                if provider in routerContextNames:
                    includeList.append(routerContextNames[provider])

            data['compiledIncludeContexts'] = ""
            for context in includeList:
                data['compiledIncludeContexts'] = data['compiledIncludeContexts'] + '\n                    %s;' % context 

            userContexts = userContexts + """
            context %(context)s {
                includes {
                    %(compiledIncludeContexts)s
                };
            };""" % data

        self.writeFile('/etc/asterisk/extensions/routing/userProviderContexts.ael', userContexts, '//', 12)

        # Write User Extensions

        userHints = ""
        userExtensions = ""

        userExtensionCompiled = ""
        userHintsCompiled = ""

        for user, userExt in config.PBXExtensions.items():
            if not userExt.get('enabled', False):
                continue
            devSet = str.join('&', [ PBXUtils.resolveDevice(dev) for dev in userExt['devices'] ])
            #hintDev = [ PBXUtils.resolveDevice(dev) for dev in userExt['devices'] ][0]
            if not devSet:
                continue
            fwdOther = config.PBX.get('fallThrough','')
            qTimeout = config.PBX.get('qtimeout', config.PBX.get('qtimeout',30))
            timeout = config.PBX.get('timeout', config.PBX.get('timeout',30))
            resNum = PBXUtils.resolveKeyNumber(fwdOther)
            if resNum:
                fwdOther = 'local/' + resNum[0]
            hintDev = devSet
            for extension in userExt['extensions']:
                if extension == userExt['extensions'][0]:
                    hintstr = "hint(%s) " % devSet
                else:
                    hintstr = ""
                userExtensionCompiled = userExtensionCompiled + """
                %(hintstr)s%(exten)s => &std-exten(%(mailboxname)s,%(dev)s,%(user)s,%(monitor)s,%(timeout)s,%(fwdVoiceMail)s,%(fwdOther)s);""" % {
                    'exten': extension,
                    'hintstr': hintstr,
                    'mailboxname': userExt['extensions'][0],
                    'dev': devSet,
                    'fwdVoiceMail': userExt['voiceMail'] and '1' or '',
                    'user': user,
                    'timeout': timeout,
                    'monitor': config.PBX.get('recordAll', True) and '1' or '',
                    'fwdOther': fwdOther,
                }
            userExtensionCompiled = userExtensionCompiled + """
                queue-%(user)s => &std-qexten(%(exten)s,%(dev)s,%(user)s,%(timeout)s);""" % {
                'exten': userExt['extensions'][0],
                'dev': devSet,
                'timeout': qTimeout,
                'user': user
            }
        
        userExtensions = """
            context userExtensions {%s
            };
        """ % userExtensionCompiled


        self.writeFile('/etc/asterisk/extensions/userExtensions.ael', userExtensions, '//', 12)

        #Compile systemExt
        systemExt = []

        ivrExtensions = ""

        for ivrName, ivrDet in config.PBX.get('ivr', {}).items():
            if not ivrDet['prompt']:
                continue
            welcomePlayback = "Playback(%s);"% ivrDet['prompt'][0].split('.')[0]
            prompts = []
            for prompt in ivrDet['prompt'][1:]:
                if prompt:
                    prompts.append(prompt.split('.')[0])
            if prompts:
                optionsPlayback = "Background(" + str.join('&',prompts) + ");"
            else:
                optionsPlayback = ""

            ivrItems = []
            for k,option in enumerate(ivrDet['options']):
                if option:
                    res = PBXUtils.resolveKeyNumber(option)
                    if res:
                        ivrItems.append('%s => Dial(Local/%s@default);' % (k,res[0]))

            timeoutEntry = "goto s|menuOptions;"
            if ivrDet.get('timeout-option',False):
                res = PBXUtils.resolveKeyNumber(ivrDet['timeout-option'])
                if res:
                    timeoutEntry = 'Dial(Local/%s@default);' % res[0]


            ivrCompiled = str.join('\n                ', ivrItems)
            
            for extNum in ivrDet['extensions']:
                systemExt.append('%s => jump s@ivr-%s;' % (extNum, ivrName))

            timedIVR = []
            if ivrDet.get('operating', {'enabled':False})['enabled']:
                tI = ivrDet['operating']
                sTime = tI.get('start-time', False)
                eTime = tI.get('end-time', False)
                dow = tI.get('dow', False)
                incD = tI.get('dates', [])
                excD = tI.get('exc-dates', [])
                res = PBXUtils.resolveKeyNumber(tI.get('action',None))
                if eTime and sTime and dow and res:
                    sTime = str.join(':',sTime.split(':')[0:2])
                    eTime = str.join(':',eTime.split(':')[0:2])
                    for date in incD:
                        if '-' in date:
                            #sDate, eDate = date.split('-')
                            #Todo XXX
                            #timedIVR.append("ifTime(*|*|
                            pass
                        ds = date.split('/')
                        if len(ds) < 2:
                            continue
                        timedIVR.append("ifTime(*|*|%s|%s) { goto s|start; };" % (ds[0], self.monSet[int(ds[1])-1]) )
                    for exDate in excD:
                        ds = exDate.split('/')
                        if len(ds) < 2:
                            continue
                        timedIVR.append("ifTime(*|*|%s|%s) { Dial(Local/%s@default); };" % (ds[0], self.monSet[int(ds[1])-1], res[0]) )
                    for day in dow:
                        timedIVR.append("ifTime(%(sTime)s-%(eTime)s|%(dow)s|*|*) { goto s|start; };" % {
                            'sTime': sTime,
                            'eTime': eTime,
                            'dow': self.dowSet[day],
                        })
                    timedIVR.append("Dial(Local/%s@default);" % res[0])
            
            timedIVRCompiled = str.join('\n                    ', timedIVR)
             
            ivrExtensions += """
            context ivr-%(name)s {
                s => {
                timedIVR:
                    //Process Timed IVR
                    %(timedIVR)s
                start:
                    Answer;
                    Set(TIMEOUT(digit)=5);
                    Set(TIMEOUT(response)=%(timeout)s);
                    %(welcomePlayback)s
                menuOptions:
                    %(optionsPlayback)s
                    WaitExten();
                    %(timeoutEntry)s
                };
                %(ivrContent)s
                t => { hangup;};
                i => { Playback(option-is-invalid) ; goto s|menuOptions;};//This will change if default timeout is specified
            };
            """ % {
                'name': ivrName,
                'timedIVR': timedIVRCompiled and timedIVRCompiled or "NoOp(Timed IVR);",
                'timeout': ivrDet['timeout'],
                'ivrContent': ivrCompiled,
                'optionsPlayback': optionsPlayback,
                'welcomePlayback': welcomePlayback,
                'timeoutEntry': timeoutEntry
            }

        self.writeFile('/etc/asterisk/extensions/ivrContexts.ael', ivrExtensions,'//',12)

        #compiling queues
        for qName, qDet in config.PBX.get('queues', {}).items():
            if 'extensions' not in qDet:
                continue
            hintExt = qDet['extensions'][0]
            for ext in qDet['extensions']:
                systemExt.append("hint(DS/%(hext)s) %(exten)s => &queue-exten(%(hext)s,%(queue-name)s,%(timeout)s,%(answer)s);" % {
                    'queue-name': qName,
                    'exten': ext,
                    'timeout': qDet.get('timeout',30),
                    'answer': qDet.get('answer',True) and "1" or "",
                    'hext': hintExt,
                }) 
        
        if self.checkFaxingModule():
            #Installs Asterisk Faxing
            for fName, fDet in config.PBX.get('faxing', {}).items():
                if 'extensions' not in fDet:
                    continue
                hintExt = fDet['extensions'][0]
                for ext in fDet['extensions']:
                    systemExt.append('hint(DS/%(hext)s) %(exten)s => &fax-exten(%(hext)s,%(fax-name)s,"%(email)s");' % {
                        'fax-name': fName,
                        'exten': ext,
                        'hext': hintExt,
                        'email': fDet['email'].replace(' ',''),
                    })

        for roomNo, mDet in config.PBX.get('meetme', {}).items():
            if 'extensions' not in mDet:
                continue
            for ext in mDet['extensions']:
                systemExt.append('hint(meetme:%(roomno)s) %(exten)s => MeetMe(%(roomno)s,Mpc);' % {
                    'roomno': roomNo,
                    'exten': ext
                })
                   



        systemCompiled = str.join('\n                ',systemExt)
        monitor = config.PBX.get('recordAll', True) and '1' or ''

        # Write System Extensions
        systemExt = """
            context systemExtensions {
                %s
            };
            context featureExtensions {
                includes {
                    features;
                };
                *60 => jump s@recorder-menu; 
                _*61XX => {
                    Answer();
                    Wait(0.5);
                    Record(custom/${EXTEN:3}.gsm);
                    Wait(1);
                    Playback(custom/${EXTEN:3});
                    Hangup; 
                };
                *96 => VoiceMailMain(${CALLERID(num)});
                *8 => {
                    monitor=%s;
                    user=${CDR(accountcode)};
                    Set(CALLERID(num)=${FROMNUM});
                    if(!${user}) {
                        user=${CALLERID(num)};
                    };
                    Set(CDR(userfield)=dst\=${user});
                    if("${monitor}" == "1") {
                        Set(RECFILE=inbound/${user}-${STRFTIME(${EPOCH},,%%Y%%m%%d%%H%%M%%S)}-${CALLERID(num)});
                        Monitor(wav,/var/lib/samba/data/vRecordings/tmp_${RECFILE});
                        Set(CDR(userfield)=${CDR(userfield)}\;rec\=${RECFILE});
                    };
                    Pickup(0);
                    if("${monitor}" == "1") {
                        System(/usr/local/tcs/tums/syscripts/mixrecordings.py ${RECFILE});
                    };
                };
                _*8. => {
                    monitor=%s;
                    user=${CDR(accountcode)};
                    Set(CALLERID(num)=${FROMNUM});
                    if(!${user}) {
                        user=${CALLERID(num)};
                    };
                    Set(CDR(userfield)=dst\=${user});
                    if("${monitor}" == "1") {
                        Set(RECFILE=inbound/${user}-${STRFTIME(${EPOCH},,%%Y%%m%%d%%H%%M%%S)}-${CALLERID(num)});
                        Monitor(wav,/var/lib/samba/data/vRecordings/tmp_${RECFILE});
                        Set(CDR(userfield)=${CDR(userfield)}\;rec\=${RECFILE});
                    };
                    DPickup(${EXTEN:2}@PICKUPMARK);
                    if("${monitor}" == "1") {
                        System(/usr/local/tcs/tums/syscripts/mixrecordings.py ${RECFILE});
                    };
                };
            };
        """ % (systemCompiled, monitor, monitor)
        self.writeFile('/etc/asterisk/extensions/system.ael', systemExt, '//', 12)

        

        incomingContext = """
            context incomming {
                includes {
                    preCustomIncomming;
                    userHints;
                    userExtensions;
                    systemExtensions;
                    postCustomIncomming;
                };
            };

            context default {
                includes {
                    incomming;
                };
            };
        """
        self.writeFile('/etc/asterisk/extensions/incoming.ael', incomingContext, '//',12)

    def resolveUserDevice(self, deviceName):
        for user, userDet in config.PBXExtensions:
            if deviceName in userDet['devices']:
                return (user, userDet)

    def resolveUserContext(self, user):
        if user in config.PBXExtensions:
            userDet = config.PBXExtensions[user]
            userDet['outbound'].sort()
            return 'userProv-'+str.join('-',userDet['outbound'])

    def createCDRDB(self):
        os.system('mysqladmin create asteriskcdr  > /dev/null 2>&1')
        os.system('mysqladmin create asteriskcdr -u root --password=thusa123 > /dev/null 2>&1')
        os.system('mysql asteriskcdr < /usr/local/tcs/tums/packages/asteriskCDR.sql > /dev/null 2>&1')
        os.system('mysql asteriskcdr -u root --password=thusa123 < /usr/local/tcs/tums/packages/asteriskCDR.sql > /dev/null 2>&1')

    def writeProviders(self):
        providers = config.PBXProviders
        self.iaxRegistrations = []
        self.sipRegistrations = []

        os.system('rm /etc/asterisk/peers/sip/vulProv_* > /dev/null 2> /dev/null')
        os.system('rm /etc/asterisk/peers/iax/vulProv_* > /dev/null 2> /dev/null')

        sipProvs = ['vox', 'worldchat']

        for blname, vals in providers.items():
            if vals['type'] == 'hardware':
                #Do Something
                pass
            if vals['type'] == "sip" or vals['type'] in sipProvs:
                vals['name'] = blname
                
                fi = "/etc/asterisk/peers/sip/vulProv_%s.conf" % blname

                codecs = ""
                for codec in vals['codecs']:
                    codecs += "allow=%s\n" % codec

                vals['codecs'] = codecs
                #if 'append' not in vals:
                vals["append"] = "fromuser=%(username)s" % vals
                if vals.get('calllimit', False):
                    vals["calllimit"] = """ 
                    call-limit="""+str(vals['calllimit'])
                else:
                    vals['calllimit'] = ""

                if vals['type'] == 'vox':
                    vals['hostname'] = 'vphone.co.za'
                    vals['register'] = True
                    vals['codecs'] = "allow=g729"
                    vals['append'] = """fromuser=%(username)s
                    authuser=%(username)s
                    authname=%(username)s
                    authfrom=%(username)s
                    fromdomain=vphone.co.za
                    realm=vphone.co.za
                    canreinvite=no
                    outboundproxy=vphone.co.za
                    qualify=5000
                    insecure=very""" % vals
                
                if not vals.get('register',False):
                    blck = """[%(name)s]
                    type=peer
                    host=%(hostname)s
                    username=%(username)s
                    secret=%(password)s
                    context=%(context)s
                    useragent=VulaniPBX
                    tos=reliability
                    qualify=yes
                    disallow=all%(calllimit)s
                    %(append)s
                    %(codecs)s\n""" % vals
                else:
                    self.sipRegistrations.append(
                        "register => %s:%s@%s/%s\n" % (vals['username'], vals['password'], vals['hostname'],vals['username'])
                    )
                    blck = """[%(name)s]
                    type=peer
                    host=%(hostname)s
                    username=%(username)s
                    secret=%(password)s
                    qualify=yes
                    tos=reliability
                    useragent=VulaniPBX
                    disallow=all%(calllimit)s
                    insecure=very
                    %(codecs)s
                    %(append)s

                    [%(username)s]
                    type=user
                    host=dynamic
                    context=%(context)s
                    disallow=all
                    %(codecs)s\n""" % vals

                conf = open(fi, 'wt')
                conf.write(blck.replace(' ', ''))
                conf.close()

            if vals['type'] == "iax2":
                # Pull in registrations
                fi = "/etc/asterisk/peers/iax/vulProv_%s.conf" % blname

                vals['name'] = blname
                
                codecs = ""
                for codec in vals['codecs']:
                    codecs += "allow=%s\n" % codec

                vals['codecs'] = codecs

                trunking = vals['trunk']
                vals['trunk'] = trunking and "yes" or "no"

                if not vals.get('register',False):
                    blck = """[%(name)s]
                    type=friend
                    host=%(hostname)s
                    username=%(username)s
                    secret=%(password)s
                    context=%(context)s
                    tos=reliability
                    qualify=yes
                    trunk=%(trunk)s
                    disallow=all
                    %(codecs)s\n""" % vals
                else:
                    self.iaxRegistrations.append(
                        "register => %s:%s@%s\n" % (vals['username'], vals['password'], vals['hostname'])
                    )
                    blck = """[%(name)s]
                    type=peer
                    host=%(hostname)s
                    username=%(username)s
                    secret=%(password)s
                    qualify=yes
                    trunk=%(trunk)s
                    tos=reliability
                    disallow=all
                    %(codecs)s

                    [%(username)s]
                    type=user
                    host=dynamic
                    context=%(context)s
                    disallow=all
                    %(codecs)s\n""" % vals

                conf = open(fi, 'wt')
                conf.write(blck.replace(' ', ''))
                conf.close()

    def stripBlock(self, block):
        return '\n'.join([i.lstrip() for i in block.split('\n')])

    def writeSipConf(self):
        """Writes the sip.conf file"""
        content = self.configContent['sip'] % {
            'codec':str.join("\n        ",self.colapseData(self.codecs)),
            'domain':config.Domain,
            'context':'default',
            'registrations': str.join("        ", self.sipRegistrations)
        }
        self.writeFile('/etc/asterisk/sip.conf',content,';')
        os.system('rm /etc/asterisk/peers/sip/vulExt_* > /dev/null 2> /dev/null')

        lowbwCodecs = ["gsm"]
        if os.path.exists('/usr/lib/asterisk/modules/codec_g729.so'):
            lowbwCodecs = ['g729', 'gsm']

        # Create sip peers for handsets

        phones = config.PBX.get('phones', {})

        for exten, conf in phones.items():
            phDevString = "Phone/" + conf['username']

            conf['context'] = ""
            conf['voicemail'] = ''
            conf['append'] = ''
            ext = PBXUtils.getDeviceExtension(phDevString)
            if ext:
                if ext[1]['enabled']:
                    conf['extname'] = ext[0]
                    conf['context'] = "context = " + PBXUtils.getExtensionContext(ext[1])
                    if 'fullcallerID' in ext[1]:
                        conf['callerid'] = ext[1]['fullcallerID']
                    if ext[1].get('voiceMail', False):
                        conf['voicemail'] = 'mailbox=' + str(ext[1]['extensions'][0])
                    conf['append'] = """callgroup=0
                accountcode=%(extname)s
                pickupgroup=0
                vmexten=*96
                %(voicemail)s
                """ % conf
                    if ext[1].get('lowbw', False) and len(lowbwCodecs) > 0:
                        conf['append'] += """disallow=all
                allow=%s
                        """ % "\n               allow=".join(lowbwCodecs)

            block = """[%(username)s]
                type=friend
                %(context)s
                callerid=%(callerid)s
                username=%(username)s
                host=dynamic
                notifyringing=yes
                nat=yes
                notifyhold=yes
                limitonpeers=yes
                call-limit=99 
                canreinvite=no
                qualify=5000
                dtmfmode=rfc2833
                %(append)s
                """ % conf
            
            if conf.get('call-limit', 0):
                block += "call-limit=%s\n" % conf['call-limit']
            

            
            ph = open('/etc/asterisk/peers/sip/vulExt_%s.conf' % exten, 'wt')
            ph.write(self.stripBlock(block))
            ph.close()
    
    def writeIaxConf(self):
        """Writes the iax.conf file"""
        content = self.configContent['iax'] % {
            'registrations': str.join("        ", self.iaxRegistrations)
        }
        self.writeFile('/etc/asterisk/iax.conf',content,';')
    
    def writeIndications(self):
        """Writes the indications file indications.conf"""
        content = self.configContent['indications'] % {
            'region':self.region #Future may require this to be set elsewhere
        }
        self.writeFile('/etc/asterisk/indications.conf',content,';')

    def writeMusicOnHold(self):
        """Generates a music on hold config file"""
        holdMusicData = { 'default':{'mode':'files','directory':'/usr/share/asterisk/mohmp3','random':'yes'}}
        content = "\n        "
        content += str.join('\n        ',self.colapseData(holdMusicData))
        self.writeFile('/etc/asterisk/musiconhold.conf',content,';')

    def writeStatics(self):
        """Write configs that do not change"""
        files = {
            #Identifies the details for each config file content from configContent
            #ID       :['PATHTOCONFIG'],'COMMENT Character']
            'debDefault':['/etc/default/asterisk', "#"],
            'asterisk':['/etc/asterisk/asterisk.conf',';'],
            'cdr':['/etc/asterisk/cdr.conf',';'],
            'cdr_custom':['/etc/asterisk/cdr_custom.conf',';'],
            'cdr_mysql':['/etc/asterisk/cdr_mysql.conf',';'],
            'codecs':['/etc/asterisk/codecs.conf',';'],
            'extensions_macro':['/etc/asterisk/extensions/macros/vulani.ael','//'],
            'extensions_recorder':['/etc/asterisk/extensions/recording.ael','//'],
            'modules':['/etc/asterisk/modules.conf',';'],
            'features':['/etc/asterisk/features.conf',';'],
            'manager':['/etc/asterisk/manager.conf',';'],
            'sip_notify':['/etc/asterisk/sip_notify.conf',';'],
            'zapata':['/etc/asterisk/zapata.conf',';'],
        }
        #Write the Extensions Config
        extConf = {
            'timeout': config.PBX.get('timeout', 30),
            'qtimeout': config.PBX.get('qtimeout', 30)
        }
        self.writeFile('/etc/asterisk/extensions.ael', self.configContent['extensions'] % extConf, '//')
        #Write all the other configs
        for confIndex in files.keys():
            self.writeFile(files[confIndex][0], self.configContent[confIndex], files[confIndex][1])

    def writeFile(self, fileName, content, commentChar, indentChars=8):
        """Cleans up the content and then writes the file"""
        contentSplit = content.split('\n')
        content = ""
        contentState = False
        for line in contentSplit:
            if len(line) > 1 or contentState:
                content += line[indentChars:] + '\n'
                contentState = True;
        Utils.writeConf(fileName, content, commentChar)
    
    def colapseData(self, data):
        """Recursively goes through a variable and generates a textual representation compatible with asterisk config files"""
        output = [] 
        if type(data) == dict:
            for indexName in data.keys():
                if type(data[indexName]) == dict:
                    output += ["[%s]"% indexName]
                    output += self.colapseData(data[indexName])
                else:
                    output += ["%s=%s" % (indexName, data[indexName])]
        elif type(data) == list:
            for data_det in data:
                for value in data_det[1]:
                    output += ["%s=%s" % (data_det[0], value)]
        return output

    def installPCodec(self):
        """Installs codec"""
        if os.path.exists('/usr/lib/asterisk/modules/codec_g729.so'):
            return

        try:        
            cpuinfo = open('/proc/cpuinfo','r')
        except Exception, _ex:
            print _ex
            return

        cpuflags = []

        for line in cpuinfo:
            if ":" not in line:
                continue
            k,v = line.strip().split(":")
            if k[0:5] == "flags":
                cpuflags = v.strip().split(' ')
                break

        if "64bit" in platform.architecture()[0]:
            arch = "-x86_64"
        else:
            arch = ""

        cput = "pentium"

        for val in cpuflags:
            if "sse4" in val:
                cput = "core2-sse4"

        url = "http://asterisk.hosting.lv/bin/"
        g729 = "codec_g729-ast14-gcc4-glibc%s-%s.so" % (arch, cput)
        g723 = "codec_g723-ast14-gcc4-glibc%s-%s.so" % (arch, cput)


        os.system('asterisk -r -x "module unload codec_g729.so"')
        os.system('asterisk -r -x "module unload codec_g729.so"')

        os.system('wget -O /usr/lib/asterisk/modules/codec_g729.so.tmp %s%s > /dev/null 2> /dev/null' % (url,g729))
        os.system('wget -O /usr/lib/asterisk/modules/codec_g723.so.tmp %s%s > /dev/null 2> /dev/null' % (url,g723))

        os.system('mv /usr/lib/asterisk/modules/codec_g729.so.tmp /usr/lib/asterisk/modules/codec_g729.so')
        os.system('mv /usr/lib/asterisk/modules/codec_g723.so.tmp /usr/lib/asterisk/modules/codec_g723.so')

        os.system('chmod a+r /usr/lib/asterisk/modules/*')
        os.system('asterisk -r -x "module load codec_g729.so"')
        os.system('asterisk -r -x "module load codec_g723.so"')

        #os.system('wget -O /tmp/cdecMD5 http://asterisk.hosting.lv/bin/MD5SUM > /dev/null 2> /dev/null')
        #try:
        #    file = open('/tmp/cdecMD5', 'r')
        #except Exception, _ex:
        #    print _ex
        #    return

        #for line in file:
        #    md5sum, filename = line.strip().replace('  ', ' ').split(' ')




    def resetPerms(self):
        os.system('chmod a+r -R /etc/asterisk/')
        os.system('chown -R asterisk:asterisk /etc/asterisk/')
        os.system('chown -R asterisk:asterisk /usr/share/asterisk/mohmp3')
        os.system('chmod a+r -R /usr/share/asterisk/mohmp3')
        os.system('chmod a+rw /usr/local/share/asterisk/sounds/')
        os.system('chmod a+r -R /var/lib/samba/data/vRecordings')
        os.system('chmod a+r -R /var/lib/samba/data/vFaxing')
        os.system('chown asterisk:asterisk -R /var/lib/samba/data/vRecordings')
        os.system('chown asterisk:asterisk -R /var/lib/samba/data/vFaxing')

    def prepareAsterisk(self):
        """Clear the asterisk directory"""
        dateString = str(datetime.now().date())
        os.system('tar czvf /var/lib/asterisk/beforeVulani-%s.tar.gz /etc/asterisk > /dev/null' % dateString) #Backup what ever is in asterisk Dir (Save some sad faces)
        self.writeFile('/etc/default/asterisk',self.configContent['debDefault'],'#')


        os.system('rm -fr /etc/asterisk/*')
        os.system('mkdir -p /etc/asterisk/peers/sip')
        os.system('touch /etc/asterisk/peers/sip/__blank__.conf') #Anticipation of a problem
        os.system('mkdir -p /etc/asterisk/peers/iax')
        os.system('touch /etc/asterisk/peers/iax/__blank__.conf') #Anticipation of a problem
        os.system('mkdir -p /etc/asterisk/peers/zap')
        os.system('touch /etc/asterisk/peers/zap/__blank__.conf') #Anticipation of a problem
        os.system('mkdir -p /usr/share/asterisk/mohmp3')
        os.system('cp /usr/local/tcs/tums/files/astMoh/* /usr/share/asterisk/mohmp3/')
        os.system('chown -R asterisk:asterisk /usr/share/asterisk/mohmp3')
        os.system('chmod a+r -R /usr/share/asterisk/mohmp3')
        os.system('cp /usr/local/tcs/tums/packages/astRecs/* /usr/local/share/asterisk/sounds/')
        os.system('mkdir -p /var/lib/samba/data/vRecordings/inbound/')
        os.system('mkdir -p /var/lib/samba/data/vRecordings/outbound/')
        os.system('mkdir -p /var/lib/samba/data/vFaxing/')
        os.system('chmod a+rw -R /var/lib/samba/data/vRecordings')
        os.system('chown asterisk:asterisk -R /var/lib/samba/data/vRecordings')
        os.system('chmod a+rw /usr/local/share/asterisk/sounds/')
        os.system('mkdir -p /etc/asterisk/extensions/macros')
        os.system('mkdir -p /etc/asterisk/extensions/routing')
        os.system('echo "DO NOT REMOVE" > /etc/asterisk/VULANI')
        os.system('chown -R asterisk:asterisk /etc/asterisk/')
