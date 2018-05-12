#!/bin/bash

/bin/df -h | /bin/grep -vE "(udev|varrun|varlock|procbus|devsh|lrm|tmp)" | /bin/grep -v none | /bin/grep -v File

