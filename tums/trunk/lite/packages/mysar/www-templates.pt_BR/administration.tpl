      <table><tr><th style="font-size: 20px";>Administra&ccedil;&atilde;o do MySar</th></tr></table>
      <p>
      <table>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="keepHistoryDays">
        <tr>
          <td colspan="2">Excluir dados antigos automaticamente depois de <input type="text" name="thisValue" size="2" value="{$pageVars.keepHistoryDays}"> dias</td>
          <td><input type="submit" name="submit" value="Modificar"></td>
        </tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Para prevenir que a base de dados fique muito grande, mysar ir&aacute; excluir os registros antigos periodicamente. Use este valor para especificar o tempo dos dados na base. N&atilde;o aumente muito o valor, pois a base ir&aacute; crescer muito, e consequentemente degradar a performance do seu servidor. Valor padr&atilde;o: 32
      </td></tr>
        </form>
      <tr><td colspan="3"><hr size="1"></td></tr>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="squidLogPath">
        <tr>
          <td>Arquivo de LOGs do Squid: (access.log)</td>
          <td><input type="text" name="thisValue" size="30" value="{$pageVars.squidLogPath}"></td>
          <td><input type="submit" name="submit" value="Modificar"></td>
        </tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Especifique aqui onde encontrar o aqruivo de LOG do Squid. MySar precisa saber onde est&aacute; localizado o arquivo de LOG do squid, pois e desse arquivo que s&atilde;o gerados os Relat&oacute;rios. Tenha certeza que o arquivo tem permiss&atilde;o de leitura para o usu&aacute;rio do MySar. Valor padr&atilde;o: /var/log/squid/access.log.
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
          <td colspan="2">Resoluc&atilde;o de Nomes est&aacute;:
            <select name="thisValue">
              <option value="enabled" {$optionEnabled}>Ativado
              <option value="disabled" {$optionDisabled}>Desativado
            </select>
          </td>
          <td><input type="submit" name="submit" value="Modificar"></td>
        </tr>
        </form>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Se a sua rede possui um servidor DNS configurado internamente, MySar ir&aacute; resolver os IPs das esta&ccedil;&otilde;es. Assim todos os Relat&oacute;rios ir&atilde;o exibir o nome da Esta&ccedil;&atilde;o, inv&eacute;s do seu IP. Deixe este valor desabilitado se sua rede n&atilde;o possui um servidor DNS, pois isso ir&aacute; degradar muito a performance do MySar, tentando resolver nomes. Valor padr&atilde;o: Desabilitado.
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
          <td colspan="2">MySAR est&aacute;
            <select name="thisValue">
              <option value="enabled" {$optionEnabled}>Ativado
              <option value="disabled" {$optionDisabled}>Desativado
            </select>
          </td>
          <td><input type="submit" name="submit" value="Modificar"></td>
        </tr>
        </form>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Se por algum motivo voce quer que o MySar pare de Importar os dados do Squid, Selecione esta op&ccedil;&atilde;o. Valor padr&atilde;o: Ativado.
      </td></tr>
      <tr><td colspan="3"><hr size="1"></td></tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Clique nesse bot&atilde;o para apagar TODOS os dados coletados pelo MySar. Esta a&ccedil;&atilde;o n&atilde;o tem volta. Use isto para resolver problemas, tipo relat&oacute;rios n&atilde;o exibindo corretamente, ou corrup&ccedil;&atilde;o dos dados nas tabelas da base. TENHA REALMENTE CERTEZA do que voce est&aacute; fazendo!
      </td>
        <td colspan="3" style="text-align:center;">
          <input type="submit" value="Apagar tudo" onClick="my_confirm('Voce tem certeza que quer apagar TODOS os dados?!','{$pageVars.uri}&action=eraseAllStats')">
        </td>
      </tr>
      
      </table>
      
