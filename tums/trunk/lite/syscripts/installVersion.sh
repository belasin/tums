#!/bin/bash
/usr/bin/qlist -IveqC | /bin/grep $1 | /bin/head -n 1
