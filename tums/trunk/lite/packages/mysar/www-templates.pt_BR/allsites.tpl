<nobr>[
<a href="./?a=IPSummary&date={$pageVars.date}">&lt;&lt;&lt; Voltar para Esta&ccedil;&otilde;es e Usu&aacute;rios de um dia Espec&iacute;fico</a>
|
<a href="{$pageVars.uri}">Atualizar esta p&aacute;gina</a>
]</nobr>

<table><tr><th style="font-size: 20px";>Relat&oacute;rio de Sites de um dia Espec&iacute;fico</th></tr></table>
<p>
<table>
  <tr><td style="font-size: 20px;">
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.previousWeek}">&lt;&lt;</a>
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.previousDate}">&lt;</a>
  {$pageVars.thisDateFormatted}
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.nextDate}">&gt;</a>
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.nextWeek}">&gt;&gt;</a>
  </td></tr>
  <tr><td style="text-align:center;">
  <a href="./?a={$pageVars.thisPage}&date={$pageVars.today}">[ Ir para o dia de Hoje ]</a>
  </td></tr>
  </table>
  <p>
      [
        <a href="{$pageVars.uri}&action=setDefaultView">
          Manter esta visualiza&ccedil;&atilde;o como padr&atilde;o
        </a>
      ]
  <table>
    <tr>
      <th></th>
      <th>
        <a href="./?{$pageVars.url.siteASC}"><img border="{$pageVars.siteASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.siteLabelStart}SITE{$pageVars.siteLabelEnd}
        <a href="./?{$pageVars.url.siteDESC}"><img border="{$pageVars.siteDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
      <th>
        <a href="./?{$pageVars.url.usersASC}"><img border="{$pageVars.usersASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.usersLabelStart}USU&Aacute;RIOS{$pageVars.usersLabelEnd}
        <a href="./?{$pageVars.url.usersDESC}"><img border="{$pageVars.usersDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
      <th>
        <a href="./?{$pageVars.url.hostsASC}"><img border="{$pageVars.hostsASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.hostsLabelStart}ESTA&Ccedil;&Otilde;ES{$pageVars.hostsLabelEnd}
        <a href="./?{$pageVars.url.hostsDESC}"><img border="{$pageVars.hostsDESCImageBorder}" src="images/down-arrow.gif"></a>
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
  {foreach from=$pageVars.allSites item=record}
  <tr onMouseOver="this.bgColor='#C5D3E7';" onMouseOut="this.bgColor='#DAE3F0';">
    <td><a href="./?a=siteusers&sitesID={$record.sitesID}&date={$pageVars.date}"><b>Detalhes</b></a></td>
    <td style="text-align: left"><a href="{$record.site}" target="_blank">{$record.site|string_trim:80:"..."}</a></td>
    <td>{$record.users}</td>
    <td>{$record.hosts}</td>
    <td>{$record.bytes|bytesToHRF:$pageVars.byteUnit}</td>
    <td>{$record.cachePercent}%</td>
  </tr>
  {/foreach}
  </table>
