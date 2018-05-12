#!/bin/sh
PS=`ps ax | awk '{{{ print $5 }}}' | grep $1 | grep -v "grep" | grep -v $0`
if [ "$PS" = "" ]; then
    echo $1 stopped
else
    echo $1 started
fi
