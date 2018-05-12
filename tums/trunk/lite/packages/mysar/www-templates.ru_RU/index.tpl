<nobr>[
<a href="{$pageVars.uri}">Обновить страницу</a>
]</nobr>

      <table><tr><th style="font-size: 20px";>Статистика {$pageVars.topGrouping}</th></tr></table>
      <p>
      [
        <a href="{$smarty.server.PHP_SELF}?a={$pageVars.thisPage}&action=setDefaultView&OrderMethod={$pageVars.OrderMethod}&OrderBy={$pageVars.OrderBy}&ByteUnit={$pageVars.ByteUnit}">
          Установить вид по-умолчанию
        </a>
      ]
      <br>
      <table cellpadding=1 cellspacing=1>
        <tr>
          <th rowspan="2">
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.dateASC}"><img border="{$pageVars.dateASCImageBorder}" src="images/up-arrow.gif"></a>
              {$pageVars.dateLabelStart}Дата{$pageVars.dateLabelEnd}
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.dateDESC}"><img border="{$pageVars.dateDESCImageBorder}" src="images/down-arrow.gif"></a>
          </th>
          <th rowspan="2">
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.usersASC}"><img border="{$pageVars.usersASCImageBorder}" src="images/up-arrow.gif"></a>
              {$pageVars.usersLabelStart}Пользователи{$pageVars.usersLabelEnd}
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.usersDESC}"><img border="{$pageVars.usersDESCImageBorder}" src="images/down-arrow.gif"></a>
          </th>
          <th rowspan="2">
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.hostsASC}"><img border="{$pageVars.hostsASCImageBorder}" src="images/up-arrow.gif"></a>
              {$pageVars.hostsLabelStart}Хосты{$pageVars.hostsLabelEnd}
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.hostsDESC}"><img border="{$pageVars.hostsDESCImageBorder}" src="images/down-arrow.gif"></a>
          </th>
          <th rowspan="2">
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.sitesASC}"><img border="{$pageVars.sitesASCImageBorder}" src="images/up-arrow.gif"></a>
              {$pageVars.sitesLabelStart}Сайты{$pageVars.sitesLabelEnd}
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.sitesDESC}"><img border="{$pageVars.sitesDESCImageBorder}" src="images/down-arrow.gif"></a>
          </th>
          <th colspan="2">Трафик</th>
        </tr>
        <tr>
          <th>
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.bytesASC}"><img border="{$pageVars.bytesASCImageBorder}" src="images/up-arrow.gif"></a>
              {$pageVars.bytesLabelStart}Объем{$pageVars.bytesLabelEnd}
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
              {$pageVars.cachePercentLabelStart}% использования КЭШ{$pageVars.cachePercentLabelEnd}
            <a href="{$smarty.server.PHP_SELF}?{$pageVars.url.cachePercentDESC}"><img border="{$pageVars.cachePercentDESCImageBorder}" src="images/down-arrow.gif"></a>
          </th>
        </tr>
        {foreach from=$pageVars.availableDates item=date}
        <tr onMouseOver="this.bgColor='#C5D3E7';" onMouseOut="this.bgColor='#DAE3F0';">
          <td style="text-align: left;">
          {if $date.minDate == $date.maxDate}
            <a href='{$smarty.server.PHP_SELF}?a=IPSummary&date={$date.date}'>{$date.dateFormatted}</a>
          {else}
            <a href='{$smarty.server.PHP_SELF}?minDate={$date.minDate}&maxDate={$date.maxDate}'>{$date.dateFormatted}</a>
          {/if}

          </td>
          <td style="text-align: center;">{$date.users}</td>
          <td style="text-align: center;">{$date.hosts}</td>
          <td style="text-align: center;">
          {if $date.minDate == $date.maxDate}
            <a href="{$smarty.server.PHP_SELF}?a=allsites&date={$date.date}">{$date.sites}</a>
          {else}
            {$date.sites}
          {/if}
          </td>
          <td style="text-align: right;">{$date.bytes|bytesToHRF:$pageVars.ByteUnit}</td>
          <td style="text-align: center;">{$date.cachePercent}%</td>
        </tr>
      {/foreach}
      </table>
