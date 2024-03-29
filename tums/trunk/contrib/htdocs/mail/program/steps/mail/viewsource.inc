<?php

/*
 +-----------------------------------------------------------------------+
 | program/steps/mail/viewsource.inc                                     |
 |                                                                       |
 | This file is part of the RoundCube Webmail client                     |
 | Copyright (C) 2005, RoundCube Dev. - Switzerland                      |
 | Licensed under the GNU GPL                                            |
 |                                                                       |
 | PURPOSE:                                                              |
 |   Display a mail message similar as a usual mail application does     |
 |                                                                       |
 +-----------------------------------------------------------------------+
 | Author: Thomas Bruederli <roundcube@gmail.com>                        |
 +-----------------------------------------------------------------------+

 $Id: viewsource.inc 8 2005-09-28 22:28:05Z roundcube $

*/


// similar code as in program/steps/mail/get.inc
if ($_GET['_uid'])
  {
  header('Content-Type: text/plain');
  print rcmail_message_source($_GET['_uid']);
  }
else
  {
  raise_error(array('code' => 500,
                    'type' => 'php',
                    'message' => 'Message UID '.$_GET['_uid'].' not found'),
              TRUE,
              TRUE);
  }

exit;
?>