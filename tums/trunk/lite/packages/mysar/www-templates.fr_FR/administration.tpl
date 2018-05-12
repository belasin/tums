      <table><tr><th style="font-size: 20px";>Administration</th></tr></table>
      <p>
      <table>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="keepHistoryDays">
        <tr>
          <td colspan="2">Effacer automatiquement les donn&eacute;es datant de plus de <input type="text" name="thisValue" size="2" value="{$pageVars.keepHistoryDays}"> jours</td>
          <td><input type="submit" name="submit" value="Chang&eacute; la valeur"></td>
        </tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Pour empêcher la base de donn&eacute;es d'obtenir d'anciennes donn&eacute;es, employer cette valeur pour indiquer combien de fois vous voulez que cet entretien ai lieu. Ne pas placer cette valeur trop haute, &agrave; mesure qu'il augmentera la charge du serveur. Valeur par d&eacute;faut : 32.
      </td></tr>
        </form>
      <tr><td colspan="3"><hr size="1"></td></tr>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="squidLogPath">
        <tr>
          <td>Localisation du fichier access.log</td>
          <td><input type="text" name="thisValue" size="30" value="{$pageVars.squidLogPath}"></td>
          <td><input type="submit" name="submit" value="Chang&eacute; la valeur"></td>
        </tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Chemin d'acc&egrave;s au fichier de log du squid. Mysar a besoin de cette valeur afin de rassembler les donn&eacute;es. S'assurer que ce dossier est lisible par l'utilisateur root. Valeur par d&eacute;faut : /var/log/squid/access.log. 
      </td></tr>
        </form>
      <tr><td colspan="3"><hr size="1"></td></tr>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="resolveClients">
        {if $pageVars.resolveClients=="enabled"}
	{assign var="optionEnabled" value="selected"}
	{assign var="optionDisabled" value=""}
	{else}
	{assign var="optionEnabled" value=""}
	{assign var="optionDisabled" value="selected"}
	{/if}
        <tr>
          <td colspan="2">R&eacute;solution DNS
            <select name="thisValue">
              <option value="enabled" {$optionEnabled}>Activer
              <option value="disabled" {$optionDisabled}>D&eacute;sactiver
            </select>
          </td>
          <td><input type="submit" name="submit" value="Chang&eacute; la valeur"></td>
        </tr>
        </form>
      <tr><td colspan="2" style="text-align:justify;" width="200">
     Si vous avez un r&eacute;seau où tous vos clients sont reli&eacute;s et ont une adresse DNS, permettre l'utilisation à mysar d'utiliser les informations du DNS pour montrer les statistiques par utilisateur. Valeur par d&eacute;faut : Activ&eacute;. 
      </td></tr>

      <tr><td colspan="3"><hr size="1"></td></tr>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="mysarImporter">
        {if $pageVars.mysarImporter=="enabled"}
	{assign var="optionEnabled" value="selected"}
	{assign var="optionDisabled" value=""}
	{else}
	{assign var="optionEnabled" value=""}
	{assign var="optionDisabled" value="selected"}
	{/if}
        <tr>
          <td colspan="2">MySAR is
            <select name="thisValue">
              <option value="enabled" {$optionEnabled}>Activer
              <option value="disabled" {$optionDisabled}>D&eacute;sactiver
            </select>
          </td>
          <td><input type="submit" name="submit" value="Chang&eacute; la valeur"></td>
        </tr>
        </form>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Si, pour quelque raison, vous voulez que mysar cesse d'importer le fichier de log dans la base de donn&eacute;es, employer cette option. Valeur par d&eacute;faut : Activ&eacute;. 
      </td></tr>


      <tr><td colspan="3"><hr size="1"></td></tr>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="topGrouping">
	{if $pageVars.topGrouping=="Yearly"}
		{assign var="optionYearly" value="selected"}
	{elseif $pageVars.topGrouping=="Monthly"}
		{assign var="optionMonthly" value="selected"}
	{elseif $pageVars.topGrouping=="Weekly"}
		{assign var="optionWeekly" value="selected"}
	{else}
		{assign var="optionDaily" value="selected"}
	{/if}
        <tr>
          <td colspan="2">P&eacute;riodicit&eacute;
            <select name="thisValue">
              <option value="Yearly" {$optionYearly}>Annuellement 
              <option value="Monthly" {$optionMonthly}>Mensuel 
              <option value="Weekly" {$optionWeekly}>Hebdomadaire 
              <option value="Daily" {$optionDaily}>Quotidien 
            </select>
          </td>
          <td><input type="submit" name="submit" value="Chang&eacute; la valeur"></td>
        </tr>
        </form>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Si, pour quelque raison, vous voulez que mysar cesse d'importer le fichier de log tout les jours ,dans la base de donn&eacute;es, employer cette option. Valeur par d&eacute;faut : Activ&eacute;. 
      </td></tr>

      <tr><td colspan="3"><hr size="1"></td></tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Appuyer sur ce bouton pour effacer TOUTES LES donn&eacute;es rassembl&eacute;es par mysar. Cette action n'est pas r&eacute;versible. Employer ceci pour r&eacute;soudre tous les problèmes &eacute;tranges, comme des rapports ne se mettant pas &agrave; jour correctement etc...
      </td>
        <td colspan="3" style="text-align:center;">
          <input type="submit" value="Erase all statistics" onClick="my_confirm('Are you sure you want to erase ALL statistics?','{$pageVars.uri}&action=eraseAllStats')">
        </td>
      </tr>
      
      </table>
      
