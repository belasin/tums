/*
 Program: mysar, File: database.c
 Copyright 2007, Cassiano Martin <cassiano@polaco.pro.br>

 Source is based on MySar 1.x importer, written by David 'scuzzy' Todd <mobilepolice@gmail.com>

  
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

#include <stdio.h>
#include <stdlib.h>
#include <mysql/mysql.h>
#include <string.h>
#include <time.h>

#include "mysar.h"
#include "db_layout.h"

extern MYSQL	*mysql;

// Tables to clean in 2.x version
char *cleanTables[]  = { "sites", "traffic", "trafficSummaries", "users" };

void MySAR_db_startup()
{
	// Establish our connection to the MySQL Server.
	mysql = mysql_init(NULL);

	if (!mysql_real_connect(mysql, config->dbserver, config->dbuser, config->dbpass, config->dbname, 0, NULL, 0))
	{
		MySAR_print(MSG_ERROR, "mysql_real_connect() in main() %s", mysql_error(mysql));
	}
	else {
		MySAR_print(MSG_DEBUG, "Connection established to MySQL server.");
		config->db_conn_open = 1;
	}
}

void MySAR_db_rollback()
{
	if (mysql_rollback(mysql)) 
	{
		printf("Argggghhh! Error!!! Can't rollback -> %s\n", mysql_error(mysql));
	}
}

void MySAR_db_shutdown()
{
	mysql_close(mysql);
}

void MySAR_db_create()
{
	unsigned int i;
	char sql[512];
	char mysql_pwd[50], mysql_user[50], mysql_host[50], mysql_database[50], mysql_client[50];
	char mysar_pwd[50], mysar_user[50];


	MySAR_print(MSG_NOTICE, "WARNING!! This will generate a new database for storing the logs.");
	MySAR_print(MSG_NOTICE, "Any existing database with the same name, will be dropped!!");
	MySAR_print(MSG_NOTICE, "You need to supply MySQL administrative user, and password.\n");
	MySAR_print(MSG_NOTICE, "If your server is running on another machine, remember to supply the correct hostname for this machine.");
	MySAR_print(MSG_NOTICE, "MySQL needs to this information to allow remote connection to the database. incorrect parameters will result in failure.");
	MySAR_print(MSG_NOTICE, "Be careful when you are behind a NATed server. MySQL server will see only your external IP.\n");
	MySAR_print(MSG_NOTICE, "Leaving fields in blank, the default values will taken from config file, except for the MySQL Admin password.\n");


	MySAR_print(MSG_NOTICE | MSG_NO_CRLF, "Enter MySQL administrative User:     (default: root) ");			MySAR_readconsole(mysql_user);
	MySAR_print(MSG_NOTICE | MSG_NO_CRLF, "Enter MySQL administrative Password: (default: blank) ");		MySAR_readconsole(mysql_pwd);
	MySAR_print(MSG_NOTICE | MSG_NO_CRLF, "Location of the database server:     (default: %s) ", config->dbserver);	MySAR_readconsole(mysql_host);
	MySAR_print(MSG_NOTICE | MSG_NO_CRLF, "This Machine Hostname or IP:         (default: localhost) ");		MySAR_readconsole(mysql_client);
	MySAR_print(MSG_NOTICE | MSG_NO_CRLF, "Database name to create:             (default: %s) ", config->dbname);	MySAR_readconsole(mysql_database);
	MySAR_print(MSG_NOTICE | MSG_NO_CRLF, "MySAR database username:             (default: %s) ", config->dbuser);	MySAR_readconsole(mysar_user);
	MySAR_print(MSG_NOTICE | MSG_NO_CRLF, "MySAR database password:             (default: %s) ", config->dbpass);	MySAR_readconsole(mysar_pwd);

	if (mysql_user[0]=='\0') strncpy(mysql_user, "root", sizeof(mysql_user));
	if (mysql_host[0]=='\0') strncpy(mysql_host, config->dbserver, sizeof(mysql_host));
	if (mysql_database[0]=='\0') strncpy(mysql_database, config->dbname, sizeof(mysql_database));
	if (mysql_client[0]=='\0') strncpy(mysql_client, "localhost", sizeof(mysql_client));

	if (mysar_user[0]=='\0') strncpy(mysar_user, config->dbuser, sizeof(mysar_user));
	if (mysar_pwd[0]=='\0') strncpy(mysar_pwd, config->dbpass, sizeof(mysar_pwd));

	// Establish our connection to the MySQL Server.
	mysql = mysql_init(NULL);
	if (!mysql_real_connect(mysql, mysql_host, mysql_user, mysql_pwd, NULL, 0, NULL, 0)) 
		MySAR_print(MSG_ERROR, "Error connection to the server! MySQL reported: %s", mysql_error(mysql));

	MySAR_print(MSG_NOTICE, "\nDropping any existing databases..");

	snprintf(sql, sizeof(sql), "DROP DATABASE IF EXISTS %s", mysql_database);
	MySAR_push_query(sql);
	snprintf(sql, sizeof(sql), "CREATE DATABASE %s", mysql_database);
	MySAR_push_query(sql);

	// quit if could not select database
	if (mysql_select_db(mysql, mysql_database))
		MySAR_print(MSG_ERROR, "Could not select the database!");

	MySAR_print(MSG_NOTICE, "Generating tables...");
	// generate db structure
	for (i=0;i<=sizeof(db_default_tables)/4-1;i++)
		MySAR_push_query((char *)db_default_tables[i]);

	MySAR_print(MSG_NOTICE, "Setting default values...");
	// insert default values
	for (i=0;i<=sizeof(db_default_values)/4-1;i++)
		MySAR_push_query((char *)db_default_values[i]);

	snprintf(sql, sizeof(sql), "GRANT ALL ON %s.* TO %s@%s IDENTIFIED BY '%s'", mysql_database, mysar_user, mysql_client, mysar_pwd);
	MySAR_push_query(sql);

	// reload privileges tables
	snprintf(sql, sizeof(sql), "FLUSH PRIVILEGES");
	MySAR_push_query(sql);

	MySAR_print(MSG_NOTICE, "Done!");

	MySAR_db_shutdown();

	// bye!!
	exit(EXIT_SUCCESS);
} 

void MySAR_db_cleanup()
{
	char cleantill[15];
	int keepdays;
	char query[512];
	char today[11] = {0};
	unsigned int cleanTablesCount;
	struct tm t_result;
	time_t time_tm_cleanup;

	long int config_int_hist = strtol(config->historydays, NULL, 0);

	// Get today's Date
	time_tm_cleanup = MySAR_current_time();
	localtime_r(&time_tm_cleanup, &t_result);

	strftime(today, sizeof(today), "%Y-%m-%d", &t_result);

	// Calculate the date difference (Keep time)
	time_tm_cleanup = time_tm_cleanup - (config_int_hist * 86400);

	MySAR_print(MSG_NOTICE, "Last Database cleanup performed on %s", config->lastcleanup);
	MySAR_print(MSG_NOTICE, "History keep days: %s", config->historydays);
	MySAR_print(MSG_NOTICE, "Current Date %s", today);

	if (strcmp(today,config->lastcleanup) != 0) 
	{
		localtime_r(&time_tm_cleanup, &t_result);
		strftime(cleantill, sizeof(cleantill), "%Y-%m-%d", &t_result);

		MySAR_print(MSG_NOTICE, "\nDatabase Cleanup. Removing entries dated back to %s", cleantill);
		for(cleanTablesCount=0; cleanTablesCount<=(sizeof(cleanTables)/4-1); cleanTablesCount++)
		{
			memset(&query, 0, sizeof(query));
			sprintf(query, "DELETE FROM %s WHERE date < '%s'", cleanTables[cleanTablesCount], cleantill);

			MySAR_push_query(query);

			MySAR_print(MSG_NOTICE, "Table: %17s Affected Rows: %5lld", cleanTables[cleanTablesCount], mysql_affected_rows(mysql));
		}

		// Update last cleanup date
		MySAR_update_config(today, "lastCleanUp");
		MySAR_print(MSG_NOTICE, "Finished cleanup routine.\n");

		// increase db optimizer counter
		config->optimize_count++;

		keepdays=atoi(config->historydays);
		if (config->optimize_count >= (long)keepdays)
		{
			config->optimize_count=0;
			MySAR_print(MSG_NOTICE, "Automatic database Optimize will run now.");
			MySAR_print(MSG_NOTICE, "Database reached %d days without optimization", keepdays);

			// run optimization
			MySAR_db_optimize();
		}

		MySAR_update_config_long(config->optimize_count, "optimizeCounter");
	}

}

void MySAR_db_optimize()
{
	unsigned int optimizeTablesCount;
	char query[512];

	MySAR_print(MSG_NOTICE, "\nDatabase Optimize is in progress...");
	for(optimizeTablesCount=0; optimizeTablesCount<=(sizeof(cleanTables)/4-1); optimizeTablesCount++)
	{
		snprintf(query, sizeof(query), "OPTIMIZE TABLE %s", cleanTables[optimizeTablesCount]);
		MySAR_print(MSG_NOTICE | MSG_NO_CRLF, "Table: %17s Optimization... ", cleanTables[optimizeTablesCount]);

		// push query and free
		MySAR_push_query_free(query);
		MySAR_print(MSG_NOTICE, "Done!");
	}

	MySAR_print(MSG_NOTICE, "Finished optimization routine.\n");

	MySAR_db_shutdown();
	exit(EXIT_SUCCESS);
}
