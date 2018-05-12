<nobr>[
<a href=".">&lt;&lt;&lt; Back to "Daily Summary"</a>
|
<a href="{$pageVars.uri}">Refresh this page</a>
]</nobr>

<table><tr><th style="font-size: 20px;">Hosts and Users Summary for a Specific Day</th></tr></table>
<p>
<p>
<table>
  <tr><td style="font-size: 20px;">
  <a href="{$smarty.server.PHP_SELF}?a={$pageVars.thisPage}&date={$pageVars.previousWeek}" title="Go back a week">&lt;&lt;</a>
  <a href="{$smarty.server.PHP_SELF}?a={$pageVars.thisPage}&date={$pageVars.previousDate}" title="Go back a day">&lt;</a>
  {$pageVars.thisDateFormatted}
  <a href="{$smarty.server.PHP_SELF}?a={$pageVars.thisPage}&date={$pageVars.nextDate}" title="Go forward a day">&gt;</a>
  <a href="{$smarty.server.PHP_SELF}?a={$pageVars.thisPage}&date={$pageVars.nextWeek}" title="Go forward a week">&gt;&gt;</a>
  </td></tr>
  <tr><td style="text-align:center;">
  <a href="{$smarty.server.PHP_SELF}?a={$pageVars.thisPage}&date={$pageVars.today}" title="Go to today's report">[ Go to today ]</a>
  </td></tr>
  </table>
<p>
[ <a href="{$smarty.server.PHP_SELF}?a=allsites&date={$pageVars.date}" title="List of all the different sites that were visited">Sites Summary for a Specific Day</a> ]

<center>
      [
        <a href="{$smarty.server.PHP_SELF}?a={$pageVars.thisPage}&action=setDefaultView&OrderMethod={$pageVars.OrderMethod}&OrderBy={$pageVars.OrderBy}&ByteUnit={$pageVars.ByteUnit}&date={$pageVars.date}" title="Click this to save the viewing preferences of this report">
          Set this view as the default
        </a>
      ]
  <table>
    <tr>
      <th></th>
      <th>
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.hostipASC}"><img border="{$pageVars.hostipASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.hostipLabelStart}HOST{$pageVars.hostipLabelEnd}
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.hostipDESC}"><img border="{$pageVars.hostipDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
      <th>
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.usernameASC}"><img border="{$pageVars.usernameASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.usernameLabelStart}USERNAME{$pageVars.usernameLabelEnd}
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.usernameDESC}"><img border="{$pageVars.usernameDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
      <th>
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.sitesASC}"><img border="{$pageVars.sitesASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.sitesLabelStart}SITES{$pageVars.sitesLabelEnd}
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.sitesDESC}"><img border="{$pageVars.sitesDESCImageBorder}" src="images/down-arrow.gif"></a>
      </th>
      <th>
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.bytesASC}"><img border="{$pageVars.bytesASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.bytesLabelStart}BYTES{$pageVars.bytesLabelEnd}
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.bytesDESC}"><img border="{$pageVars.bytesDESCImageBorder}" src="images/down-arrow.gif"></a>
        <br>
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.B}">{$pageVars.BLabelStart}B{$pageVars.BLabelEnd}</a>
        |
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.K}">{$pageVars.KLabelStart}K{$pageVars.KLabelEnd}</a>
        |
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.M}">{$pageVars.MLabelStart}M{$pageVars.MLabelEnd}</a>
        |
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.G}">{$pageVars.GLabelStart}G{$pageVars.GLabelEnd}</a>
      </th>
      <th>
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.cachePercentASC}"><img border="{$pageVars.cachePercentASCImageBorder}" src="images/up-arrow.gif"></a>
          {$pageVars.cachePercentLabelStart}CACHE PERCENT{$pageVars.cachePercentLabelEnd}
        <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.cachePercentDESC}"><img border="{$pageVars.cachePercentDESCImageBorder}" src="images/down-arrow.gif"></a>
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
      <td><a href='{$smarty.server.PHP_SELF}?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$thisRecord}</td>
      <td><a href='{$smarty.server.PHP_SELF}?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$record.username}</td>
      <td><a href='{$smarty.server.PHP_SELF}?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$record.sites}</td>
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
    <tr><th colspan="7">Latest user activity</th></td>
    <tr>
      <th>HOST IP</th>
      <th>USERNAME</th>
      <th>TIME</th>
      <th>BYTES</th>
      <th>URL</th>
      <th>STATUS</th>
    </tr>
    {foreach from=$pageVars.latestUserActivity item=record}
    <tr onMouseOver="this.bgColor='#C5D3E7';" onMouseOut="this.bgColor='#DAE3F0';">
      <td><a href='{$smarty.server.PHP_SELF}?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$record.hostip}</a></td>
      <td><a href='{$smarty.server.PHP_SELF}?a=IPSitesSummary&date={$pageVars.date}&hostiplong={$record.hostiplong}&usersID={$record.usersID}'>{$record.username}</a></td>
      <td>{$record.time}</td>
      <td>{$record.bytes}</td>
      <td style="text-align: left"><a href="{$record.url}" target="_blank">{$record.url|string_trim:80:"..."}</a></td>
      <td style="text-align: left">{$record.resultCode}</td>
    </tr>
    {/foreach}
  </table>
</center>
