#!/bin/bash
cd /etc/openvpn/easy-rsa
source vars
./clean-all
echo "Hit enter alot here"
./pkitool --initca 
./build-dh
echo "Hit enter alot again, then just choose 'y'"
./pkitool --server vpn
./revoke-full nothing
