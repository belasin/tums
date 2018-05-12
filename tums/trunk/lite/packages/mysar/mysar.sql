-- MySQL dump 10.11
--
-- Host: localhost    Database: mysar
-- ------------------------------------------------------
-- Server version	5.0.32-Debian_7etch1-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `config`
--

use mysar;
GRANT ALL ON mysar.* to mysar@localhost identified by 'mysar';

DROP TABLE IF EXISTS `config`;
CREATE TABLE `config` (
  `name` varchar(255) NOT NULL default '',
  `value` varchar(255) NOT NULL default '',
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `config`
--

LOCK TABLES `config` WRITE;
/*!40000 ALTER TABLE `config` DISABLE KEYS */;
INSERT INTO `config` VALUES ('lastTimestamp','0'),('lastCleanUp','0000-00-00'),('defaultindexOrderBy','date'),('defaultindexOrderMethod','DESC'),('lastImportedRecordsNumber','0'),('defaultDateTimeOrderBy','time'),('defaultindexByteUnit','M'),('defaultIPSummaryOrderBy','cachePercent'),('defaultIPSummaryOrderMethod','DESC'),('defaultIPSummaryByteUnit','M'),('defaultIPSitesSummaryOrderBy','bytes'),('defaultIPSitesSummaryOrderMethod','DESC'),('defaultIPSitesSummaryByteUnit','M'),('defaultDateTimeOrderMethod','DESC'),('defaultAllSitesOrderBy','cachePercent'),('defaultAllSitesOrderMethod','DESC'),('defaultAllSitesByteUnit','M'),('defaultDateTimeByteUnit','K'),('defaultSiteUsersOrderBy','bytes'),('defaultSiteUsersOrderMethod','DESC'),('defaultSiteUsersByteUnit','M'),('keepHistoryDays','32'),('squidLogPath','/var/log/squid/access.log'),('schemaVersion','3'),('resolveClients','enabled'),('mysarImporter','enabled'),('topGrouping','Daily');
/*!40000 ALTER TABLE `config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hostnames`
--

DROP TABLE IF EXISTS `hostnames`;
CREATE TABLE `hostnames` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `ip` int(10) unsigned NOT NULL default '0',
  `description` varchar(50) NOT NULL default '',
  `isResolved` tinyint(3) unsigned NOT NULL default '0',
  `hostname` varchar(255) NOT NULL default '',
  PRIMARY KEY  (`id`),
  KEY `isResolved` (`isResolved`),
  KEY `ip` (`ip`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `hostnames`
--

LOCK TABLES `hostnames` WRITE;
/*!40000 ALTER TABLE `hostnames` DISABLE KEYS */;
/*!40000 ALTER TABLE `hostnames` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sites`
--

DROP TABLE IF EXISTS `sites`;
CREATE TABLE `sites` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `date` date NOT NULL default '0000-00-00',
  `site` varchar(255) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `date_site` (`date`,`site`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `sites`
--

LOCK TABLES `sites` WRITE;
/*!40000 ALTER TABLE `sites` DISABLE KEYS */;
/*!40000 ALTER TABLE `sites` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `traffic`
--

DROP TABLE IF EXISTS `traffic`;
CREATE TABLE `traffic` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `date` date NOT NULL default '0000-00-00',
  `time` time NOT NULL default '00:00:00',
  `ip` int(10) unsigned NOT NULL default '0',
  `resultCode` varchar(50) NOT NULL default '',
  `bytes` bigint(20) unsigned NOT NULL default '0',
  `url` text NOT NULL,
  `authuser` varchar(30) NOT NULL default '',
  `sitesID` bigint(20) unsigned NOT NULL default '0',
  `usersID` bigint(20) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  KEY `date_ip_sitesID_usersID` (`date`,`ip`,`sitesID`,`usersID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `traffic`
--

LOCK TABLES `traffic` WRITE;
/*!40000 ALTER TABLE `traffic` DISABLE KEYS */;
/*!40000 ALTER TABLE `traffic` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trafficSummaries`
--

DROP TABLE IF EXISTS `trafficSummaries`;
CREATE TABLE `trafficSummaries` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `date` date NOT NULL default '0000-00-00',
  `ip` int(10) unsigned NOT NULL default '0',
  `usersID` bigint(20) unsigned NOT NULL default '0',
  `inCache` bigint(20) unsigned NOT NULL default '0',
  `outCache` bigint(20) unsigned NOT NULL default '0',
  `sitesID` bigint(20) unsigned NOT NULL default '0',
  `summaryTime` tinyint(3) unsigned NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `date_ip_usersID_sitesID_summaryTime` (`date`,`ip`,`usersID`,`sitesID`,`summaryTime`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `trafficSummaries`
--

LOCK TABLES `trafficSummaries` WRITE;
/*!40000 ALTER TABLE `trafficSummaries` DISABLE KEYS */;
/*!40000 ALTER TABLE `trafficSummaries` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `authuser` varchar(50) NOT NULL default '',
  `date` date NOT NULL default '0000-00-00',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `date_authuser` (`date`,`authuser`),
  KEY `authuser` (`authuser`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2007-08-08 15:57:49
