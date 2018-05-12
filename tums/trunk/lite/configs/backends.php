<?php
/**
 * $Horde: passwd/config/backends.php.dist,v 1.14.2.3 2003/02/05 15:48:13 ericr Exp $
 *
 * This file is where you specify what backends people use to
 * change their passwords. There are a number of properties
 * that you can set for each backend:
 *
 * name: This is the plaintext, english name that you want displayed
 *       to people if you are using the drop down server list.  Also
 *       displayed on the main page (input form).
 *
 * password policy: The password policies for this backend. You are responsible
 *                  for the sanity checks of these options. Options are:
 *              minLength   Minimum length of the password
 *              maxLength   Maximum length of the password
 *              maxSpace    Maximum number of white space characters
 *              minUpper    Minimum number of uppercase characters
 *              minLower    Minimum number of lowercase characters
 *              minNumeric  Minimum number of numeric characters (0-9)
 *              minAlphaNum Minimum number of alphanumeric characters
 *              minAlpha    Minimum number of alphabetic characters
 *
 * driver:    The Passwd driver used to change the password. Valid
 *            Valid values are currently:
 *              ldap         Change the password on a ldap server
 *              sql          Change the password for sql authentication
 *                           (exim, pam_mysql, horde)
 *              poppassd     Change the password via a poppassd server
 *              smbpasswd    Change the password via the smbpasswd command
 *              expect       Change the password via an expect script
 *              vmailmgr     Change the password via a local vmailmgr daemon
 *              vpopmail     Change the password for sql based vpopmail
 *              servuftp     Change the password via a servuftp server
 *
 * params:    A params array containing any additional information that the
 *            Passwd driver needs
 *
 *            The following is a list of supported encryption/hashing methods
 *            supported by passwd
 *
 *            1) plain
 *            2) crypt
 *            3) md5-hex
 *            4) md5-base64
 *            5) smd5
 *            6) sha
 *            7) ssha
 *
 *            Currently, md5-base64, smd5, sha, and ssha require the mhash php
 *            library in order to work properly.  See the INSTALL file for
 *            directions on enabling this.  md5 passwords have caused some 
 *            problems in the past because there are different definitions of 
 *            what is a "md5 password".  Systems implement them in a different 
 *            manner.  If you are using OpenLDAP as your backend or have 
 *            migrated your passwords from your OS based passwd file, you will 
 *            need to use the md5-base64 hashing method.  If you are using a
 *            SQL database or used the PHP md5() method to create your
 *            passwords, you will need to use the md5-hex hashing method.   
 *
 * preferred: This is only useful if you want to use the same backend.php
 *            file for different machines: if the Hostname of the Passwd
 *            Machine is identical to one of those in the preferred list,
 *            then the corresponding option in the select box will include
 *            SELECTED, i.e. it is selected per default. Otherwise the
 *            first entry in the list is selected.
 */

$backends['ldap'] = array(
    'name' => 'LDAP',
    'preferred' => 'mail.bpexample.com',
    'password policy' => array(
        'minLength' => 1,
        'maxLength' => 12
    ),
    'driver' => 'ldap',
    'params' => array(
        'host' => 'localhost',
        'port' => 389,
        'basedn' => 'o=BPEXAMPLE',
        'uid' => 'mail',
        'realm' => '', 
        'encryption' => 'sha'
    )
);
