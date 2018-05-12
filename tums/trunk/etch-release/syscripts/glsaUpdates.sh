#!/bin/bash
/usr/bin/glsa-check -ln affected | /bin/grep -v "\[A\]" 2>/dev/null
