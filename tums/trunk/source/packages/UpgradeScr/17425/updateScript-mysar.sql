SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL';

CREATE  TABLE IF NOT EXISTS `mysar`.`sessions` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT ,
  `startdatetime` DATETIME NULL DEFAULT NULL ,
  `enddatetime` DATETIME NULL DEFAULT NULL ,
  `datain` INT(11) NULL DEFAULT NULL ,
  `dataout` INT(11) NULL DEFAULT NULL ,
  `cachein` INT(11) NULL DEFAULT NULL ,
  `cacheout` INT(11) NULL DEFAULT NULL ,
  `user` VARCHAR(100) NULL DEFAULT NULL ,
  `macAddress` VARCHAR(60) NULL DEFAULT NULL ,
  `siteName` VARCHAR(45) NULL DEFAULT NULL ,
  `sessionTime` FLOAT NULL DEFAULT NULL ,
  `hostnamesID` BIGINT(20) UNSIGNED NOT NULL ,
  `sitesID` BIGINT(20) UNSIGNED NOT NULL ,
  `usersID` BIGINT(20) UNSIGNED NULL DEFAULT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_sessions_hostnames` (`hostnamesID` ASC) ,
  INDEX `user` (`user` ASC) ,
  INDEX `sdatetime` (`startdatetime` ASC) ,
  INDEX `edatetime` (`enddatetime` ASC) ,
  INDEX `sitename` (`siteName` ASC) ,
  INDEX `fk_sessions_sites1` (`sitesID` ASC) ,
  INDEX `fk_sessions_users1` (`usersID` ASC) ,
  CONSTRAINT `fk_sessions_hostnames`
    FOREIGN KEY (`hostnamesID` )
    REFERENCES `mysar`.`hostnames` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_sessions_sites1`
    FOREIGN KEY (`sitesID` )
    REFERENCES `mysar`.`sites` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_sessions_users1`
    FOREIGN KEY (`usersID` )
    REFERENCES `mysar`.`users` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1
COLLATE = latin1_swedish_ci;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

ALTER TABLE `mysar`.`traffic` ADD COLUMN `bytesOut` BIGINT(20) UNSIGNED NULL DEFAULT NULL  AFTER `bytes` , ADD COLUMN `sessionsID` BIGINT(20) NULL DEFAULT NULL  AFTER `usersID` , CHANGE COLUMN `date` `date` DATE NOT NULL DEFAULT 0  , CHANGE COLUMN `time` `time` TIME NOT NULL DEFAULT 0  , CHANGE COLUMN `usersID` `usersID` BIGINT(20) UNSIGNED NOT NULL  , 
ADD INDEX `fk_traffic_sessions1` (`sessionsID` ASC) 
, ADD INDEX `fk_traffic_sites` (`sitesID` ASC) 
, ADD INDEX `fk_traffic_users1` (`usersID` ASC) 
, DROP INDEX `date_ip_sitesID_usersID` 
, ADD INDEX `date_ip_sitesID_usersID` (`date` ASC, `ip` ASC) ;

ALTER TABLE `mysar`.`trafficSummaries` DROP COLUMN `sitesID` , DROP COLUMN `usersID` , ADD COLUMN `sitesID` BIGINT(20) UNSIGNED NULL DEFAULT 0  AFTER `outCache` , ADD COLUMN `usersID` BIGINT(20) UNSIGNED NULL DEFAULT 0  AFTER `ip` , 
ADD INDEX `fk_trafficSummaries_sites1` (`sitesID` ASC) 
, ADD INDEX `fk_trafficSummaries_users1` (`usersID` ASC) 
, DROP INDEX `date_ip_usersID_sitesID_summaryTime` 
, ADD INDEX `date_ip_usersID_sitesID_summaryTime` (`date` ASC, `ip` ASC, `summaryTime` ASC) ;

ALTER TABLE `mysar`.`users` ADD COLUMN `ip` INT(10) UNSIGNED NULL DEFAULT NULL  AFTER `date` , ADD COLUMN `macAddress` VARCHAR(60) NULL DEFAULT NULL  AFTER `date` 
, ADD INDEX `ip` (`ip` ASC) 
, ADD INDEX `macaddr` (`macAddress` ASC) ;


ALTER TABLE `mysar`.`users` DROP INDEX `date_authuser`,ADD INDEX `date_authuser` ( `date` ) 
