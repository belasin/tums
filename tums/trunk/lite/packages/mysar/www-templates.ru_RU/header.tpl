<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN">
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8">
    <title>{$pageVars.programName} {$pageVars.programVersion}</title>
    <link rel="stylesheet" href="dfl.css" type="text/css">
    {literal}
    <SCRIPT language="JavaScript"><!--
      function my_confirm(msg,go) {
        var where_to= confirm(msg);
        if (where_to== true) {
          window.location=go;
        }
      }
    //--></SCRIPT>
   {/literal}
  </head>
    <body><center>
    <h1>{$pageVars.programName} {$pageVars.programVersion}</h1>
    <p>[ <a href=".">Главная страница</a> | <a href="{$smarty.server.PHP_SELF}?a=administration">Администрированиие MySAR</a> ]</p>
