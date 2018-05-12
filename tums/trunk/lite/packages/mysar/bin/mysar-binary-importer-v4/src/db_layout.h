/*
 Program: mysar, File: db_layout.h
 Copyright 2007, Cassiano Martin <cassiano@polaco.pro.br>
  
 This file is part of mysar.

 mysar is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License version 2 as published by
 the Free Software Foundation.

 mysar is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with mysar; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/





/*
MySar 2.0.12 database layout
+------------------+
| Tables_in_mysar  |
+------------------+
| config           |
| hostnames        |
| sites            |
| traffic          |
| trafficSummaries |
| users            |
+------------------+

Table config
+-------+--------------+------+-----+---------+-------+
| Field | Type         | Null | Key | Default | Extra |
+-------+--------------+------+-----+---------+-------+
| name  | varchar(255) |      | PRI |         |       |
| value | varchar(255) |      |     |         |       |
+-------+--------------+------+-----+---------+-------+

Table hostnames
+-------------+---------------------+------+-----+---------+----------------+
| Field       | Type                | Null | Key | Default | Extra          |
+-------------+---------------------+------+-----+---------+----------------+
| id          | bigint(20) unsigned |      | PRI | NULL    | auto_increment |
| ip          | int(10) unsigned    |      | MUL | 0       |                |
| description | varchar(50)         |      |     |         |                |
| isResolved  | tinyint(3) unsigned |      | MUL | 0       |                |
| hostname    | varchar(255)        |      |     |         |                |
+-------------+---------------------+------+-----+---------+----------------+

Table sites
+-------+---------------------+------+-----+------------+----------------+
| Field | Type                | Null | Key | Default    | Extra          |
+-------+---------------------+------+-----+------------+----------------+
| id    | bigint(20) unsigned |      | PRI | NULL       | auto_increment |
| date  | date                |      | MUL | 0000-00-00 |                |
| site  | varchar(255)        |      |     |            |                |
+-------+---------------------+------+-----+------------+----------------+

Table traffic
+------------+---------------------+------+-----+------------+----------------+
| Field      | Type                | Null | Key | Default    | Extra          |
+------------+---------------------+------+-----+------------+----------------+
| id         | bigint(20) unsigned |      | PRI | NULL       | auto_increment |
| date       | date                |      | MUL | 0000-00-00 |                |
| time       | time                |      |     | 00:00:00   |                |
| ip         | int(10) unsigned    |      |     | 0          |                |
| resultCode | varchar(50)         |      |     |            |                |
| bytes      | bigint(20) unsigned |      |     | 0          |                |
| url        | varchar(255)        |      |     |            |                |
| authuser   | varchar(30)         |      |     |            |                |
| sitesID    | bigint(20) unsigned |      |     | 0          |                |
| usersID    | bigint(20) unsigned |      |     | 0          |                |
+------------+---------------------+------+-----+------------+----------------+

Table trafficSummaries
+-------------+---------------------+------+-----+------------+----------------+
| Field       | Type                | Null | Key | Default    | Extra          |
+-------------+---------------------+------+-----+------------+----------------+
| id          | bigint(20) unsigned |      | PRI | NULL       | auto_increment |
| date        | date                |      | MUL | 0000-00-00 |                |
| ip          | int(10) unsigned    |      |     | 0          |                |
| usersID     | bigint(20) unsigned |      |     | 0          |                |
| inCache     | bigint(20) unsigned |      |     | 0          |                |
| outCache    | bigint(20) unsigned |      |     | 0          |                |
| sitesID     | bigint(20) unsigned |      |     | 0          |                |
| summaryTime | tinyint(3) unsigned |      |     | 0          |                |
+-------------+---------------------+------+-----+------------+----------------+

Table users
+----------+---------------------+------+-----+------------+----------------+
| Field    | Type                | Null | Key | Default    | Extra          |
+----------+---------------------+------+-----+------------+----------------+
| id       | bigint(20) unsigned |      | PRI | NULL       | auto_increment |
| authuser | varchar(50)         |      | MUL |            |                |
| date     | date                |      | MUL | 0000-00-00 |                |
+----------+---------------------+------+-----+------------+----------------+
*/


// some fields have indexes, this slows the import time a little,
// but gives a boost when viewing the report
const char *db_default_tables[] = {
	"CREATE TABLE IF NOT EXISTS config (" \
		"name varchar(255) NOT NULL default ''," \
		"`value` varchar(255) NOT NULL default ''," \
		"UNIQUE KEY name (name)" \
	");",
	//
	"CREATE TABLE IF NOT EXISTS hostnames (" \
		"id bigint(20) unsigned NOT NULL auto_increment," \
		"ip int(10) unsigned NOT NULL default '0'," \
		"description varchar(50) NOT NULL default ''," \
		"isResolved tinyint(3) unsigned NOT NULL default '0'," \
		"hostname varchar(255) NOT NULL default ''," \
		"PRIMARY KEY  (id)," \
		"KEY isResolved (isResolved)," \
		"KEY ip (ip)" \
	");",
	//
	"CREATE TABLE IF NOT EXISTS trafficSummaries (" \
		"id bigint(20) unsigned NOT NULL auto_increment," \
		"`date` date NOT NULL default '0000-00-00'," \
		"ip int(10) unsigned NOT NULL default '0'," \
		"usersID bigint(20) unsigned NOT NULL default '0'," \
		"inCache bigint(20) unsigned NOT NULL default '0'," \
		"outCache bigint(20) unsigned NOT NULL default '0'," \
		"sitesID bigint(20) unsigned NOT NULL default '0'," \
		"summaryTime tinyint(3) unsigned NOT NULL default '0'," \
		"PRIMARY KEY  (id)," \
		"UNIQUE KEY date_ip_usersID_sitesID_summaryTime (`date`,ip,usersID,sitesID,summaryTime)" \
	");",
	//
	"CREATE TABLE IF NOT EXISTS traffic (" \
		"id bigint(20) unsigned NOT NULL auto_increment," \
		"`date` date NOT NULL default '0000-00-00'," \
		"`time` time NOT NULL default '00:00:00'," \
		"ip int(10) unsigned NOT NULL default '0'," \
		"resultCode varchar(50) NOT NULL default ''," \
		"bytes bigint(20) unsigned NOT NULL default '0'," \
		"url varchar(255) NOT NULL default ''," \
		"authuser varchar(30) NOT NULL default ''," \
		"sitesID bigint(20) unsigned NOT NULL default '0'," \
		"usersID bigint(20) unsigned NOT NULL default '0'," \
		"PRIMARY KEY  (id)," \
		"KEY date_ip_sitesID_usersID (`date`,ip,sitesID,usersID)" \
	");",
	//
	"CREATE TABLE IF NOT EXISTS users (" \
		"id bigint(20) unsigned NOT NULL auto_increment," \
		"authuser varchar(50) NOT NULL default ''," \
		"`date` date NOT NULL default '0000-00-00'," \
		"PRIMARY KEY  (id)," \
		"UNIQUE KEY date_authuser (`date`,authuser)," \
		"KEY authuser (authuser)" \
	");",
	//
	"CREATE TABLE IF NOT EXISTS sites (" \
		"id bigint(20) unsigned NOT NULL auto_increment," \
		"`date` date NOT NULL default '0000-00-00'," \
		"site varchar(255) NOT NULL default ''," \
		"PRIMARY KEY  (id)," \
		"UNIQUE KEY date_site (`date`,site)" \
	");"
};

const char *db_default_values[] = {
	"INSERT IGNORE INTO `config` VALUES ('lastTimestamp', '0');",
	"INSERT IGNORE INTO `config` VALUES ('lastCleanUp', '0000-00-00');",
	"INSERT IGNORE INTO `config` VALUES ('defaultindexOrderBy', 'date');",
	"INSERT IGNORE INTO `config` VALUES ('defaultindexOrderMethod', 'DESC');",
	"INSERT IGNORE INTO `config` VALUES ('lastImportedRecordsNumber', '0');",
	"INSERT IGNORE INTO `config` VALUES ('defaultDateTimeOrderBy', 'time');",
	"INSERT IGNORE INTO `config` VALUES ('defaultindexByteUnit', 'M');",
	"INSERT IGNORE INTO `config` VALUES ('defaultIPSummaryOrderBy', 'cachePercent');",
	"INSERT IGNORE INTO `config` VALUES ('defaultIPSummaryOrderMethod', 'DESC');",
	"INSERT IGNORE INTO `config` VALUES ('defaultIPSummaryByteUnit', 'M');",
	"INSERT IGNORE INTO `config` VALUES ('defaultIPSitesSummaryOrderBy', 'bytes');",
	"INSERT IGNORE INTO `config` VALUES ('defaultIPSitesSummaryOrderMethod', 'DESC');",
	"INSERT IGNORE INTO `config` VALUES ('defaultIPSitesSummaryByteUnit', 'M');",
	"INSERT IGNORE INTO `config` VALUES ('defaultDateTimeOrderMethod', 'DESC');",
	"INSERT IGNORE INTO `config` VALUES ('defaultAllSitesOrderBy', 'cachePercent');",
	"INSERT IGNORE INTO `config` VALUES ('defaultAllSitesOrderMethod', 'DESC');",
	"INSERT IGNORE INTO `config` VALUES ('defaultAllSitesByteUnit', 'M');",
	"INSERT IGNORE INTO `config` VALUES ('defaultDateTimeByteUnit', 'K');",
	"INSERT IGNORE INTO `config` VALUES ('defaultSiteUsersOrderBy', 'bytes');",
	"INSERT IGNORE INTO `config` VALUES ('defaultSiteUsersOrderMethod', 'DESC');",
	"INSERT IGNORE INTO `config` VALUES ('defaultSiteUsersByteUnit', 'M');",
	"INSERT IGNORE INTO `config` VALUES ('keepHistoryDays', '32');",
	"INSERT IGNORE INTO `config` VALUES ('squidLogPath', '/var/log/squid/access.log');",
	"INSERT IGNORE INTO `config` VALUES ('schemaVersion', '3');",
	"INSERT IGNORE INTO `config` VALUES ('resolveClients', 'disabled');",
	"INSERT IGNORE INTO `config` VALUES ('mysarImporter', 'enabled');",
	"INSERT IGNORE INTO `config` VALUES ('topGrouping', 'Daily');",
	"INSERT IGNORE INTO `config` VALUES ('lastLogOffset', '0');",
	"INSERT IGNORE INTO `config` VALUES ('firstLogTimestamp', '0');",
	"INSERT IGNORE INTO `config` VALUES ('optimizeCounter', '0');"
};
