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
        os.system('/etc/init.d/exim restart')

    def writeConfig(self, *a):
        if os.path.exists('/etc/debian_version'):
            debianPath = True
        else:
            debianPath = False

        locals = "\n".join(config.LocalDomains)
        relays = "\n".join(config.Mail.get('relay', []))
        hubs = "\n".join(["%s        %s        byname" % (i,j) for i,j in config.Mail.get('hubbed', [])])
        blacklists = "\n".join(config.Mail.get('blacklist', []))

        whitelistAddr = ""
        whitelistHost = ""
        for w in config.Mail.get('whitelist', []):
            if "@" in w:
                whitelistAddr += w + "\n"
            else:
                whitelistHost += w + "\n"

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

        if debianPath:
            Utils.writeConf('/etc/exim4/local_sender_whitelist', whitelistAddr, '#')
            Utils.writeConf('/etc/exim4/local_host_whitelist', whitelistHost, '#')
            Utils.writeConf('/etc/exim4/local_sender_blacklist', blacklists, '#')
            Utils.writeConf('/etc/exim4/local_domains', locals, '#')
            Utils.writeConf('/etc/exim4/relay_domains', relays, '#')
            Utils.writeConf('/etc/exim4/hubbed_hosts', hubs, '#')
            Utils.writeConf('/etc/exim4/system_filter', copyTo, '#')
            # Get rid of the autogenerated tag so aptitude doesn't break us
            os.system('rm /var/lib/exim4/config.autogenerated')
            systemFilter = "system_filter = /etc/exim4/system_filter\n"
        else:
            Utils.writeConf('/etc/exim/local_domains', locals, '#')
            Utils.writeConf('/etc/exim/relay_domains', relays, '#')
            Utils.writeConf('/etc/exim/hubbed_hosts', hubs, '#')
            Utils.writeConf('/etc/exim/local_sender_whitelist', whitelistAddr, '#')
            Utils.writeConf('/etc/exim/local_host_whitelist', whitelistHost, '#')
            Utils.writeConf('/etc/exim/local_sender_blacklist', blacklists, '#')
            Utils.writeConf('/etc/exim/system_filter', copyTo, '#')
            systemFilter = "system_filter = /etc/exim/system_filter\n"
 
        primaryDomain = config.Domain
        hostname = config.Hostname + '.' + config.Domain
        mailSize = config.Mail.get('mailsize', '')
        localNet = config.EthernetDevices[config.LANPrimary]['network']
        if not localNet: #somehow it isn't set ??
            # use the ip...
            ip = config.EthernetDevices[config.LANPrimary]['ip']
            cidr = ip.split('/')[-1]
            host = '.'.join(ip.split('.')[:3])
            net = '%s.0/%s' % (host, cidr)
            # For CIDR's which are not a whole class A, B or C this method is broken...
            localNet = ip

        # Accept mail on our IPv6 prefix
        if config.EthernetDevices[config.LANPrimary].get('ipv6', False):
            localNet += ' : %s ' % config.EthernetDevices[config.LANPrimary]['ipv6'].replace(':', '::')

        # fill in allowed hosts.
        if config.Mail.get('relay-from'):
            localNet += ' : ' + ' : '.join(config.Mail['relay-from'])
        extensionBlock = ""

        if config.Mail.get('blockedfiles', []):
            extensionBlock = "deny  message     = We do not accept \".$found_extension\" attachments here.\n"
            extensionBlock += "        demime      = %s\n" % ':'.join(config.Mail['blockedfiles'])

        mm_router = ""
        mm_transport = ""
        mm_main = ""
        if config.Mail.get('mailman'):
            mm_router = """mailman_router:
 domains = +local_domains
 driver = accept
 require_files = MAILMAN_HOME/lists/$local_part/config.pck
 local_part_suffix_optional
 local_part_suffix = -bounces : -bounces+* : \
 -confirm+* : -join : -leave : \
 -owner : -request : -admin
 transport = mailman_transport\n\n"""
            mm_transport = """mailman_transport:
 driver = pipe
 command = MAILMAN_WRAP \
 '${if def:local_part_suffix \
 {${sg{$local_part_suffix}{-(\\w+)(\\+.*)?}{\$1}}} \
 {post}}' \
 $local_part
 current_directory = MAILMAN_HOME
 home_directory = MAILMAN_HOME
 user = MAILMAN_USER
 group = MAILMAN_GROUP\n\n"""
            mm_main = """MAILMAN_HOME=/var/lib/mailman
MAILMAN_WRAP=MAILMAN_HOME/mail/mailman
MAILMAN_USER=list
MAILMAN_GROUP=list\n
"""
        spamscore = config.Mail.get('spamscore', 70)
        greylist1 = ""
        greylist2 = ""

        if config.Mail.get('greylisting', True):
            greylist1 = """  # Greylist incomming
  defer
    message        = $sender_host_address is not yet authorized to deliver \\
                     mail from <$sender_address> to <$local_part@$domain>. \\
                     Please try later.
    log_message    = greylisted.
    !senders       = :
    !hosts         = : +relay_from_hosts : \\
                     ${if exists {/etc/greylistd/whitelist-hosts}\\
                                 {/etc/greylistd/whitelist-hosts}{}} : \\
                     ${if exists {/var/lib/greylistd/whitelist-hosts}\\
                                 {/var/lib/greylistd/whitelist-hosts}{}}
    !authenticated = *
    !acl           = acl_whitelist_local_deny
    domains        = +local_domains : +relay_to_domains
    verify         = recipient/callout=20s,use_sender,defer_ok
    condition      = ${readsocket{/var/run/greylistd/socket}\\
                                 {--grey \\
                                  $sender_host_address \\
                                  $sender_address \\
                                  $local_part@$domain}\\
                                 {5s}{}{false}}

 # Deny if blacklisted by greylist
 deny
   message = $sender_host_address is blacklisted from delivering \\
                     mail from <$sender_address> to <$local_part@$domain>.
   log_message = blacklisted.
   !senders        = :
   !authenticated = *
   verify         = recipient/callout=20s,use_sender,defer_ok
   condition      = ${readsocket{/var/run/greylistd/socket}\\
                                 {--black \\
                                  $sender_host_address \\
                                  $sender_address \\
                                  $local_part@$domain}\\
                                 {5s}{}{false}}\n"""
            greylist2 = """  defer
    message        = $sender_host_address is not yet authorized to deliver \\
                     mail from <$sender_address> to <$recipients>. \\
                     Please try later.
    log_message    = greylisted.
    senders        = :
    !hosts         = : +relay_from_hosts : \\
                     ${if exists {/etc/greylistd/whitelist-hosts}\\
                                 {/etc/greylistd/whitelist-hosts}{}} : \\
                     ${if exists {/var/lib/greylistd/whitelist-hosts}\\
                                 {/var/lib/greylistd/whitelist-hosts}{}}
    !authenticated = *
    !acl           = acl_whitelist_local_deny
    condition      = ${readsocket{/var/run/greylistd/socket}\\
                                 {--grey \\
                                  $sender_host_address \\
                                  $recipients}\\
                                  {5s}{}{false}}

 deny
   message = $sender_host_address is blacklisted from delivering \\
                     mail from <$sender_address> to <$recipients>.
   log_message = blacklisted.
   !senders        = :
   !authenticated = *
   condition      = ${readsocket{/var/run/greylistd/socket}\\
                                 {--black \\
                                  $sender_host_address \\
                                  $recipients}\\
                                  {5s}{}{false}}\n"""


        eximMain = """######################################################################
#                    MAIN CONFIGURATION SETTINGS                     #
######################################################################

ldap_default_servers = 127.0.0.1
primary_hostname = %s
domainlist local_domains = @ : lsearch;/etc/exim/local_domains
domainlist relay_to_domains = lsearch;/etc/exim/relay_domains
hostlist   relay_from_hosts = 127.0.0.1 : %s
domainlist rbl_domain_whitelist = lsearch;/etc/exim/rbl_domain_whitelist
hostlist rbl_ip_whitelist = net-iplsearch;/etc/exim/rbl_ip_whitelist
addresslist rbl_sender_whitelist = lsearch*@;/etc/exim/rbl_sender_whitelist
acl_smtp_rcpt = acl_check_rcpt
acl_smtp_data = check_message
av_scanner = clamd:/var/run/clamav/clamd.sock
spamd_address = 127.0.0.1 783
%s
qualify_domain = %s
trusted_users = mail
message_size_limit = %s
helo_allow_chars = _
host_lookup = *
smtp_enforce_sync = false
helo_accept_junk_hosts = *
strip_excess_angle_brackets
strip_trailing_dot
delay_warning_condition = "\\
        ${if match{$h_precedence:}{(?i)bulk|list|junk}{no}{yes}}"
rfc1413_hosts = ${if eq{$interface_port}{SMTP_PORT} {*}{! *}}
rfc1413_query_timeout = 30s
sender_unqualified_hosts = %s
recipient_unqualified_hosts = %s
ignore_bounce_errors_after = 2d
timeout_frozen_after = 7d
# SSL/TLS cert and key
tls_certificate = /etc/exim/exim.cert
tls_privatekey = /etc/exim/exim.key
# Advertise TLS to anyone
tls_advertise_hosts = *
smtp_etrn_command = /etc/exim/etrn_script $domain
acl_smtp_etrn = acl_check_etrn
%s
""" % (hostname, localNet, systemFilter, primaryDomain, mailSize, localNet, localNet, mm_main)

        eximACL="""######################################################################
#                       ACL CONFIGURATION                            #
#         Specifies access control lists for incoming SMTP mail      #
######################################################################

begin acl

acl_whitelist_local_deny:
  accept
    hosts = ${if exists{CONFDIR/local_host_whitelist}\
                 {CONFDIR/local_host_whitelist}\
                 {}}
  accept
    senders = ${if exists{CONFDIR/local_sender_whitelist}\
                   {CONFDIR/local_sender_whitelist}\
                   {}}

  # This hook allows you to hook in your own ACLs without having to
  # modify this file. If you do it like we suggest, you'll end up with
  # a small performance penalty since there is an additional file being
  # accessed. This doesn't happen if you leave the macro unset.
  .ifdef WHITELIST_LOCAL_DENY_LOCAL_ACL_FILE
  .include WHITELIST_LOCAL_DENY_LOCAL_ACL_FILE
  .endif

check_message:

   accept condition = ${lookup{$sender_host_address}lsearch{/etc/exim/host_noscan_from}{1}{0}}
   deny message = This message contains a virus ($malware_name)
        condition = ${lookup{$sender_host_address}lsearch{/etc/exim/host_av_noscan_from}{0}{1}}
        demime = *
        malware = *

   deny message = This message contains a broken MIME container ($demime_reason).
        condition=${if >{$demime_errorlevel}{2}{1}{0}}
        condition=${lookup{$sender_host_address}lsearch{/etc/exim/host_demime_noscan_from}{0}{1}}
        demime = *

  warn  message = X-Spam-Score: $spam_score ($spam_bar)
        condition = ${if <{$message_size}{80k}{1}{0}}
        spam = nobody:true

  warn  message = X-Spam-Report: $spam_report
        condition = ${if <{$message_size}{80k}{1}{0}}
        spam = nobody:true

  # Add X-Spam-Flag if spam is over system-wide threshold
  warn message = X-Spam-Flag: YES
        condition = ${if <{$message_size}{80k}{1}{0}}
        spam = nobody

  # Reject spam messages with score over 7, using an extra condition.
  deny  message = This message scored $spam_score spam points and is considered to be unsolicited. Rejected.
        condition = ${if <{$message_size}{80k}{1}{0}}
        spam = nobody:true
        condition = ${if >{$spam_score_int}{%s}{1}{0}}

  %s
  accept

acl_check_rcpt:
  # Blacklist
  deny message = sender envelope address $sender_address is locally blacklisted here. See http://www.sput.nl/spam/
    !acl    = acl_whitelist_local_deny
    hosts   = !+relay_from_hosts
    senders = ${if exists{CONFDIR/local_sender_blacklist}\\
                         {CONFDIR/local_sender_blacklist}\\
               {}}
%s

  accept  hosts = :

  deny    local_parts   = ^.*[@%%!/|]

  accept  local_parts   = postmaster
          domains       = +local_domains

  require verify        = sender

  deny message = rejected because $sender_host_address is in a blacklist at $dnslist_domain\\n$dnslist_text
     !authenticated = *
     !domains = +rbl_domain_whitelist
     !hosts = +rbl_ip_whitelist
     !senders = +rbl_sender_whitelist
     dnslists = sbl-xbl.spamhaus.org : \\
     list.dsbl.org : \\
     web.dnsbl.sorbs.net : \\
     zombie.dnsbl.sorbs.net : \\
     nomail.rhsbl.sorbs.net : \\
     combined.njabl.org

  accept  domains       = +local_domains
          endpass
          message       = unknown user
          verify        = recipient

  accept  domains       = +relay_to_domains
          endpass
          message       = unrouteable address
          verify        = recipient

  accept  hosts         = +relay_from_hosts
  accept  authenticated = *

  deny    message       = relay not permitted

acl_check_data:
%s
 accept

acl_check_etrn:

 accept hosts = 0.0.0.0/0
""" % (spamscore, extensionBlock, greylist1, greylist2)

        # Set the external router depending on how the relay is set
        if config.SMTPRelay:
            externalRouter = """gateway:
  driver = manualroute
  domains = ! +local_domains
  route_list = * %s bydns
  transport = remote_smtp\n""" % config.SMTPRelay
        else:
            externalRouter = """dnslookup:
  driver = dnslookup
  domains = ! +local_domains
  transport = remote_smtp
  ignore_target_hosts = 0.0.0.0 : 127.0.0.0/8
  no_more\n"""

        eximRouters = """######################################################################
#                      ROUTERS CONFIGURATION                         #
######################################################################

begin routers

%s
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

hubbed_hosts:
  driver = manualroute
  domains = ! +local_domains
  route_data = ${lookup{$domain}lsearch{/etc/exim/hubbed_hosts}}
  transport = remote_smtp

userforward:
 driver = redirect
 file = /var/spool/mail/forward/${local_part}@${domain}
 no_verify
 no_expn
 check_ancestor
 file_transport = address_file
 pipe_transport = address_pipe
 reply_transport = address_reply

user_vacation:
 driver = accept
 require_files = /var/spool/mail/vacation/${local_part}@${domain}.txt
 no_verify
 user = apache
 senders = !^.*-request@.* : !^owner-.*@.* : !^postmaster@.* : \\
            ! ^listmaster@.* : !^mailer-daemon@.*
 transport = vacation_reply
 unseen

ldap_aliases:
  driver = redirect
  allow_defer
  allow_fail
  data = ${lookup ldap {user="cn=Manager,o=%s" pass=%s \\
         ldap:///?mail?sub?(mailAlternateAddress=${local_part}@${domain})}}
  redirect_router = ldap_forward
  retry_use_local_part

ldap_forward:
  driver = redirect
  allow_defer
  allow_fail
  data = ${lookup ldap {user="cn=Manager,o=%s" pass=%s \\
         ldap:///?mailForwardingAddress?sub?\\
         (&(accountStatus=active)(mail=${local_part}@${domain}))}{$value}fail}
  no_expn
  retry_use_local_part
  no_verify

ldap_user:
  driver = accept
  condition =   ${if eq {}{${lookup ldap {user="cn=Manager,o=%s" pass=%s \\
                ldap:///?mail?sub?(&(accountStatus=active)(mail=${local_part}@${domain}))}}}{no}{yes}}
  group = users
  retry_use_local_part
  transport = local_delivery

%s

localuser:
  driver = accept
  check_local_user
  transport = local_delivery

""" % (
        mm_router,
        config.LDAPBase,
        config.LDAPPassword,
        config.LDAPBase,
        config.LDAPPassword,
        config.LDAPBase,
        config.LDAPPassword,
        externalRouter,
    )

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
 from = postmaster@${domain}
 to = $sender_address
 subject = "Re: $h_subject"
 text = "\\
 Dear $h_from:\\n\\n\\
 This is an automatic reply. Feel free to send additional\\n\\
 mail, as only this one notice will be generated. The following\\n\\
 is a prerecorded message, sent for $local_part@${domain}:\\n\\
 ====================================================\\n\\n\\
 "

remote_smtp:
  driver = smtp
local_delivery:
  driver = appendfile
  create_directory
  delivery_date_add
  directory = ${lookup ldap {user="cn=Manager,o=%s" pass=%s \\
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

%s
""" % (config.LDAPBase, config.LDAPPassword, mm_transport)

        eximOther = """######################################################################
#                      RETRY CONFIGURATION                           #
######################################################################

begin retry
*                      *           F,2h,15m; G,16h,1h,1.5; F,4d,6h

######################################################################
#                      REWRITE CONFIGURATION                         #
######################################################################

begin rewrite

######################################################################
#                   AUTHENTICATION CONFIGURATION                     #
######################################################################

begin authenticators

login:
    driver = plaintext
    public_name = LOGIN
    server_prompts = "Username:: : Password::"
    server_advertise_condition = yes
    server_condition = \\
        ${\\
        lookup ldap { \\
        user="${lookup ldapdn {user="cn=Manager,o=%s" pass=%s \\
        ldap:///?dn?sub?(&(accountStatus=active)(mail=${quote_ldap:$1}))}}" \\
        pass="$2" \\
        ldap:///?mail?sub?(&(accountStatus=active)(mail=${quote_ldap:$1})) \\
        }{yes}fail \\
        }
    server_set_id = $1
plain:
    driver = plaintext
    public_name = PLAIN
    server_prompts = :
    server_advertise_condition = yes
    server_condition = \\
        ${\\
        lookup ldap { \\
        user="${lookup ldapdn {user="cn=Manager,o=%s" pass=%s \\
        ldap:///?dn?sub?(&(accountStatus=active)(mail=${quote_ldap:$2}))}}" \\
        pass="$3" \\
        ldap:///?mail?sub?(&(accountStatus=active)(mail=${quote_ldap:$2})) \\
        }{yes}fail \\
        }
    server_set_id = $2
""" % ( 
        config.LDAPBase,
        config.LDAPPassword,
        config.LDAPBase,
        config.LDAPPassword,
    )
        confFile = eximMain + eximACL + eximRouters + eximTransports + eximOther
        os.system('mkdir -p /var/spool/mail/forward/')
        if debianPath:
            confFile = confFile.replace('/etc/exim/', '/etc/exim4/').replace('apache', 'www-data')
            Utils.writeConf('/etc/exim4/exim4.conf', confFile, '#')
        else:
            Utils.writeConf('/etc/exim/exim.conf', confFile, '#')


