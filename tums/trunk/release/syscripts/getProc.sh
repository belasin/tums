#!/bin/sh
/bin/ps aux | /bin/grep $1 | /usr/bin/head -n 1 
