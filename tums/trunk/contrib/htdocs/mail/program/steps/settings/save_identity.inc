<?php

/*
 +-----------------------------------------------------------------------+
 | program/steps/settings/save_identity.inc                              |
 |                                                                       |
 | This file is part of the RoundCube Webmail client                     |
 | Copyright (C) 2005, RoundCube Dev. - Switzerland                      |
 | Licensed under the GNU GPL                                            |
 |                                                                       |
 | PURPOSE:                                                              |
 |   Save an identity record or to add a new one                         |
 |                                                                       |
 +-----------------------------------------------------------------------+
 | Author: Thomas Bruederli <roundcube@gmail.com>                        |
 +-----------------------------------------------------------------------+

 $Id: save_identity.inc 292 2006-08-04 12:10:34Z thomasb $

*/

$a_save_cols = array('name', 'email', 'organization', 'reply-to', 'bcc', 'standard', 'signature');
$a_html_cols = array('signature');


// check input
if (empty($_POST['_name']) || empty($_POST['_email']))
  {
  show_message('formincomplete', 'warning');
  rcmail_overwrite_action('edit-identitiy');
  return;
  }


// update an existing contact
if ($_POST['_iid'])
  {
  $a_write_sql = array();

  foreach ($a_save_cols as $col)
    {
    $fname = '_'.$col;
    if (!isset($_POST[$fname]))
      continue;

    $a_write_sql[] = sprintf("%s=%s",
                             $DB->quoteIdentifier($col),
                             $DB->quote(get_input_value($fname, RCUBE_INPUT_POST, in_array($col, $a_html_cols))));
    }

  if (sizeof($a_write_sql))
    {
    $DB->query("UPDATE ".get_table_name('identities')."
                SET ".join(', ', $a_write_sql)."
                WHERE  identity_id=?
                AND    user_id=?
                AND    del<>1",
                $_POST['_iid'],
                $_SESSION['user_id']);
                       
    $updated = $DB->affected_rows();
    }
       
  if ($updated && !empty($_POST['_standard']))
    {
    show_message('successfullysaved', 'confirmation');

    // mark all other identities as 'not-default'
    $DB->query("UPDATE ".get_table_name('identities')."
                SET ".$DB->quoteIdentifier('standard')."='0'
                WHERE  user_id=?
                AND    identity_id<>?
                AND    del<>1",
                $_SESSION['user_id'],
                $_POST['_iid']);
    
    if ($_POST['_framed'])
      {
      // update the changed col in list
      // ...      
      }
    }
  else if ($DB->is_error())
    {
    // show error message
    show_message('errorsaving', 'error');
    rcmail_overwrite_action('edit-identitiy');
    }
  }

// insert a new contact
else
  {
  $a_insert_cols = $a_insert_values = array();

  foreach ($a_save_cols as $col)
    {
    $fname = '_'.$col;
    if (!isset($_POST[$fname]))
      continue;
    
    $a_insert_cols[] = $DB->quoteIdentifier($col);
    $a_insert_values[] = $DB->quote(get_input_value($fname, RCUBE_INPUT_POST, in_array($col, $a_html_cols)));
    }
    
  if (sizeof($a_insert_cols))
    {
    $DB->query("INSERT INTO ".get_table_name('identities')."
                (user_id, ".join(', ', $a_insert_cols).")
                VALUES (?, ".join(', ', $a_insert_values).")",
                $_SESSION['user_id']);

    $insert_id = $DB->insert_id(get_sequence_name('identities'));
    }
    
  if ($insert_id)
    {
    $_GET['_iid'] = $insert_id;

    if ($_POST['_framed'])
      {
      // add contact row or jump to the page where it should appear
      // ....
      }
    }
  else
    {
    // show error message
    show_message('errorsaving', 'error');
    rcmail_overwrite_action('edit-identitiy');
    }
  }


// go to next step
rcmail_overwrite_action($_POST['_framed'] ? 'edit-identitiy' : 'identities');

?>