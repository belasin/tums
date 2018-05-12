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

use asteriskcdr;
GRANT ALL ON asteriskcdr.* to asteriskcdr@localhost identified by 'asteriskcdr';

CREATE TABLE IF NOT EXISTS `cdr` (
    `calldate` datetime NOT NULL default '0000-00-00 00:00:00',
    `clid` varchar(80) NOT NULL default '',
    `src` varchar(80) NOT NULL default '',
    `dst` varchar(80) NOT NULL default '',
    `dcontext` varchar(80) NOT NULL default '', 
    `channel` varchar(80) NOT NULL default '',
    `dstchannel` varchar(80) NOT NULL default '',
    `lastapp` varchar(80) NOT NULL default '',
    `lastdata` varchar(80) NOT NULL default '',
    `duration` int(11) NOT NULL default '0',
    `billsec` int(11) NOT NULL default '0',
    `disposition` varchar(45) NOT NULL default '', 
    `amaflags` int(11) NOT NULL default '0',
    `accountcode` varchar(20) NOT NULL default '',
    `userfield` varchar(255) NOT NULL default '',
    `uniqueid` VARCHAR(32) NOT NULL default '',
    KEY `calldate` (`calldate`),
    KEY `dst` (`dst`),
    KEY `accountcode` (`accountcode`),
    KEY `disposition` (`disposition`),
    KEY `uniqueid` (`uniqueid`)
) ENGINE=InnoDB;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
