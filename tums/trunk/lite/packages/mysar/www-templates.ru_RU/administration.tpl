      <table><tr><th style="font-size: 20px";>Администрированиие MySAR</th></tr></table>
      <p>
      <table>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="keepHistoryDays">
        <tr>
          <td colspan="2">Автоматически удалять записи из БД старше, чем <input type="text" name="thisValue" size="2" value="{$pageVars.keepHistoryDays}"> дней</td>
          <td><input type="submit" name="submit" value="Изменить значение"></td>
        </tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Для того, чтобы БД не была слишком громоздкой, MySAR периодически удаляет старые записи. Используйте данное значение для определения периода времени, в течение которого вы хотите хранить информацию в БД. Чтобы не перегрузить сервер, не устанавливайте данной переменной слишком большое значение.<br>Значение по-умолчанию: 32 дня.
      </td></tr>
        </form>
      <tr><td colspan="3"><hr size="1"></td></tr>
        <form method="POST">
        <input type="hidden" name="hiddenSubmit" value="1">
        <input type="hidden" name="configName" value="squidLogPath">
        <tr>
          <td>Путь к лог-файлу Squid'а - access.log</td>
          <td><input type="text" name="thisValue" size="30" value="{$pageVars.squidLogPath}"></td>
          <td><input type="submit" name="submit" value="Изменить значение"></td>
        </tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Это полный путь к лог-файлу Squid access.log. MySAR требует данное значение для выборки данных из лог-файла. Проверьте, имеет ли возможность чтения этого файла пользователь, с правами которого запускается задача чтения лог-файлов cron.<br>Значение по-умолчанию: /var/log/squid/access.log.
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
          <td colspan="2">Разрешение DNS-имен компьютеров
            <select name="thisValue">
              <option value="enabled" {$optionEnabled}>включено
              <option value="disabled" {$optionDisabled}>отключено
            </select>
          </td>
          <td><input type="submit" name="submit" value="Изменить значение"></td>
        </tr>
        </form>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Если в вашей сети все клиенты, соединяющиеся со Squid имеют DNS-имена, включение данной функциональности позволит отобразить их имена в статистике. Иначе, держите эту опцию выключенной, т.к. она потребляет ресурсы системы.<br>Значение по-умолчанию: Выключено.
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
          <td colspan="2">MySAR 
            <select name="thisValue">
              <option value="enabled" {$optionEnabled}>запущен
              <option value="disabled" {$optionDisabled}>остановлен
            </select>
          </td>
          <td><input type="submit" name="submit" value="Изменить значение"></td>
        </tr>
        </form>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Если по какой-либо причине вы хотите остановить импортирование статистики из лог-файлов, используйте данную опцию.<br>Значение по-умолчанию: запущен.
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
          <td colspan="2">Первичная группировка
            <select name="thisValue">
              <option value="Yearly" {$optionYearly}>по годам
              <option value="Monthly" {$optionMonthly}>по месяцам
              <option value="Weekly" {$optionWeekly}>по неделям
              <option value="Daily" {$optionDaily}>по дням
            </select>
          </td>
          <td><input type="submit" name="submit" value="Изменить значение"></td>
        </tr>
        </form>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Если вы хотите сменить первичную группировку статистики на Главной странице, выберите необходимое правило.
      </td></tr>

      <tr><td colspan="3"><hr size="1"></td></tr>
      <tr><td colspan="2" style="text-align:justify;" width="200">
      Нажмите на эту кнопку, чтобы ПОЛНОСТЬЮ УДАЛИТЬ содержимое БД со статистикой.<br>ВНИМАНИЕ! Отменить это действие после его выполнения невозможно! Используйте данную функциональную возможность только при крайней необходимости (например: обновление БД происходит некорректно).
      </td>
        <td colspan="3" style="text-align:center;">
          <input type="submit" value="Удалить статистику" onClick="my_confirm('Вы уверены, что хотите ПОЛНОСТЬЮ УДАЛИТЬ СТАТИСТИКУ?','{$pageVars.uri}&action=eraseAllStats')">
        </td>
      </tr>

      </table>

