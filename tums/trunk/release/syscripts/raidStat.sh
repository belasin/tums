#!/bin/bash
/bin/cat /proc/mdstat | /bin/grep -v Person | /bin/grep -v unused
