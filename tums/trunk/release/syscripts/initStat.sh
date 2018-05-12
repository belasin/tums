#!/bin/sh
/etc/init.d/$1 status | grep status  2>&1
