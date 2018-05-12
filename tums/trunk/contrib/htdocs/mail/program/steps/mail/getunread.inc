<?php

/*
 +-----------------------------------------------------------------------+
 | program/steps/mail/getunread.inc                                      |
 |                                                                       |
 | This file is part of the RoundCube Webmail client                     |
 | Copyright (C) 2005, RoundCube Dev. - Switzerland                      |
 | Licensed under the GNU GPL                                            |
 |                                                                       |
 | PURPOSE:                                                              |
 |   Check all mailboxes for unread messages and update GUI              |
 |                                                                       |
 +-----------------------------------------------------------------------+
 | Author: Thomas Bruederli <roundcube@gmail.com>                        |
 +-----------------------------------------------------------------------+

 $Id: getunread.inc 269 2006-06-29 23:41:40Z richs $

*/

$REMOTE_REQUEST = TRUE;

$a_folders = $IMAP->list_mailboxes();

if (!empty($a_folders))
  {
  foreach ($a_folders as $mbox_row)
    {
    $commands = sprintf("this.set_unread_count('%s', %d);\n", addslashes($mbox_row), $IMAP->messagecount($mbox_row, 'UNSEEN'));
    rcube_remote_response($commands, TRUE);
    }
  }

exit;
?>
