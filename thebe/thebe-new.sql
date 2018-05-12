CREATE TABLE `backuplog` (
  `id` int(11) NOT NULL auto_increment,
  `sid` int(11) default NULL,
  `type` varchar(255) default NULL,
  `success` int(11) default NULL,
  `date` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `domaingroup` (
  `id` int(11) NOT NULL auto_increment,
  `did` int(11) default NULL,
  `gid` int(11) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `domains` (
  `id` int(11) NOT NULL auto_increment,
  `domain` varchar(255) default NULL,
  `registrant` varchar(255) default NULL,
  `addresspost` varchar(255) default NULL,
  `addressstreet` varchar(255) default NULL,
  `phonenum` varchar(255) default NULL,
  `email` varchar(255) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `groups` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(255) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `isdsl` (
  `id` int(11) NOT NULL auto_increment,
  `gid` int(11) default NULL,
  `linetag` varchar(128) default NULL,
  `gateway` varchar(20) default NULL,
  `name` varchar(128) default NULL,
  `hash` varchar(255) default NULL,
  `svsdescrip` varchar(255) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `log` (
  `id` int(11) NOT NULL auto_increment,
  `sid` int(11) default NULL,
  `type` varchar(255) default NULL,
  `message` varchar(255) default NULL,
  `date` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `pending` (
  `id` int(11) NOT NULL auto_increment,
  `uid` int(11) default NULL,
  `sid` int(11) default NULL,
  `type` text,
  `detail` text,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `server` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(255) default NULL,
  `hostname` varchar(255) default NULL,
  `skey` varchar(255) default NULL,
  `lasthost` varchar(255) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `serverconfigs` (
  `id` int(11) NOT NULL auto_increment,
  `gid` int(11) default NULL,
  `description` varchar(255) default NULL,
  `filename` varchar(255) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `serverdomains` (
  `id` int(11) NOT NULL auto_increment,
  `sid` int(11) default NULL,
  `domain` varchar(255) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `servergroup` (
  `id` int(11) NOT NULL auto_increment,
  `gid` int(11) default NULL,
  `sid` int(11) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `serverusers` (
  `id` int(11) NOT NULL auto_increment,
  `sid` int(11) default NULL,
  `domain` varchar(255) default NULL,
  `name` varchar(255) default NULL,
  `giveName` varchar(255) default NULL,
  `sn` varchar(255) default NULL,
  `cn` varchar(255) default NULL,
  `uid` varchar(255) default NULL,
  `gid` varchar(255) default NULL,
  `emp` varchar(255) default NULL,
  `active` varchar(255) default NULL,
  `mail` varchar(255) default NULL,
  `mailForward` varchar(255) default NULL,
  `mailAlias` varchar(255) default NULL,
  `ntPass` varchar(255) default NULL,
  `password` varchar(255) default NULL,
  `lmPass` varchar(255) default NULL,
  `samSid` varchar(255) default NULL,
  `pgSid` varchar(255) default NULL,
  `vacation` text,
  `vacEnable` smallint(6) default NULL,
  `flags` varchar(255) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `updates` (
  `id` int(11) NOT NULL auto_increment,
  `sid` int(11) default NULL,
  `package` varchar(255) default NULL,
  `date` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `applied` int(11) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `usergroup` (
  `id` int(11) NOT NULL auto_increment,
  `uid` int(11) default NULL,
  `gid` int(11) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `users` (
  `id` int(11) NOT NULL auto_increment,
  `username` varchar(255) default NULL,
  `password` varchar(255) default NULL,
  `fullname` varchar(255) default NULL,
  `email` varchar(255) default NULL,
  `company` varchar(255) default NULL, 
  `address` varchar(255) default NULL, 
  `address1` varchar(255) default NULL, 
  `address2` varchar(255) default NULL, 
  `address3` varchar(255) default NULL, 
  `phone` varchar(255) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


/*
R 4

CREATE TABLE `transactionlog` (
  `id` int(11) NOT NULL auto_increment,
  `orderid` int(11) default NULL,
  `rcode`   varchar(255) default NULL,
  `tdata`  TEXT default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

R 3

ALTER TABLE `users` ADD (
    `emailConfirmed` smallint(6) default NULL, 
    `accountActive`  smallint(6) default NULL, 
    `zaId`           varchar(14) default NULL,
    `country`        varchar(255) default NULL,
    `acthash`        varchar(255) default NULL
);

*/

/*

R2
ALTER TABLE `users` ADD (
  `fullname` varchar(255) default NULL,
  `company` varchar(255) default NULL, 
  `address` varchar(255) default NULL, 
  `address1` varchar(255) default NULL, 
  `address2` varchar(255) default NULL, 
  `address3` varchar(255) default NULL, 
  `phone` varchar(255) default NULL);


ALTER TABLE `server` ADD (
    `lastversion` varchar(255) default NULL,
    `support` varchar(255) default NULL);

CREATE TABLE `orders` (
  `id` int(11) NOT NULL auto_increment,
  `uid` int(11) default NULL,
  `sid` int(11) default NULL, 
  `name` varchar(255) default NULL,
  `hostname` varchar(255) default NULL, 
  `type`    varchar(255) default NULL,
  `support` varchar(255) default NULL,
  `status`  varchar(255) default NULL,
  `created` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `modified` timestamp NOT NULL,

  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

ALTER TABLE `orders` ADD (
  `created` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `modified` timestamp NOT NULL);



*/
