#!/bin/bash
cd /etc/openvpn/easy-rsa
source vars
./clean-all
echo "Hit enter alot here"
./build-ca
./build-dh
echo "Hit enter alot again, then just choose 'y'"
./build-key-server vpn
