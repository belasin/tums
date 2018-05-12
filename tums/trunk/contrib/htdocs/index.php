<!DOCTYPE html
  PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
    <head>
        <title>Vulani - <?=$_SERVER["SERVER_NAME"]?></title>
        <link href="style.css" rel="stylesheet" type="text/css"/>
        <script type="text/javascript">
            function mouseOver(id){
                document.getElementById(id).src="/images/"+id+"-hover.png"
            }
            function mouseOut(id){
                document.getElementById(id).src="/images/"+id+".png"
            }
        </script>
    </head>
    <body>
        <table height="100%" width="100%">
            <tr height=100%><td>
            <div id="centerBox" valign="middle">
                <div id="blockTop"></div>
                <div id="centerBlock">
                </div>
                <div id="menuBlock">
                    <a href="http://<?=$_SERVER["SERVER_NAME"]?>/mail/">
                        <img id="mail" src="/images/mail.png" onmouseover="mouseOver('mail')" onmouseout="mouseOut('mail')"/>
                    </a>
                    &nbsp;&nbsp;&nbsp;
                    &nbsp;&nbsp;&nbsp;
                    <a href="http://<?=$_SERVER["SERVER_NAME"]?>:9682/auth/">
                        <img id="config" src="/images/config.png" onmouseover="mouseOver('config')" onmouseout="mouseOut('config')"/>
                    </a>
                </div>
            </div>
            </td></tr>
        </table>

    </body>

</html>
