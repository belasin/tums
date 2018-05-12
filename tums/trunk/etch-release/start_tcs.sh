#!/bin/bash
# Remove the cron, ASAP
rm /etc/cron.d/tumsreboot
#Cleanup
/usr/local/tcs/tums/configurator --upgrade > /dev/null 2>&1

killall tums > /dev/null 2>&1
killall tums-fc > /dev/null 2>&1
killall -r exilog > /dev/null 2>&1
killall fprobe  > /dev/null 2>&1

sleep 10 
killall -9 tums  > /dev/null 2>&1
killall -9 tums-fc  > /dev/null 2>&1

export PYTHONPATH='/usr/local/tcs/tums'
/usr/local/tcs/tums/tums  > /dev/null 2>&1
/usr/local/tcs/tums/tums-fc  > /dev/null 2>&1
/usr/local/tcs/exilog-tums/exilog_agent.pl > /dev/null 2>&1


