#!/bin/sh
/usr/sbin/smartctl -H /dev/$1 | /bin/grep SMART
