<nobr>[
<a href=".">&lt;&lt;&lt; Voltar para Relat&oacute;rio Di&aacute;rio</a>
|
<a href="{$pageVars.uri}">Atualizar esta p&aacute;gina</a>
]</nobr>

<table><tr><th style="font-size: 20px;">Relat&oacute;rio de Esta&ccedil;&otilde;es e Usu&aacute;rios de Um dia</th></tr></table>
<p>
<p>
<table>
  <tr><td style="font-size: 20px;">
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.previousWeek}" title="Voltar 1 Semana">&lt;&lt;</a>
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.previousDate}" title="Voltar 1 Dia">&lt;</a>
  {$pageVars.thisDateFormatted}
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.nextDate}" title="Avancar 1 Dia">&gt;</a>
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.nextWeek}" title="Avancar 1 Semana">&gt;&gt;</a>
  </td></tr>
  <tr><td style="text-align:center;">
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.today}" title="Dia de Hoje">[ Ir para o dia de Hoje ]</a>
  </td></tr>
  </table>
<p>
[ <a href="./?a=allsites&date={$pageVars.date}" title="Lista de sites que foram acessados">Visualizar TODOS os sites acessados Neste dia</a> ]

<center>
      [
        <a href="./?a={$pageVars.thisPage}&action=setDefaultView&OrderMethod={$pageVars.OrderMethod}&OrderBy={$pageVars.OrderBy}&ByteUnit={$pageVars.ByteUnit}&date={$pageVars.date}">
          Manter esta visualiza&ccedil;&atilde;o como padr&atilde;o
        </a>
      ]
  <table>
    <tr>
      <th></th>
      <th>
        <a href="./?{$pageVars.url.hostipASC}"><img border="{$pageVars.hostipASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.hostipLabelStart}ESTA&Ccedil;&Otilde;ES{$pageVars.hostipLabelEnd}
        <a href="./?{$pageVars.url.hostipDESC}"><img border="{$pageVars.hostipDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
      <th>
        <a href="./?{$pageVars.url.usernameASC}"><img border="{$pageVars.usernameASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.usernameLabelStart}USU&Aacute;RIOS{$pageVars.usernameLabelEnd}
        <a href="./?{$pageVars.url.usernameDESC}"><img border="{$pageVars.usernameDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
      <th>
        <a href="./?{$pageVars.url.sitesASC}"><img border="{$pageVars.sitesASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.sitesLabelStart}SITES{$pageVars.sitesLabelEnd}
        <a href="./?{$pageVars.url.sitesDESC}"><img border="{$pageVars.sitesDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
      <th>
        <a href="./?{$pageVars.url.bytesASC}"><img border="{$pageVars.bytesASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.bytesLabelStart}BYTES{$pageVars.bytesLabelEnd}
        <a href="./?{$pageVars.url.bytesDESC}"><img border="{$pageVars.bytesDESCImageBorder}" src="images/down-arrow.gif"></a>
        <br>
        <a href="./?{$pageVars.url.B}">{$pageVars.BLabelStart}B{$pageVars.BLabelEnd}</a>
        |
        <a href="./?{$pageVars.url.K}">{$pageVars.KLabelStart}K{$pageVars.KLabelEnd}</a>
        |
        <a href="./?{$pageVars.url.M}">{$pageVars.MLabelStart}M{$pageVars.MLabelEnd}</a>
        |
        <a href="./?{$pageVars.url.G}">{$pageVars.GLabelStart}G{$pageVars.GLabelEnd}</a>
      </th>
      <th>
        <a href="./?{$pageVars.url.cachePercentASC}"><img border="{$pageVars.cachePercentASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.cachePercentLabelStart}USO DO CACHE{$pageVars.cachePercentLabelEnd}
        <a href="./?{$pageVars.url.cachePercentDESC}"><img border="{$pageVars.cachePercentDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
    </tr>
    {assign var=bytesTotal value="0"}
    {foreach from=$pageVars.summaryIPRecords item=record}
      {if $record.hostdescription!=""}
        {assign var="thisRecord" value=$record.hostdescription"}
      {elseif $record.hostip!=$record.hostname}
        {assign var="thisRecord" value=$record.hostname}
      {else}
        {assign var="thisRecord" value=$record.hostip}
      {/if}

    <tr onMouseOver="this.bgColor='#C5D3E7';" onMouseOut="this.bgColor='#DAE3F0';">
      <td></td>
      <td><a href='./?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$thisRecord}</td>
      <td><a href='./?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$record.username}</td>
      <td><a href='./?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$record.sites}</td>
      <td>{$record.bytes|bytesToHRF:$pageVars.ByteUnit}</td>
      <td>{$record.cachePercent}%</td>
    </tr>
    {assign var=bytesTotal value=$bytesTotal+$record.bytes}
    {/foreach}
    <tr><td></td></tr>
    <tr><td></td></tr>
    <tr>
      <th>TOTALS</th>
      <th style="text-align: right;">{$pageVars.distinctValues.ips}</th>
      <th style="text-align: right;">{$pageVars.distinctValues.users}</th>
      <th style="text-align: right;">{$pageVars.distinctValues.sites}</th>
      <th style="text-align: right;">{$bytesTotal|bytesToHRF:$pageVars.ByteUnit}</th>
      <th></th>
    </tr>
  </table>
  <p>
  <table>
    <tr><th colspan="7">&Uacute;ltimas Atividades do Usu&aacute;rio</th></td>
    <tr>
      <th>IP ESTA&Ccedil;&Atilde;O</th>
      <th>USU&Aacute;RIO</th>
      <th>HORA</th>
      <th>BYTES</th>
      <th>URL</th>
      <th>STATUS</th>
    </tr>
    {foreach from=$pageVars.latestUserActivity item=record}
    <tr onMouseOver="this.bgColor='#C5D3E7';" onMouseOut="this.bgColor='#DAE3F0';">
      <td><a href='./?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$record.hostip}</a></td>
      <td><a href='./?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$record.username}</a></td>
      <td>{$record.time}</td>
      <td>{$record.bytes}</td>
      <td style="text-align: left"><a href="{$record.url}" target="_blank">{$record.url|string_trim:80:"..."}</a></td>
      <td style="text-align: left">{$record.resultCode}</td>
    </tr>
    {/foreach}
  </table>
</center>
