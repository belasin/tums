#!/bin/bash
/usr/bin/emerge -pq  --nospinner $1 | /bin/grep $1| /bin/awk '{{{ print $4 }}}' 2>&1
