<?php

/*
 +-----------------------------------------------------------------------+
 | program/steps/addressbook/list.inc                                    |
 |                                                                       |
 | This file is part of the RoundCube Webmail client                     |
 | Copyright (C) 2005, RoundCube Dev. - Switzerland                      |
 | Licensed under the GNU GPL                                            |
 |                                                                       |
 | PURPOSE:                                                              |
 |   Send contacts list to client (as remote response)                   |
 |                                                                       |
 +-----------------------------------------------------------------------+
 | Author: Thomas Bruederli <roundcube@gmail.com>                        |
 +-----------------------------------------------------------------------+

 $Id: list.inc 88 2005-12-03 16:54:12Z roundcube $

*/

$REMOTE_REQUEST = TRUE;

// count contacts for this user
$sql_result = $DB->query("SELECT COUNT(contact_id) AS rows
                          FROM ".get_table_name('contacts')."
                          WHERE  del<>1
                          AND    user_id=?",
                          $_SESSION['user_id']);
                                   
$sql_arr = $DB->fetch_assoc($sql_result);
$rowcount = $sql_arr['rows'];    

// update message count display
$pages = ceil($rowcount/$CONFIG['pagesize']);
$commands = sprintf("this.set_rowcount('%s');\n", rcmail_get_rowcount_text($rowcount));
$commands .= sprintf("this.set_env('pagecount', %d);\n", $pages);

$start_row = ($CONTACTS_LIST['page']-1) * $CONFIG['pagesize'];

// get contacts from DB
$sql_result = $DB->limitquery("SELECT * FROM ".get_table_name('contacts')."
                               WHERE  del<>1
                               AND    user_id=?
                               ORDER BY name",
                               $start_row,
                               $CONFIG['pagesize'],
                               $_SESSION['user_id']);
                                 
$commands .= rcmail_js_contacts_list($sql_result);
  
// send response
rcube_remote_response($commands);

exit;
?>