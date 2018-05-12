#!/usr/bin/python

import Database 

flowDb = Database.AggregatorDatabase()

portTotal = flowDb.getVolumeRecByIp(05, 2007,'172.31.0.212')

print [i for i in portTotal]
