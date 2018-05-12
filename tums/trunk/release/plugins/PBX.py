import config, os
from Core import PBXUtils, Utils
from datetime import datetime

class Plugin(object):
    parameterHook = "--pbx"
    parameterDescription = "Reconfigure PBX"
    parameterArgs = ""
    autoRun = False 

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
        "/etc/asterisk/zapata.conf" ]

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
    'extensions':"""
        //Vulani Configuration
        #include "/etc/asterisk/extensions/*.ael"
        #include "/etc/asterisk/extensions/macros/*.ael"
        #include "/etc/asterisk/extensions/routing/*.ael"
    """,
    'extensions_macro':"""
        //User Standard Extension Macro
        macro std-exten( ext , dev, user, monitor, timeout, fwdVoicemail, fwdOther ) {
               if(!${timeout}) {
                   timeout=30;
               };
               Set(CDR(userfield)=dst\=${user});
               if(${monitor}) {
                   Set(RECFILE=inbound/${user}-${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)}-${CALLERID(num)}.wav);
                   MixMonitor(/var/lib/samba/public/vRecordings/${RECFILE});
                   Set(CDR(userfield)=${CDR(userfield)}\;rec\=${RECFILE});
               };
               SET(GLOBAL(PICKUPMARK)=${ext});
               Dial(${dev},${timeout});
               switch(${DIALSTATUS}) {
               case BUSY:
                       if(!${fwdVoicemail}) {
                           if(${fwdOther}) {
                               Dial(${fwdOther},${timeout});
                           };
                       } else { 
                           Voicemail(b${ext});
                       };
                       break;
               default:
                       if(!${fwdVoicemail}) {
                           if(${fwdOther}) {
                               Dial(${fwdOther},${timeout});
                           };
                       } else { 
                           Voicemail(u${ext});
                       };
               };
               catch a {
                       if(!${fwdVoicemail}) {
                           //if(${fwdOther}) {
                           //    Dial(${fwdOther},timeout);
                           //};
                       } else { 
                           VoiceMailMain(${ext});
                       };
                       return;
               };
        };
        //Queue Extension
        macro queue-exten(ext, queue, timeout) {
            if(!${timeout}) {
                timeout=30;
            };
            Set(RECFILE=inbound/q${queue}-${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)}-${CALLERID(num)}.wav);
            MixMonitor(/var/lib/samba/public/vRecordings/${RECFILE});
            DevState(${ext},2);
            Queue(${queue});
            catch h {
                DevState(${ext},0);
            };
            DevState(${ext},0);
        };
        //Router Extension
        //%(prefix)s${EXTEN%(ltrim)s},%(dev0)s,%(dev1)s,%(dev2)s,%(dev3)s,%(dev4)s,%(dev5)s,%(provider)s,,)
        macro route-provider(ext,dev,dev1,dev2,dev3,dev4,dev5,providerName,monitor,callerID,timeout) {
               if(!${timeout}) {
                   timeout=30;
               };
               NoOp(Dialing Via Provider ${providerName});
               Set(CDR(userfield)=dst\=${providerName});
               if(${monitor}) {
                   src=${CDR(accountcode)};
                   if(!${src}) {
                       src=${CALLERID(num)};
                   };
                   Set(RECFILE=outbound/${ext}-${STRFTIME(${EPOCH},,%Y%m%d%H%M%S)}-${src}.wav);
                   MixMonitor(/var/lib/samba/public/vRecordings/${RECFILE});
                   Set(CDR(userfield)=${CDR(userfield)}\;rec\=${RECFILE});
               };
               Set(CDR(provider)=${providerName});
               Dial(${dev}/${ext},${timeout});
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
        pickupexten = *8                ; Configure the pickup extension.  Default is *8

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
        tos=lowdelay
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
        monitor-type = MixMonitor

        %(queues)s
    """,
    'sip':"""
        [general]
        context=%(context)s
        realm=%(domain)s
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
            
            # Write Binding Extensions
            self.writeExtensions()
            
            # Write Voicemail Settings
            self.writeVoiceMail()

            # Create CDR DB
            self.createCDRDB()

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
            'mailbox': str.join('\n', voiceMailConfig),
        }
        self.writeFile('/etc/asterisk/voicemail.conf',voicemailData,';')

    def writeQueues(self):
        """Generate the queue file"""
        queues = {}
        #Start by collecting setting for the queues
        for queueName, queueData in config.PBX.get('queues', {}).items():
            queues[queueName] = queueData
            queues[queueName]['members'] = []

        #Merge members into the dict entry for each queue
        for user, extension in config.PBXExtensions.items():
            for queue in extension.get('queues', []):
                if queue in queues:
                    queues[queue]['members'].extend([
                        PBXUtils.resolveDevice(dev) for dev in extension['devices']
                    ])

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

                content = """&route-provider(%(prefix)s${EXTEN%(ltrim)s},%(dev0)s,%(dev1)s,%(dev2)s,%(dev3)s,%(dev4)s,%(dev5)s,%(provider)s,%(monitor)s,,);""" % {
                    'num': clr(num[0]),
                    'prefix': clr(num[2]),
                    'provider': clr(num[1]),
                    'ltrim': clr(num[3]),
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
            if not userExt['enabled']:
                continue
            devSet = str.join('&', [ PBXUtils.resolveDevice(dev) for dev in userExt['devices'] ])
            hintDev = [ PBXUtils.resolveDevice(dev) for dev in userExt['devices'] ][0]
            for extension in userExt['extensions']:
                userExtensionCompiled = userExtensionCompiled + """
                hint(%(dev)s) %(exten)s => &std-exten(%(mailboxname)s,%(dev)s,%(user)s,%(monitor)s,,%(fwdVoiceMail)i,);""" % {
                    'exten': extension,
                    'mailboxname': userExt['extensions'][0],
                    'dev': devSet,
                    'fwdVoiceMail': userExt['voiceMail'],
                    'user': user,
                    'monitor': config.PBX.get('recordAll', True) and '1' or '',
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
             
            ivrExtensions += """
            context ivr-%(name)s {
                s => {
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
                'timeout': ivrDet['timeout'],
                'ivrContent': ivrCompiled,
                'optionsPlayback': optionsPlayback,
                'welcomePlayback': welcomePlayback,
                'timeoutEntry': timeoutEntry
            }

        self.writeFile('/etc/asterisk/extensions/ivrContexts.ael', ivrExtensions,'//',12)

        #compiling queues
        for qName, qDet in config.PBX.get('queues', {}).items():
            if 'extensions' in qDet:
                systemExt.append("hint(DS/%(exten)s) %(exten)s => &queue-exten(%(exten)s,%(queue-name)s,);" % {
                    'queue-name': qName,
                    'exten': qDet['extensions'][0],
                }) 

        systemCompiled = str.join('\n                ',systemExt)

        # Write System Extensions
        systemExt = """
            context systemExtensions {
                %s
            };
            context featureExtensions {
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
                *8 => Pickup(0);
                _*8. => {
                    DPickup(${EXTEN:2}@PICKUPMARK);
                };
            };
        """ % systemCompiled
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

        for blname, vals in providers.items():
            if vals['type'] == 'hardware':
                #Do Something
                pass
            if vals['type'] == "iax2":
                # Pull in registrations
                self.iaxRegistrations.append(
                    "register => %s:%s@%s\n" % (vals['username'], vals['password'], vals['hostname'])
                )

                fi = "/etc/asterisk/peers/iax/%s.conf" % blname

                vals['name'] = blname
                
                codecs = ""
                for codec in vals['codecs']:
                    codecs += "allow=%s\n" % codec

                vals['codecs'] = codecs

                trunking = vals['trunk']
                vals['trunk'] = trunking and "yes" or "no"

                if vals['branch']:
                    
                    
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
            'context':'default'
        }
        self.writeFile('/etc/asterisk/sip.conf',content,';')

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

            block = """[%(username)s]
                type=peer
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

            
            ph = open('/etc/asterisk/peers/sip/%s.conf' % exten, 'wt')
            ph.write(self.stripBlock(block))
            ph.close()
    
    def writeIaxConf(self):
        """Writes the iax.conf file"""
        content = self.configContent['iax'] % {
            'registrations': ''.join(self.iaxRegistrations)
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
            'asterisk':['/etc/asterisk/asterisk.conf',';'],
            'cdr':['/etc/asterisk/cdr.conf',';'],
            'cdr_custom':['/etc/asterisk/cdr_custom.conf',';'],
            'cdr_mysql':['/etc/asterisk/cdr_mysql.conf',';'],
            'codecs':['/etc/asterisk/codecs.conf',';'],
            'extensions':['/etc/asterisk/extensions.ael','//'],
            'extensions_macro':['/etc/asterisk/extensions/macros/vulani.ael','//'],
            'extensions_recorder':['/etc/asterisk/extensions/recording.ael','//'],
            'modules':['/etc/asterisk/modules.conf',';'],
            'features':['/etc/asterisk/features.conf',';'],
            'manager':['/etc/asterisk/manager.conf',';'],
            'sip_notify':['/etc/asterisk/sip_notify.conf',';'],
            'zapata':['/etc/asterisk/zapata.conf',';'],
        }
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


    def prepareAsterisk(self):
        """Clear the asterisk directory"""
        dateString = str(datetime.now().date())
        os.system('tar czvf /var/lib/asterisk/beforeVulani-%s.tar.gz /etc/asterisk > /dev/null' % dateString) #Backup what ever is in asterisk Dir (Save some sad faces)
        os.system('rm -fr /etc/asterisk/*')
        os.system('mkdir -p /etc/asterisk/peers/sip')
        os.system('touch /etc/asterisk/peers/sip/__blank__.conf') #Anticipation of a problem
        os.system('mkdir -p /etc/asterisk/peers/iax')
        os.system('touch /etc/asterisk/peers/iax/__blank__.conf') #Anticipation of a problem
        os.system('mkdir -p /etc/asterisk/peers/zap')
        os.system('touch /etc/asterisk/peers/zap/__blank__.conf') #Anticipation of a problem
        os.system('mkdir -p /usr/share/asterisk/mohmp3')
        os.system('cp /usr/local/tcs/tums/packages/astMoh/* /usr/share/asterisk/mohmp3/')
        os.system('chown -R asterisk:asterisk /usr/share/asterisk/mohmp3')
        os.system('chmod a+r -R /usr/share/asterisk/mohmp3')
        os.system('cp /usr/local/tcs/tums/packages/astRecs/* /usr/local/share/asterisk/sounds/')
        os.system('mkdir -p /var/lib/samba/public/vRecordings/inbound/')
        os.system('mkdir -p /var/lib/samba/public/vRecordings/outbound/')
        os.system('chmod a+rw -R /var/lib/samba/public/vRecordings')
        os.system('chown asterisk:asterisk -R /var/lib/samba/public/vRecordings')
        os.system('chmod a+rw /usr/local/share/asterisk/sounds/')
        os.system('mkdir -p /etc/asterisk/extensions/macros')
        os.system('mkdir -p /etc/asterisk/extensions/routing')
        os.system('echo "DO NOT REMOVE" > /etc/asterisk/VULANI')
        os.system('chown -R asterisk:asterisk /etc/asterisk/')
