#!/bin/sh

# Restart some things that have a history of memory leaks
/etc/init.d/tums stop
/etc/init.d/clamav-daemon restart
/etc/init.d/spamassassin restart
/etc/init.d/tums start

/usr/local/tcs/tums/diskStat.py

if [ -e /usr/local/tcs/tums/packages/nomng ]; then
    # Perform update cache flushing
    /usr/local/tcs/tums/bin/flush_updates
    exit
fi

/usr/bin/wget --no-cache http://updates.thusa.co.za/pubkey.txt -O /usr/local/tcs/tums/thusa-repo-pub
/usr/bin/apt-key add /usr/local/tcs/tums/thusa-repo-pub

if [ ! -e /tmp/dailyRunning ]; then
    echo `date` > /tmp/dailyRunning
    
    rm /usr/local/tcs/tums/syscripts/dailyUpdate-501
    /usr/bin/wget --no-cache http://vulani.net/updates/dailyUpdate-501 -O /usr/local/tcs/tums/syscripts/dailyUpdate-501
    
    # Ensure the update is not one we last performed..
    
    THISHASH=`md5sum /usr/local/tcs/tums/syscripts/dailyUpdate-501 | awk '{print $1}'`
    LASTHASH=`cat /var/log/lastDaily`
    echo $THISHASH
    
    if [ -e /var/log/lastDaily ]; then
        if [ "$LASTHASH" = "$THISHASH" ]; then
            rm /tmp/dailyRunning 
            exit 1
        fi
    fi 
    
    echo $THISHASH > /var/log/lastDaily
    
    echo `date` -- Started daily update -- >> /var/log/tums-daily.log
    echo My hash $LASTHASH >> /var/log/tums-daily.log
    echo Your hash $THISHASH >> /var/log/tums-daily.log
    bash /usr/local/tcs/tums/syscripts/dailyUpdate-501 >> /var/log/tums-daily.log
    echo `date` -- Ended daily update -- >> /var/log/tums-daily.log
    
    /usr/local/tcs/tums/configurator --ssh
    
    /usr/bin/wget --no-cache http://siza.thusa.net/fetch/filter.db -O /usr/local/tcs/tums/filter.db
    /usr/local/tcs/tums/configurator --exim
    /etc/init.d/exim4 restart
    
    # Perform update cache flushing
    /usr/local/tcs/tums/bin/flush_updates
    
    rm /tmp/dailyRunning
fi
