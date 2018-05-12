<?php /* Smarty version 2.6.10, created on 2007-08-08 17:57:20
         compiled from footer.tpl */ ?>
      <p>
      <table>
       <tr><td>Current active users: </td><td><?php echo $this->_tpl_vars['pageVars']['activeUsers']; ?>
</td>
       <tr><td>Current date and time is: </td><td><?php echo $this->_tpl_vars['pageVars']['currentDateTime']; ?>
</td>
       <tr><td>Last processed record: </td><td><?php echo $this->_tpl_vars['pageVars']['lastTimestampFormatted']; ?>
</td>
       <tr><td>Number of records processed at last import: </td><td><?php echo $this->_tpl_vars['pageVars']['lastImportedRecordsNumber']; ?>
</td>
       <tr><td>Last clean-up of the database was done at: </td><td><?php echo $this->_tpl_vars['pageVars']['lastCleanUp']; ?>
</td>
      </table>
    <hr>
    <a href="http://giannis.stoilis.gr/software/mysar/" target="_blank"><?php echo $this->_tpl_vars['pageVars']['programName']; ?>
</a> <?php echo $this->_tpl_vars['pageVars']['programVersion']; ?>
 (c) 2004-2005 by <a href="mailto:giannis@stoilis.gr">Giannis Stoilis</a>
<br>Licenced under the <a href="http://www.fsf.org/copyleft/gpl.html" target="_blank">GNU General Public Licence</a>.
    </a>
  </center></body>
</html>