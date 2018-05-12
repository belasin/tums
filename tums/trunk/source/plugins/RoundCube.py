import config, os
from Core import Utils


class Plugin(object):
    parameterHook = "--webmail"
    parameterDescription = "Reconfigure Roundcube webmail"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "",
    ]

    def reloadServices(self):
        # Doesn't have anything to reload
        pass

    def writeConfig(self, *a):
        configHunk = """<?php
$rcmail_config = array();
$rcmail_config['debug_level'] = 1;
$rcmail_config['enable_caching'] = FALSE;
$rcmail_config['message_cache_lifetime'] = '2m';
$rcmail_config['auto_create_user'] = TRUE;
$rcmail_config['default_host'] = '127.0.0.1';
$rcmail_config['default_port'] = 143;
$rcmail_config['username_domain'] = '';
$rcmail_config['mail_domain'] = '%s';
$rcmail_config['virtuser_file'] = '';
$rcmail_config['virtuser_query'] = '';
$rcmail_config['smtp_server'] = '127.0.0.1';
$rcmail_config['smtp_port'] = 25;
$rcmail_config['smtp_user'] = '';
$rcmail_config['smtp_pass'] = '';
$rcmail_config['smtp_auth_type'] = '';
$rcmail_config['smtp_log'] = TRUE;
$rcmail_config['list_cols'] = array('subject', 'from', 'date', 'size');
$rcmail_config['skin_path'] = 'skins/thusa/';
$rcmail_config['temp_dir'] = 'temp/';
$rcmail_config['log_dir'] = 'logs/';
$rcmail_config['session_lifetime'] = 10;
$rcmail_config['ip_check'] = FALSE;
$rcmail_config['des_key'] = 'rcmail-!24ByteDESkey*Str';
$rcmail_config['locale_string'] = 'en';
$rcmail_config['date_short'] = 'D H:i';
$rcmail_config['date_long'] = 'd.m.Y H:i';
$rcmail_config['useragent'] = 'Vulani Web Access';
$rcmail_config['product_name'] = 'Vulani Web Access';
$rcmail_config['imap_root'] = '';
$rcmail_config['drafts_mbox'] = 'Drafts';
$rcmail_config['junk_mbox'] = 'Junk';
$rcmail_config['sent_mbox'] = 'Sent';
$rcmail_config['trash_mbox'] = 'Trash';
$rcmail_config['default_imap_folders'] = array('INBOX', 'Drafts', 'Sent', 'Junk', 'Trash');
$rcmail_config['protect_default_folders'] = TRUE;
$rcmail_config['skip_deleted'] = FALSE;
$rcmail_config['read_when_deleted'] = TRUE;
$rcmail_config['flag_for_deletion'] = TRUE;
$rcmail_config['enable_spellcheck'] = TRUE;
$rcmail_config['generic_message_footer'] = '';
$rcmail_config['mail_header_delimiter'] = NULL;
$rcmail_config['include_host_config'] = FALSE;
$rcmail_config['pagesize'] = 40;
$rcmail_config['timezone'] = 1;
$rcmail_config['dst_active'] = TRUE;
$rcmail_config['prefer_html'] = TRUE;
$rcmail_config['prettydate'] = TRUE;
$rcmail_config['message_sort_col'] = 'date';
$rcmail_config['message_sort_order'] = 'DESC';
$rcmail_config['javascript_config'] = array('read_when_deleted', 'flag_for_deletion');
?>
""" % config.Domain
        
        l = open('/var/www/localhost/htdocs/mail/config/main.inc.php', 'wt')
        l.write(configHunk)
        l.close()

        os.system('mysqladmin create roundcube > /dev/null 2>&1')
        os.system('mysql roundcube < /var/www/localhost/htdocs/mail/SQL/mysql5.initial.sql > /dev/null 2>&1')
        os.system('mysqladmin create roundcube -u root --password=thusa123 > /dev/null 2>&1')
        os.system('mysql roundcube -u root --password=thusa123 < /var/www/localhost/htdocs/mail/SQL/mysql5.initial.sql > /dev/null 2>&1')

