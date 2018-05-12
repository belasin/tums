<?php
/*
 * $Horde: turba/config/sources.php.dist,v 1.22.2.21 2004/02/23 16:47:14 chuck Exp $
 *
 * This file is where you specify the sources of contacts available to
 * users at your installation. There are a number of properties that you
 * can set for each server, including:
 *
 * title: This is the common (user-visible) name that you want displayed
 * in the contact source drop-down box.
 *
 * type: The types 'ldap', 'sql' and 'prefs' are currently supported.
 *
 * params: These are the connection parameters specific to the contact
 * source. See below for examples of how to set these.
 *
 * map: This is a list of mappings from the standard Turba attribute
 * names (on the left) to the attribute names by which they are known in
 * this contact source (on the right).
 *
 * search: A list of Turba attribute names that can be searched for
 * this source.
 *
 * strict: A list of native field/attribute names that must always be
 * matched exactly in a search.
 *
 * public: If set to true, this source will be available to all users.
 * See also 'readonly' -- public=true readonly=false means writable
 * by all users!
 *
 * readonly: If set to true, this source can only be modified by users
 * on the 'admin' list.
 *
 * admin: A list (array) of users that are allowed to modify this source,
 * if it's marked 'readonly'.
 *
 * export: If set to true, this source will appear on the Export menu,
 * allowing users to export the contacts to a CSV (etc.) file.
 *
 * encoding: Some LDAP servers use UTF8 for encoding. See below for
 * examples.
 *
 * Here are some example configurations:
 */

/*
 * Public netcenter and bigfoot addressbooks.
$cfgSources['netcenter'] = array(
    'title' => 'Netcenter Member Directory',
    'type' => 'ldap',
    'params' => array(
        'server' => 'memberdir.netscape.com',
        'port' => 389,
        'root' => 'ou=member_directory,o=netcenter.com',
        'dn' => array('cn'),
        'objectclass' => 'person',
        'filter' => ''
    ),
    'map' => array(
        '__key' => 'dn',
        'name' => 'cn',
        'email' => 'mail',
        'alias' => 'givenname'
    ),
    'search' => array(
        'name',
        'email',
        'alias'
    ),
    'strict' => array(
        'dn'
    ),
    'public' => true,
    'readonly' => true,
    'export' => false
);

$cfgSources['bigfoot'] = array(
    'title' => 'Bigfoot',
    'type' => 'ldap',
    'params' => array(
        'server' => 'ldap.bigfoot.com',
        'port' => 389,
        'root' => ''
    ),
    'map' => array(
        '__key' => 'dn',
        'name' => 'cn',
        'email' => 'mail',
        'alias' => 'givenname'
    ),
    'search' => array(
        'name',
        'email',
        'alias'
    ),
    'strict' => array(
        'dn'
    ),
    'public' => true,
    'readonly' => true,
    'export' => false
);

$cfgSources['verisign'] = array(
    'title' => 'Verisign Directory',
    'type' => 'ldap',
    'params' => array(
        'server' => 'directory.verisign.com',
        'port' => 389,
        'root' => '',
    ),
    'map' => array(
        '__key' => 'dn',
        'name' => 'cn',
        'email' => 'mail',
    ),
    'search' => array(
        'name',
        'email'
    ),
    'strict' => array(
        'dn'
    ),
    'public' => true,
    'readonly' => true,
    'export' => false
);
 */

/**
 * A local address book in an SQL database. This implements a per-user
 * address book.
 *
 * Be sure to create a turba_objects table in your Horde database
 * from the schema in turba/scripts/drivers/turba.sql if you use
 * this source.
 */
$cfgSources['localsql'] = array(
    'title' => 'My Addressbook',
    'type' => 'sql',
    'params' => array(
        'phptype' => 'mysql',
        'hostspec' => 'localhost',
        'username' => 'horde',
        'password' => 'hrd12',
        'database' => 'horde',
        'table' => 'turba_objects'
    ),
    'map' => array(
        '__key' => 'object_id',
        '__owner' => 'owner_id',
        '__type' => 'object_type',
        '__members' => 'object_members',
        'name' => 'object_name',
        'email' => 'object_email',
        'homeAddress' => 'object_homeaddress',
        'workAddress' => 'object_workaddress',
        'homePhone' => 'object_homephone',
        'workPhone' => 'object_workphone',
        'cellPhone' => 'object_cellphone',
        'fax' => 'object_fax',
        'title' => 'object_title',
        'company' => 'object_company',
        'notes' => 'object_notes'
    ),
    'search' => array(
        'name',
        'email'
    ),
    'strict' => array(
        'object_id'
    ),
    'public' => false,
    'readonly' => false,
    'admin' => array(),
    'export' => true
);

/**
 * A local address book in an LDAP directory. This implements a public
 * (shared) address book.
$cfgSources['localldap'] = array(
    'title' => 'Shared Directory',
    'type' => 'ldap',
    'params' => array(
        'server' => 'ldap.example.com',
        'port' => 389,
        'root' => 'dc=example,dc=com',
        'bind_dn' => 'cn=admin,ou=users,dc=example,dc=com',
        'bind_password' => '********',
        'dn' => array('cn'),
        'objectclass' => 'person',
        'version' => 3
    ),
    'map' => array(
        '__key' => 'dn',
        'name' => 'cn',
        'email' => 'mail',
        'homePhone' => 'homephone',
        'workPhone' => 'telephonenumber',
        'cellPhone' => 'mobiletelephonenumber',
        'homeAddress' => 'homepostaladdress'
    ),
    'search' => array(
        'name',
        'email',
        'homePhone',
        'workPhone',
        'cellPhone',
        'homeAddress'
    ),
    'strict' => array(
        'dn'
    ),
    'public' => true,
    'readonly' => false,
    'admin' => array(),
    'export' => true
);
 */

/**
 * A personal adressbook. This assumes that the login is
 * <username>@domain.com and that the users are stored on the same
 * ldap server. Thus it is possible to bind with the username and
 * password from the user. For more info; please refer to the
 * docs/LDAP file in the Turba distribution.

// First we need to get the uid.
$uid = Auth::getAuth();
if (preg_match('/(^.*)@/', $uid, $matches)) {
    $uid = $matches[1];
}
$basedn = 'dc=example, dc=com';
$cfgSources['personal_ldap'] = array(
    'title' => 'My Addressbook',
    'type' => 'ldap',
    'params' => array(
        'server' => 'localhost',
        'root' => 'ou=' . $uid . ',ou=personal_addressbook' . $basedn,
        'bind_dn' => 'uid=' . $uid . ',ou=People,' . $basedn,
        'bind_password' => Auth::getCredential('password'),
        'dn' => array('cn', 'uid'),
        'objectclass' => array('person',
                               'pilotPerson',
                               'organizationalPerson'),
        'encoding' => 'utf8',
        'version' => 3
    ),
    'map' => array(
        '__key' => 'dn',
        'name' => 'cn',
        'email' => 'mail',
        'surname' => 'sn',
        'title' => 'title',
        'company' => 'organizationname',
        'businessCategory' => 'businesscategory',
        'companyAddress' => 'postaladdress',
        'zip' => 'postalcode',
        'workPhone' => 'telephonenumber',
        'fax' => 'facsimiletelephonenumber',
        'homeAddress' => 'homepostaladdress',
        'homePhone' => 'homephone',
        'cellPhone' => 'mobile',
        'notes' => 'description',
        'pgpPublicKey' => 'object_pgppublickey'
    ),
    'search' => array(
        'name',
        'email',
        'businessCategory',
        'title',
        'homePhone',
        'workPhone',
        'cellPhone',
        'homeAddress'
    ),
    'strict' => array(
        'dn'
    ),
    'public' => true,
    'readonly' => false,
    'admin' => array($uid),
    'export' => true
);
 */

/**
 * A preferences-based adressbook. This will always be private. You
 * can add any attributes you like to the map and it will just work;
 * you can also create multiple prefs-based addressbooks by changing
 * the 'name' parameter. This is best for addressbooks that are
 * expected to remain small; it's not the most efficient, but it can't
 * be beat for getting up and running quickly, especially if you
 * already have Horde preferences working.
$cfgSources['prefs'] = array(
    'title' => 'Private AddressBook',
    'type' => 'prefs',
    'params' => array(
        'name' => 'prefs'
    ),
    'map' => array(
        '__key' => 'id',
        '__type' => '_type',
        '__members' => '_members',
        'name' => 'name',
        'email' => 'mail',
        'alias' => 'alias'
    ),
    'search' => array(
        'name',
        'email',
        'alias'
    ),
    'strict' => array(
        'id'
    ),
    'public' => false,
    'readonly' => false,
    'export' => true);
 */
