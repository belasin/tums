echo \#\!/bin/bash > /usr/local/tcs/tums/syscripts/availVersion.sh
echo "/usr/bin/emerge -pq  --nospinner \$1 | /bin/grep \$1| /bin/awk '{{{ print \$4 }}}' 2>&1" >> /usr/local/tcs/tums/syscripts/availVersion.sh