#!/bin/sh

rm /etc/cron.d/tums
cp /usr/local/tcs/tums/configs/tums.cron /etc/cron.d/tums

mysql --user=root --password=thusa123 < /usr/local/tcs/tums/packages/UpgradeScr/17425/updateScript-mysar.sql
