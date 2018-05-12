#!/bin/sh

if [ ! -e /tmp/periodicRunning ]; then
    if [ -e /usr/local/tcs/tums/syscripts/periodic ]; then
        echo `date` > /tmp/periodicRunning
    
        mv /usr/local/tcs/tums/syscripts/periodic /tmp/periodic

        echo `date` -- Started periodic run -- >> /var/log/tums-periodic.log
        bash /tmp/periodic >> /var/log/tums-periodic.log
        echo `date` -- Ended periodic run -- >> /var/log/tums-periodic.log

        rm /tmp/periodicRunning
    fi
fi

rm /var/log/tums.log.11 > /dev/null 2>&1
rm /var/log/tums-proxy.log.11 > /dev/null 2>&1
rm /var/log/tums-fc.log.11 > /dev/null 2>&1
