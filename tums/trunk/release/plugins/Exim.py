import config, os
from Core import Utils


class Plugin(object):
    parameterHook = "--exim"
    parameterDescription = "Reconfigure exim"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/exim/exim.conf",
        "/etc/exim/local_domains",
        "/etc/exim/relay_domains",
        "/etc/exim/hubbed_hosts",
    ]

    def __init__(self):
        if os.path.exists('/etc/exim4'):
            self.configFiles = [
                "/etc/exim4/exim.conf",
                "/etc/exim4/local_domains",
                "/etc/exim4/relay_domains",
                "/etc/exim4/hubbed_hosts"
            ]

    def reloadServices(self):
        os.system('/etc/init.d/exim4 restart')

    def MailMan(self):        
        if config.Mail.get('mailman'):
            if config.Mail.get('mailmanvirtualaliases'):
                mm_router = [
                    "        mailman_router1:",
                    " domains = +local_domains",
                    " require_files = MAILMAN_HOME/lists/$local_part/config.pck",
                    " driver = accept",
                    " local_parts = mailman",
                    " local_part_suffix_optional",
                    " local_part_suffix = -bounces : -bounces+* : \\",
                    "          -confirm+* : -join : -leave : \\",
                    "          -subscribe : -unsubscribe : \\",
                    "          -owner : -request : -admin",
                    " transport = mailman_transport",
                    " group = MAILMAN_GROUP\n",
                    "mailman_router2:",
                    " domains = +local_domains",
                    " condition = ${lookup{$local_part@$domain}lsearch{MAILMAN_HOME/data/virtual-mailman}{1}{0}}",
                    " require_files = MAILMAN_HOME/lists/$local_part/config.pck",
                    " driver = accept",
                    " local_part_suffix_optional",
                    " local_part_suffix = -bounces : -bounces+* : \\",
                    "                     -confirm+* : -join : -leave : \\",
                    "                     -subscribe : -unsubscribe : \\",
                    "                     -owner : -request : -admin",
                    " transport = mailman_transport",
                    " group = MAILMAN_GROUP\n"                    
                ]
                mm_transport = [
                    "mailman_transport:",
                    " driver = pipe",
                    " command = MAILMAN_WRAP \\",
                    "           '${if def:local_part_suffix \\",
                    "                 {${sg{$local_part_suffix}{-(\\\\w+)(\\\\+.*)?}{\\$1}}} \\",
                    "                 {post}}' \\",
                    "           $local_part",
                    " current_directory = MAILMAN_HOME",
                    " home_directory = MAILMAN_HOME",
                    " user = MAILMAN_USER",
                    " group = MAILMAN_GROUP",
                    " freeze_exec_fail = true\n\n"              
                ]
            else:
                mm_router = [
                    "        mailman_router:",
                    " domains = +local_domains",
                    " driver = accept",
                    " require_files = MAILMAN_HOME/lists/$local_part/config.pck",
                    " local_part_suffix_optional",
                    " local_part_suffix = -bounces : -bounces+* : \\",
                    " -confirm+* : -join : -leave : \\",
                    " -owner : -request : -admin",
                    " transport = mailman_transport\n\n"
                ]
                mm_transport = [
                    "        mailman_transport:",
                    " driver = pipe",
                    " command = MAILMAN_WRAP \\",
                    "   '${if def:local_part_suffix \\",
                    "       {${sg{$local_part_suffix}{-(\\\\w+)(\\\\+.*)?}{\\$1}}} \\",
                    "       {post}}' \\",
                    "   $local_part",
                    " current_directory = MAILMAN_HOME",
                    " home_directory = MAILMAN_HOME",
                    " user = MAILMAN_USER",
                    " group = MAILMAN_GROUP\n\n"
                ]
            mm_main = [
                "        MAILMAN_HOME=/var/lib/mailman",
                "MAILMAN_WRAP=MAILMAN_HOME/mail/mailman",
                "MAILMAN_USER=list",
                "MAILMAN_GROUP=list\n"
                ]            
            return (
                '\n        '.join(mm_router),
                '\n        '.join(mm_transport),
                '\n        '.join(mm_main)
            )
        else:
            return ('','','')

    def Greylisting(self):
        if config.Mail.get('greylisting', True):
            aclCheckSenderGreylist = [
                "        # Defer if greylisted",
                "  defer message     = $sender_host_address is not yet authorized to deliver \\",
                "                      mail from <$sender_address> to <$local_part@$domain>. \\",
                "                      Please try later.",
                "    log_message     = greylisted.",
                "    !senders        = :",
                "    !hosts          = ${if exists {/etc/greylistd/whitelist-hosts}\\",
                "                                  {/etc/greylistd/whitelist-hosts}{}} : \\",
                "                      ${if exists {/var/lib/greylistd/whitelist-hosts}\\",
                "                                  {/var/lib/greylistd/whitelist-hosts}{}} : +relay_hosts",
                "    domains         = +local_domains : +relay_domains",
                "    verify          = recipient/callout=20s,use_sender,defer_ok",
                "    condition       = ${readsocket{/var/run/greylistd/socket}\\",
                "                       {--grey \\",
                "                       $sender_host_address \\",
                "                       $sender_address \\",
                "                       $local_part@$domain}\\",
                "                       {5s}{}{false}}",
                "# Deny if blacklisted by greylistd",
                " deny message       = $sender_host_address is blacklisted from delivering \\",
                "                      mail from <$sender_address> to <$local_part@$domain>.",
                "    log_message     = blacklisted.",
                "    !senders        = :",
                "    verify          = recipient/callout=20s,use_sender,defer_ok",
                "    condition       = ${readsocket{/var/run/greylistd/socket}\\",
                "                       {--black \\",
                "                       $sender_host_address \\",
                "                       $sender_address \\",
                "                       $local_part@$domain}\\",
                "                       {5s}{}{false}}\n"
            ]

            aclCheckDataGreylist = [
                "        # Defer if greylisted",
                " defer message     = $sender_host_address is not yet authorized to deliver \\",
                "                      mail from <$sender_address> to <$recipients>. \\",
                "                      Please try later.",
                "    log_message    = greylisted.",
                "    senders        = :",
                "    !hosts         = ${if exists {/etc/greylistd/whitelist-hosts}\\",
                "                                 {/etc/greylistd/whitelist-hosts}{}} : \\",
                "                     ${if exists {/var/lib/greylistd/whitelist-hosts}\\",
                "                                 {/var/lib/greylistd/whitelist-hosts}{}} : +relay_hosts",
                "    !authenticated = *",
                "    condition      = ${readsocket{/var/run/greylistd/socket}\\",
                "                      {--grey \\",
                "                      $sender_host_address \\",
                "                      $recipients}\\",
                "                      {5s}{}{false}}",
                "# Deny if blacklisted by greylist",
                " deny message      = $sender_host_address is blacklisted from delivering \\",
                "                     mail from <$sender_address> to <$recipients>.",
                "    log_message    = blacklisted.",
                "    !senders       = :",
                "    !authenticated = *",
                "    condition      = ${readsocket{/var/run/greylistd/socket}\\",
                "                      {--black \\",
                "                      $sender_host_address \\",
                "                      $recipients}\\",
                "                      {5s}{}{false}}\n"
            ]

            return ('\n        '.join(aclCheckSenderGreylist), '\n        '.join(aclCheckDataGreylist))
        else:
            return ('', '')

    def writeConfig(self, *a):
        # VERY IMPORTANT NOTICE! 
        #
        #  All lines are lead by 8 spaces. These spaces are stripped out at the end.
        #  If you have less than 8 spaces before any new line written to the config
        #  then it will be broken
        #  This is done to make the source semi readable 
        # 
        # END OF IMPORTANT NOTICE

        # Setup local delivery domains
        locals = "\n".join(config.LocalDomains)

        # A list of servers we redeliver or hub mail to
        serverhosts = ['127.0.0.1']

        # Configure hubbed hosts and relay domains
        relayDoms = config.Mail.get('relay', [])
        hubs = ""
        mailReroute = ""
        for dom, dest in config.Mail.get('hubbed', []):
            if dest not in serverhosts:
                serverhosts.append(dest)
            if "@" in dom:
                mailReroute += "%s       %s        byname\n" % (dom,dest)
                dom = dom.split('@')[-1]
            else:
                hubs += "%s        %s        byname\n" % (dom, dest)

            if dom not in relayDoms:
                relayDoms.append(dom)

        # Branch configuration 
        branches = config.Mail.get('branchtopology', {})
        branchMap = {}
        for r in config.Mail.get('branches', []):

            # if the items in branches are not lists, we assume an old datastructure
            if not isinstance(r, list):
                branchMap[r] = None
                continue

            svr, relay = r


            branchMap[svr] = None

            if relay:
                branchMap[svr] = relay.replace(' ', '').replace(';', ',').replace(':', ',').split(',')

        branchReroute = ""
        for branch, addrs in branches.items():
            for addr in addrs:
                # Extend relay domains to handle this remote server too
                dom = addr.split('@')[-1]
                if dom not in relayDoms:
                    relayDoms.append(dom)

                if branchMap[branch]:
                    relay = ':'.join(branchMap[branch])
                else:
                    relay = branch
                
                if relay not in serverhosts:
                    serverhosts.append(relay)

                # Add the address to mail reroute
                branchReroute += "%s       %s        byname\n" % (
                    addr,
                    relay
                )
                
        # Setup our relay list
        relays = "\n".join(relayDoms)

        # Initialise blacklists
        blacklistSender = ""
        blacklistHost = ""
        blacklistDom  = ""
        
        for b in config.Mail.get('blacklist', []):
            if "@" in b:
                blacklistSender += b + '\n'
            else:
                try:
                    int(b.split('.')[0])
                    blacklistHost += b + '\n'
                except:
                    blacklistDom += b + '\n'

        whitelistSender = ""
        whitelistHost = ""
        whitelistDom = ""
        for w in config.Mail.get('whitelist', []):
            if "@" in w:
                whitelistSender += w + "\n"
            else:
                try:
                    int(w.split('.')[0])
                    whitelistHost += w + '\n'
                except:
                    whitelistDom += w + '\n'

        catchall = ""
        for c in config.Mail.get('catchall', []):
            catchall += c + "\n"

        # System filters
        copyTo = "#System Filter\nif error_message then finish endif\n\n"

        if config.Mail.get('copytoall', None):
            copyTo += "if first_delivery then\n"
            copyTo += "    unseen deliver %s errors_to postmaster@%s\n" % (config.Mail['copytoall'], config.Domain)
            copyTo += "endif\n\n"

        for addr, dest in config.Mail.get('copys', []):
            copyTo += "if $recipients contains %s then\n" % addr
            copyTo += "    unseen deliver %s errors_to postmaster@%s\n" % (dest, config.Domain)
            copyTo += "endif\n\n"

        # Global system filter
        if os.path.exists('/usr/local/tcs/tums/filter.db'):
            filterCont = open('/usr/local/tcs/tums/filter.db').read()
            copyTo += filterCont
            copyTo += "\n"
        
        allowsend = ""
        if config.Mail.get('allowsend', None):
            allowsend = "\n".join(config.Mail['allowsend'])

        if config.Mail.get('disableratelimit', None):
            rateLimit = ""
        else:
            rateLimit = """
        # System-wide rate limit for dodgey senders
          defer message = Connection limited: Sender rate $sender_rate / $sender_rate_period.
                hosts            = +relay_hosts
                !sender_domains  = +local_domains : +relay_domains
                !senders         = :
                ratelimit = 50 / 1h / strict\n"""

        if config.Mail.get('disablerpfilter', None):
            senderRpFilter = ""
        else:
            senderRpFilter = """
        # Block mail from forged address on the local side. 
          deny message  =  Vulani has rejected this message from $sender_address because it is not local to this site. http://vulani.net/
                !sender_domains  = +local_domains : +relay_domains
                !senders         = :
                !senders         = +acl_allowed_senders
                hosts            = +relay_hosts
                !hosts           = +server_hosts\n"""


        Utils.writeConf('/etc/exim4/sender_whitelist', whitelistSender, '#')
        Utils.writeConf('/etc/exim4/host_whitelist', whitelistHost, '#')
        Utils.writeConf('/etc/exim4/domain_whitelist', whitelistDom, '#')

        Utils.writeConf('/etc/exim4/sender_blacklist', blacklistSender, '#')
        Utils.writeConf('/etc/exim4/host_blacklist', blacklistHost, '#')
        Utils.writeConf('/etc/exim4/domain_blacklist', blacklistDom, '#')

        Utils.writeConf('/etc/exim4/allowed_senders', allowsend, '#')

        Utils.writeConf('/etc/exim4/host_noavscan', "", '#')

        Utils.writeConf('/etc/exim4/local_domains', locals, '#')
        Utils.writeConf('/etc/exim4/relay_domains', relays, '#')
        Utils.writeConf('/etc/exim4/hubbed_hosts', hubs, '#')
        Utils.writeConf('/etc/exim4/mail_reroute', mailReroute, '#')
        Utils.writeConf('/etc/exim4/branch_reroute', branchReroute, '#')
        Utils.writeConf('/etc/exim4/system_filter', copyTo, '#')
        Utils.writeConf('/etc/exim4/catchall_domains', catchall, '#')

        # Get rid of the autogenerated tag so aptitude doesn't break us
        os.system('rm /var/lib/exim4/config.autogenerated > /dev/null 2>&1')
        systemFilter = "system_filter = /etc/exim4/system_filter\n"
 
        if config.Mail.get('noavscan'):
            avScan = ""
            avscanacl = ""
            print "Antivirus scanning disabled!"
        else:
            avScan = "av_scanner = clamd:/var/run/clamav/clamd.sock"
            avscanacl = """            accept condition  = ${if <={$message_size}{250k}{yes}{no}}
            deny message      = This message contains a virus ($malware_name)
                !hosts        = +acl_host_noavscan
                malware       = *\n"""

        primaryDomain = config.Domain
        hostname = config.ExternalName  # Must be externally lookupable(?!?) name
        mailSize = config.Mail.get('mailsize', '')
        localNet = " : ".join([v for k,v in Utils.getLanNetworks(config).items()])
        
        for n in Utils.getLanIP6s(config):
            localNet += ' : %s ' % n.replace(':', '::')

        # fill in allowed hosts (config.Mail.relay-from)
        if config.Mail.get('relay-from'):
            localNet += ' : ' + ' : '.join(config.Mail['relay-from'])
        extensionBlock = ""

        # Blocked file extensions
        if config.Mail.get('blockedfiles', []):
            extensionBlock = "            deny  message     = We do not accept \".$found_extension\" attachments here.\n"
            extensionBlock += "                 demime      = %s\n" % ':'.join(config.Mail['blockedfiles'])

        # Mail rewrite rules
        rewriteRules = ""
        for fromm,too,flags in config.Mail.get('rewrites', []):
            # flags is one of TtFfbcr
            rewriteRules+='        *@%s    $1@%s   %s\n' % (fromm, too, flags)

        # Get any mailman settings
        mm_router, mm_transport, mm_main = self.MailMan()

        # SpamAssassin required score
        spamscore = config.Mail.get('spamscore', 70)

        # Get greylisting ACLS (if greylisting is enabled)
        aclCheckSenderGreylist, aclCheckDataGreylist = self.Greylisting()

        ### Enable tweaked performance
        performanceTweak = ""
        if config.Mail.get('performance', False):
            performanceTweak =  "        # use muliple directories (default false)\n"
            performanceTweak += "        split_spool_directory\n"
            performanceTweak += "        # queue incoming if load high (no default)\n"
            performanceTweak += "        queue_only_load = 4\n"
            performanceTweak += "        # maximum simultaneous queue runners (default 5)\n"
            performanceTweak += "        queue_run_max = 0\n"
            performanceTweak += "        # parallel delivery of one message to a number of remote hosts (default 2)\n"
            performanceTweak += "        remote_max_parallel = 30\n"
            performanceTweak += "        # simultaneous connections from a single host (default 10)\n"
            performanceTweak += "        smtp_accept_max_per_connection = 20\n"
            performanceTweak += "        # maximum number of waiting SMTP connections (default 20)\n"
            performanceTweak += "        smtp_connect_backlog = 50\n"
            performanceTweak += "        # maximum number of simultaneous incoming SMTP calls that Exim will accept (default 20)\n"
            performanceTweak += "        smtp_accept_max = 0\n"

        if config.Mail.get('rbls'):
            RBL = config.Mail.get('rbls')
        else:
            RBL = [
                "dsn.rfc-ignorant.org/$sender_address_domain",
                "zen.spamhaus.org",
                "dnsbl.njabl.org",
                "bhnc.njabl.org",
                "combined.njabl.org",
                "bl.spamcop.net",
                "psbl-mirror.surriel.com",
                "blackholes.mail-abuse.org",
                "dialup.mail-abuse.org"
            ]


        ### Exim main configuration

        eximMain = """
        ######################################################################
        #                    MAIN CONFIGURATION SETTINGS                     #
        ######################################################################
        ldap_default_servers = %(ldap)s
        primary_hostname = %(hostname)s
        %(avScan)s
        spamd_address = 127.0.0.1 783
        %(systemFilter)s
        
        domainlist local_domains = @ : lsearch;/etc/exim4/local_domains
        domainlist relay_domains = lsearch;/etc/exim4/relay_domains
        hostlist   relay_hosts = 127.0.0.1 : %(hostlist)s
        hostlist   server_hosts = %(serverhosts)s
        
        domainlist acl_domain_whitelist = lsearch;/etc/exim4/domain_whitelist
        hostlist acl_host_whitelist = net-iplsearch;/etc/exim4/host_whitelist
        addresslist acl_sender_whitelist = lsearch*@;/etc/exim4/sender_whitelist
        domainlist acl_domain_blacklist = lsearch;/etc/exim4/domain_blacklist
        hostlist acl_host_blacklist = net-iplsearch;/etc/exim4/host_blacklist
        addresslist acl_sender_blacklist = lsearch*@;/etc/exim4/sender_blacklist
        addresslist acl_allowed_senders = /etc/exim4/allowed_senders

        hostlist acl_host_noavscan = net-iplsearch;/etc/exim4/host_noavscan

        acl_smtp_connect = acl_check_host
        acl_smtp_helo = acl_check_helo
        acl_smtp_mail = acl_check_sender
        acl_smtp_rcpt = acl_check_rcpt
        acl_smtp_data = acl_check_data
        acl_smtp_etrn = acl_check_etrn

        qualify_domain = %(domain)s
        trusted_users = mail
        message_size_limit = %(mailSize)s
        helo_allow_chars = _
        host_lookup = *
        smtp_enforce_sync = false 
        helo_accept_junk_hosts = *
        strip_excess_angle_brackets
        strip_trailing_dot
        delay_warning_condition = "\\
                ${if match{$h_precedence:}{(?i)bulk|list|junk}{no}{yes}}"
        #rfc1413_hosts = ${if eq{$interface_port}{SMTP_PORT} {*}{! *}}
        rfc1413_query_timeout = 0s
        sender_unqualified_hosts = %(hostlist)s
        recipient_unqualified_hosts = %(hostlist)s
        ignore_bounce_errors_after = 2d
        timeout_frozen_after = 7d
        recipients_max = 0
        # SSL/TLS cert and key
        tls_certificate = /etc/exim4/exim.cert
        tls_privatekey = /etc/exim4/exim.key
        # Advertise TLS to anyone
        tls_advertise_hosts = *
        smtp_etrn_command = /etc/exim4/etrn_script $domain

        LDAP_AUTH_CHECK_LOGIN = ${lookup ldap { \\
            user="${lookup ldapdn {user="cn=Manager,o=%(base)s" pass=%(pass)s ldap:///?dn?sub?(&(accountStatus=active)(mail=${quote_ldap:$1}))}}" \\
            pass="$2" ldap:///?mail?sub?(&(accountStatus=active)(mail=${quote_ldap:$1}))}{yes}{no}}
        
        LDAP_AUTH_CHECK_PLAIN = ${lookup ldap { \\
            user="${lookup ldapdn {user="cn=Manager,o=%(base)s" pass=%(pass)s ldap:///?dn?sub?(&(accountStatus=active)(mail=${quote_ldap:$2}))}}" \\
            pass="$3" ldap:///?mail?sub?(&(accountStatus=active)(mail=${quote_ldap:$2}))}{yes}{no}}
        

%(extra)s
        """ % {
            'ldap':         '127.0.0.1',
            'hostname':     hostname,
            'hostlist':     localNet,
            'serverhosts':  ' : '.join(serverhosts),
            'domain':       primaryDomain,
            'mailSize':     mailSize,
            'extra':        performanceTweak + mm_main,
            'systemFilter': systemFilter,
            'avScan':       avScan,
            'base':config.LDAPBase,
            'pass':config.LDAPPassword
        }

        eximACL="""
        ######################################################################
        #                       ACL CONFIGURATION                            #
        #         Specifies access control lists for incoming SMTP mail      #
        ######################################################################

        begin acl

        ######################################################################
        # Check connecting host (DNSBL's checked in acl_check_rcpt to ensure no reconnect attempt)
        ######################################################################
        acl_check_host:
            deny hosts        = +acl_host_blacklist
            accept

        ######################################################################
        # Check conencting host is not pretending to be the localhost
        ######################################################################
        acl_check_helo:

            accept hosts         = +relay_hosts
        # If the HELO pretend to be this host
            deny condition       = ${if or { \\
                                  {eq {${lc:$sender_helo_name}}{%(hostname)s}} \\
                                  {eq {${lc:$sender_helo_name}}{%(domain)s}} \\
                                  } {true}{false} }
            accept


        ######################################################################
        # Check sender address
        ######################################################################
        acl_check_sender:
            deny message      = sender envelope address $sender_address is locally blacklisted here.
                senders         = +acl_sender_blacklist

            accept


        ######################################################################
        # Check incoming messages
        ######################################################################
        acl_check_rcpt:

        # Accept if source is local SMTP
          accept hosts      = :
        # Deny if illegal characters in email address
          deny local_parts  = ^.*[@%%!/|] : ^\\\\.

%(ratelimit)s

        # Accept mail to postmaster at any local domain without any checks
          accept local_parts = postmaster
                domains    = +local_domains

%(senderRpFilter)s

        # Accept local, authenticated, whitelisted and dnswl'd hosts
          accept hosts      = +relay_hosts
          accept authenticated = *
          accept dnslists   = list.dnswl.org
          accept hosts      = +acl_host_whitelist
          accept domains    = +acl_domain_whitelist
          accept senders    = +acl_sender_whitelist

        # Deny if domain is locally blacklisted
          deny message        = rejected because $sender_domain is locally blacklisted here
                domains             = +acl_domain_blacklist

        # Deny if listed in a DNSBL
          deny message      = rejected because $sender_host_address is in a blacklist \\
                              at $dnslist_domain\\n$dnslist_text
            !senders        = :
            domains         = +local_domains : +relay_domains
            dnslists        = %(rbl)s

        # Accept if this is a local domain
          accept domains    = +local_domains
            endpass
            message         = unknown user
            verify          = recipient

        # Accept if this is a relay domain
          accept domains    = +relay_domains
            endpass
            message         = unrouteable address
            verify          = recipient

%(senderGreylist)s

        # Deny everything else
            deny message    = relay not permitted

        ######################################################################
        # Check contents of email
        ######################################################################
        acl_check_data:
%(dataGreylist)s

        # ClamAV virus scanning
            deny message      = Vulani has rejected this message because it contains a virus: ($malware_name) http://vulani.net
                log_message   = rejected VIRUS ($malware_name) from $sender_address to $recipients
                !hosts        = +acl_host_noavscan
                demime        = *
                malware       = */defer_ok

        # Reject messages that have serious MIME errors. This calls the demime
        # condition again, but will return cached results.
            deny message      = Vulani has rejected this message because it contains a broken MIME container ($demime_reason) http://vulani.net
                log_message   = rejected broken MIME container ($demime_reason) from $sender_address to $recipients
                condition     = ${if >{$demime_errorlevel}{2}{1}{0}}
                demime        = *

        # SpamAssassin Content Filtering
        # Include Spam Score in Header
            warn message      = X-Spam-Score: $spam_score\\n\\
                                X-Spam-Score-Int: $spam_score_int\\n\\
                                X-Spam-Bar: $spam_bar
                condition     = ${if <{$message_size}{250k}{1}{0}}
                !hosts        = +relay_hosts
                spam          = nobody:true/defer_ok

        # Reject spam messages with score over 7, using an extra condition.
            deny message      = Vulani has rejected this message because it scored $spam_score spam points and is considered to be unsolicited http://vulani.net
                log_message   = rejected SPAM score above threshhold in message from $sender_address to $recipients
                !hosts        = +acl_host_noavscan
                condition     = ${if >{$spam_score_int}{70}{1}{0}}
                spam          = nobody:true

%(extblock)s

            accept

        ######################################################################
        # Check ETRN requests
        ######################################################################
        acl_check_etrn:
            accept hosts = 0.0.0.0/0

        """ % {
            'rbl':              ' : '.join(RBL),        # DNS block lists
            'spamlow':          int(spamscore)-20,      # Warn spam score
            'spamhigh':         int(spamscore),         # Drop spam score.
            'senderGreylist':   aclCheckSenderGreylist, # Greylisting configuration
            'dataGreylist':     aclCheckDataGreylist,   #
            'extblock':         extensionBlock,         # Blocked file extensions
            'hostname':         hostname,
            'domain':       primaryDomain,
            'senderRpFilter': senderRpFilter,
            'ratelimit':    rateLimit,
            'avscan':       avscanacl
        }

        # Trigger our disclaimer transport 
        if config.Mail.get('disclaimer'):
            transport = "remote_smtp_filter"
        else:
            transport = "remote_smtp"

        # Set the external router depending on how the relay is set
        if config.SMTPRelay:
            externalRouter = """
        gateway:
            driver = manualroute
            domains = ! +local_domains
            route_list = * %s bydns
            transport = %s
           """ % (config.SMTPRelay, transport)
        else:
            externalRouter = """
        dnslookup:
            driver = dnslookup
            domains = ! +local_domains
            transport = %s
            ignore_target_hosts = 0.0.0.0 : 127.0.0.0/8
            no_more
            """ % transport

        eximRouters = """
        ######################################################################
        #                      ROUTERS CONFIGURATION                         #
        ######################################################################

        begin routers

        etrn_already:
            driver = accept
            transport = bsmtp_for_etrn
            require_files = /var/spool/mail/etrn/$domain
            domains = lsearch;/etc/exim/etrn_domains

        etrn_delay:
            driver = accept
            transport = bsmtp_for_etrn
            condition = ${if >{$message_age}{1800} {yes}{no}}
            domains = lsearch;/etc/exim/etrn_domains

        mail_reroute:
            driver = manualroute
            route_data = ${lookup{$local_part@$domain}lsearch{/etc/exim4/mail_reroute}}
            transport = remote_smtp

        branch_reroute:
            driver = manualroute
            route_data = ${lookup{$local_part@$domain}lsearch{/etc/exim4/branch_reroute}}
            transport = remote_smtp

        hubbed_hosts:
            driver = manualroute
            domains = ! +local_domains
            route_data = ${lookup{$domain}lsearch{/etc/exim/hubbed_hosts}}
            transport = remote_smtp

%(extro)s

        userforward:
            driver = redirect
            domains = +local_domains
            file = /var/spool/mail/forward/${local_part}@${domain}
            no_verify
            no_expn
            check_ancestor
            file_transport = address_file
            pipe_transport = address_pipe
            reply_transport = address_reply

        alias_user_vacation:
            driver = redirect
            domains = +local_domains
            allow_defer
            allow_fail
            data = ${lookup ldap {user="cn=Manager,o=%(ldapbase)s" pass=%(ldappass)s \\
                   ldap:///?mail?sub?(mailAlternateAddress=${local_part}@${domain})}}
            redirect_router = user_vacation
            retry_use_local_part

        user_vacation:
            driver = accept
            domains = +local_domains
            require_files = /var/spool/mail/vacation/${local_part}@${domain}.txt
            no_verify
            user = apache
            senders = !^.*-request@.* : !^owner-.*@.* : !^postmaster@.* : \\
                      ! ^listmaster@.* : !^mailer-daemon@.* : !^noreply@.* : \\
                      !^.*-bounces@.*
            transport = vacation_reply
            unseen

        ldap_aliases:
            driver = redirect
            domains = +local_domains
            allow_defer
            allow_fail
            data = ${lookup ldap {user="cn=Manager,o=%(ldapbase)s" pass=%(ldappass)s \\
                   ldap:///?mail?sub?(mailAlternateAddress=${local_part}@${domain})}}
            redirect_router = ldap_forward
            retry_use_local_part

        ldap_forward:
            driver = redirect
            domains = +local_domains
            allow_defer
            allow_fail
            data = ${lookup ldap {user="cn=Manager,o=%(ldapbase)s" pass=%(ldappass)s \\
                    ldap:///?mailForwardingAddress?sub?\\
                    (&(accountStatus=active)(mail=${local_part}@${domain}))}{$value}fail}
            no_expn
            retry_use_local_part
            no_verify

        ldap_user:
            driver = accept
            domains = +local_domains
            condition =   ${if eq {}{${lookup ldap {user="cn=Manager,o=%(ldapbase)s" pass=%(ldappass)s \\
                          ldap:///?mail?sub?(&(accountStatus=active)(mail=${local_part}@${domain}))}}}{no}{yes}}
            group = users
            retry_use_local_part
            transport = local_delivery

        catchall:
            domains = lsearch;/etc/exim/catchall_domains
            driver = redirect
            data = catchall@${domain}

%(router)s

        #localuser:
        #    driver = accept
        #    domains = +local_domains
        #    check_local_user
        #    transport = local_delivery
        """ % {
            'router': mm_router,
            'ldapbase': config.LDAPBase,
            'ldappass': config.LDAPPassword,
            'extro': externalRouter,
        }

        ## Prevent bounce of failed hosts? (Maximum send timeout reached)
        hostfailBounce = ""
        if config.Mail.get('hostfailbounce', False):
            hostfailBounce += "    delay_after_cutoff = false\n"

        if config.Mail.get('smtpinterface'):
            hostfailBounce += "    interface = %s\n" % config.Mail.get('smtpinterface')

        eximTransports = """
        ######################################################################
        #                      TRANSPORTS CONFIGURATION                      #
        ######################################################################

        begin transports

        bsmtp_for_etrn:
            driver=appendfile
            file=/var/spool/mail/etrn/$domain
            user=mail
            batch_max=1000
            use_bsmtp

        vacation_reply:
            debug_print = "T: vacation_reply for $local_part@$domain"
            driver = autoreply
            file = /var/spool/mail/vacation/${local_part}@${domain}.txt
            file_expand
            log = /var/spool/mail/vacation/${local_part}@${domain}.log
            once_repeat = 7d
            once = /var/spool/mail/vacation/${local_part}@${domain}.db
            from = ${local_part}@${domain}
            to = $sender_address
            subject = "Re: $h_subject"
            text = "\\
            This is an automated response for $local_part@${domain}:\\n\\
            ====================================================\\n\\n"

        remote_smtp:
            driver = smtp
            %(iface)s

        remote_smtp_filter:
            driver = smtp
            transport_filter = /usr/local/tcs/tums/bin/remime
            %(iface)s

        local_delivery:
            driver = appendfile
            create_directory
            delivery_date_add
            directory = ${lookup ldap {user="cn=Manager,o=%(basedn)s" pass=%(wpass)s \\
                        ldap:///?mailMessageStore?sub?(&(accountStatus=active)\\
                        (mail=${local_part}@${domain}))}}
            directory_mode = 770
            envelope_to_add
            group = mail
            maildir_format
            mode = 660
            return_path_add
            user = mail

        address_pipe:
            driver = pipe
            return_output

        address_file:
            driver = appendfile
            delivery_date_add
            envelope_to_add
            return_path_add

        address_reply:
            driver = autoreply

        %(mm)s\n""" % {
            'iface': hostfailBounce, 
            'basedn': config.LDAPBase, 
            'wpass': config.LDAPPassword, 
            'mm': mm_transport
        }

        eximOther = """
        ######################################################################
        #                      RETRY CONFIGURATION                           #
        ######################################################################

        begin retry
        *        *   senders=:      F,2m,1m
        *        *                  F,2h,15m; G,16h,1h,1.5; F,7d,4h

        ######################################################################
        #                      REWRITE CONFIGURATION                         #
        ######################################################################

        begin rewrite
%(rewrite)s
        ######################################################################
        #                   AUTHENTICATION CONFIGURATION                     #
        ######################################################################

        begin authenticators

        login:
            driver = plaintext
            public_name = LOGIN
            server_prompts = "Username:: : Password::"
            server_advertise_condition = yes
            server_condition = ${if match_ip{$sender_host_address}{+relay_hosts}{yes}{LDAP_AUTH_CHECK_LOGIN}}
            server_set_id = $1
        plain:
            driver = plaintext
            public_name = PLAIN
            server_prompts = :
            server_advertise_condition = yes
            server_condition = ${if match_ip{$sender_host_address}{+relay_hosts}{yes}{LDAP_AUTH_CHECK_PLAIN}}
            server_set_id = $2 
        """ % {
            'base':config.LDAPBase,
            'pass':config.LDAPPassword,
            'rewrite': rewriteRules
        }

        confFile = eximMain + eximACL + eximRouters + eximTransports + eximOther
        os.system('mkdir -p /var/spool/mail/forward/')
        os.system('mkdir -p /var/spool/mail/etrn/')

        # Reprocess the config file
        lp = confFile.split('\n')
        confFile = ""
        for i in lp:
            confFile += i[8:] + '\n'

        confFile = confFile.replace('/etc/exim/', '/etc/exim4/').replace('apache', 'www-data')
        # Patches user names
        confFile = confFile.replace('user=mail', 'user=Debian-exim')
        Utils.writeConf('/etc/exim4/exim4.conf', confFile, '#')
        os.system('chmod a+r /etc/exim4/*')
        os.system('chmod -R a+r /usr/local/tcs/tums/data')
        os.system('chmod a+x /etc/exim4/etrn_script >/dev/null 2>&1')
        os.system('chmod a+rx /var/mail/vacation >/dev/null 2>&1')
        os.system('chown Debian-exim:Debian-exim /var/spool/mail/etrn')
        os.system('mkdir /var/cache/vulani/ >/dev/null 2>&1')

        ### Mailname
        mailname = "%s.%s\n" % ( config.Hostname, config.Domain )
        l = open('/etc/mailname', 'wt')
        l.write(mailname)
        l.close()

