/*
 Program: mysar, File: sql.c
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
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>

#include "mysar.h"


// MySQL statements for Mysar 2.x
#define xSTMT_INSTRAFFIC	"INSERT INTO traffic(date,time,sitesID,usersID,ip,resultCode,bytes,url,authuser) VALUES (?,?,?,?,?,?,?,?,?)"

#define xSTMT_SELRESOLVED	"SELECT isResolved FROM hostnames WHERE ip=?"
#define xSTMT_INSRESOLVED	"INSERT INTO hostnames (ip, hostname, isResolved) VALUES (?,?,?)"

#define xSTMT_SELSITES		"SELECT id FROM sites WHERE date=? AND site=?"
#define xSTMT_INSSITES		"INSERT INTO sites(site,date) VALUES (?,?)"

#define xSTMT_SELUSERS		"SELECT id FROM users WHERE date=? AND authuser=?"
#define xSTMT_INSUSERS		"INSERT INTO users(authuser,date) VALUES (?,?)"

#define xSTMT_INSSUMS_IN	"INSERT INTO trafficSummaries(date,ip,inCache,sitesID,usersID,summaryTime) VALUES (?,?,?,?,?,?)"
#define xSTMT_INSSUMS_OUT	"INSERT INTO trafficSummaries(date,ip,outCache,sitesID,usersID,summaryTime) VALUES (?,?,?,?,?,?)"

#define xSTMT_UPDSUMS_IN	"UPDATE trafficSummaries SET inCache=inCache+? WHERE date=? AND ip=? AND sitesID=? AND usersID=? AND summaryTime=?"
#define xSTMT_UPDSUMS_OUT	"UPDATE trafficSummaries SET outCache=outCache+? WHERE date=? AND ip=? AND sitesID=? AND usersID=? AND summaryTime=?"


// MYSQL Data Types
MYSQL		*mysql;

MYSQL_STMT	*insert_traffic;
MYSQL_STMT	*insert_resolved;
MYSQL_STMT	*select_resolved;
MYSQL_STMT	*insert_sites;
MYSQL_STMT	*select_sites;
MYSQL_STMT	*insert_users;
MYSQL_STMT	*select_users;
MYSQL_STMT	*update_sums_in;
MYSQL_STMT	*update_sums_out;
MYSQL_STMT	*insert_sums_in;
MYSQL_STMT	*insert_sums_out;

MYSQL_BIND	bind_insert_traffic[6];
MYSQL_BIND	bind_insert_resolved[3];
MYSQL_BIND	bind_select_resolved[1];
MYSQL_BIND	bind_insert_sites[2];
MYSQL_BIND	bind_select_sites[2];

MYSQL_BIND	bind_insert_users[2];
MYSQL_BIND	bind_select_users[2];

MYSQL_BIND	bind_update_sums_in[6];
MYSQL_BIND	bind_update_sums_out[6];

MYSQL_BIND	bind_insert_sums_in[6];
MYSQL_BIND	bind_insert_sums_out[6];

MYSQL_BIND	bind_output[1];

unsigned long	len[1];
char		bind_data[50];

data_store	record;

// update 'value' in 'config' where name is 'name'
int MySAR_update_config(char *value, char *name)
{
	char query[512];
	
	//snprintf(query, sizeof(query), "UPDATE config SET value='%s' WHERE name='%s'", value, name);
	snprintf(query, sizeof(query), "INSERT INTO config (name,value) VALUES ('%s','%s') ON DUPLICATE KEY UPDATE value=VALUES(value)", name, value);
	MySAR_push_query_free(query);
	
	return 0;
}

int MySAR_update_config_long(long value, char *name)
{
	char buf[40];

	snprintf(buf, sizeof(buf), "%ld", value);
	MySAR_update_config(buf, name);

	return 0;
}

long MySAR_fetch_config_long(char *name)
{
	char *val;

	val=MySAR_fetch_configvalue(name);

	// crap mysql
	return atol(val);
}

// retrieve 'value' from 'config' where name is 'name'
// return with select_field.
char *MySAR_fetch_configvalue(char *name)
{
	char query[512];
	char *return_result;
	MYSQL_ROW row;
	MYSQL_RES *result;
	
	snprintf(query, sizeof(query), "SELECT value FROM config WHERE name='%s'", name);
	MySAR_push_query(query);

	if ((result = mysql_use_result(mysql)) == NULL)
		return "";
	
	if ((row = mysql_fetch_row(result)) == NULL)
		return "";
	
	asprintf(&return_result, "%s", row[0]);
	mysql_free_result(result);
	
	return return_result;
}

// send a query to the MySQL database, free the result
int MySAR_push_query_free(char *query)
{
	int ret;
	MYSQL_RES *result;

	if ((ret = mysql_real_query(mysql, query, (unsigned int) strlen(query))) != 0)
		MySAR_print(MSG_ERROR, "mysql_real_query() in MySAR_push_query_free() %s", mysql_error(mysql));

	// some data returned
	if ((result = mysql_use_result(mysql)) != NULL)
		mysql_free_result(result);
	
	return 0;
}

// send a query and retain the result
int MySAR_push_query(char *query)
{
	int ret;
	if ((ret = mysql_real_query(mysql, query, (unsigned int) strlen(query))) != 0)
		MySAR_print(MSG_ERROR, "mysql_real_query() in MySAR_push_query() %s", mysql_error(mysql));
	
	return 0;
}

// free the used statements
void MySAR_free_mysql_statements()
{
	MySAR_print(MSG_NOTICE, "Freeing statements....");

	// free any select results
	mysql_stmt_free_result(select_resolved);
	mysql_stmt_free_result(select_sites);
	mysql_stmt_free_result(select_users);

	mysql_stmt_close(insert_traffic);
	mysql_stmt_close(insert_resolved);
	mysql_stmt_close(select_resolved);
	mysql_stmt_close(insert_sites);
	mysql_stmt_close(select_sites);
	mysql_stmt_close(insert_users);
	mysql_stmt_close(select_users);
	mysql_stmt_close(update_sums_in);
	mysql_stmt_close(update_sums_out);
	mysql_stmt_close(insert_sums_in);
	mysql_stmt_close(insert_sums_out);
}

// used to prepare MySQL statements
void MySAR_prepare_stmt(MYSQL_STMT *stmt, const char *stmt_str, unsigned long length)
{
	if (mysql_stmt_prepare(stmt, stmt_str, length) != 0)
		MySAR_print(MSG_ERROR, "FATAL: Error while preparing MySQL statement: %s", mysql_stmt_error(stmt));

}

// inlining give it a boost, as these routines are called lots of times
inline int MySAR_execute_stmt(MYSQL_STMT *stmt)
{
	int st;

	// this way I can avoid repeating lots of code...
	if ((st=mysql_stmt_execute(stmt)) != 0)
		MySAR_print(MSG_ERROR, "FATAL: Statement Error: %s", mysql_stmt_error(stmt));

	return st;
}

// used to create a bind to retrieve data
inline void MySAR_bind_stmt(MYSQL_STMT *stmt, MYSQL_BIND *bind)
{
	int st;

	if ((st=mysql_stmt_bind_result(stmt, bind)) != 0)
		MySAR_print(MSG_ERROR, "FATAL: Statement Bind Error: %s", mysql_stmt_error(stmt));

}

inline void MySAR_import_traffic()
{
	if (config->importtraffic)
	{
		// Insert our record data into the 'traffic' table
		(void)MySAR_execute_stmt(insert_traffic);
	}
}

inline void MySAR_import_hostnames()
{
	struct sockaddr_in san;
	int fetch_return;
	int san_len;

	// select our statements from the hostnames table.
	(void)MySAR_execute_stmt(select_resolved);
	MySAR_bind_stmt(select_resolved, bind_output);

	fetch_return = mysql_stmt_fetch(select_resolved);
	
	// huh? host is not in table
	// enter this routine only if the host is not on table
	if (fetch_return == MYSQL_NO_DATA) 
	{
		// Get the hostname of the record, if enabled. - if it returns non-zero, use the ip address.
		if (config->resolver)
		{
			// create the socket only if the resolver is enabled
			memset(&san, 0, sizeof(san));
			san.sin_family = AF_INET;
			san.sin_port = htons(0);
			san.sin_addr.s_addr = inet_addr(record.ip);
			memset(&(san.sin_zero), '\0', 8);
			san_len = sizeof(san);
		
			if (getnameinfo((struct sockaddr *)&san, san_len, record.hostname, sizeof(record.hostname), NULL, 0, NI_NAMEREQD) != 0)
			{
				// nope, could not get hostname. use IP instead.
				strcpy(record.hostname, record.ip);
				// set resolved to zero, as we'll try to resolve it later...
				strcpy(record.isResolved, "0");
			}
			else
				strcpy(record.isResolved, "1");
		} 
		else 
		{
			// if resolver disabled, use the IP address
			strcpy(record.hostname, record.ip);
			strcpy(record.isResolved, "0");
		}
		record.l_hostname = strlen(record.hostname);
		record.l_isResolved = strlen(record.isResolved);

		// execute the insert statement
		(void)MySAR_execute_stmt(insert_resolved);

	} 
	else if (fetch_return == 0) 
	{
		// got it
		//if (mysql_stmt_fetch_column(select_resolved, bind_output, 0, 0) == 0)
		//{
		//	snprintf(record.isResolved, sizeof(record.isResolved), "%s", (char *)bind_output[0].buffer);
		//}
		//else
		//	MySAR_print(MSG_ERROR, "mysql_stmt_fetch_column in processing loop %s", mysql_stmt_error(select_resolved));
	} 
	else
		MySAR_print(MSG_ERROR, "Statement Error in MySAR_import_hostnames(): %s", mysql_stmt_error(select_resolved));


	// Free statements
	// hostname search is completed
	mysql_stmt_free_result(select_resolved);
}

inline void MySAR_import_sites()
{
	int fetch_return;

	// execute the statement to find the desired site on the database
	(void)MySAR_execute_stmt(select_sites);
	MySAR_bind_stmt(select_sites, bind_output);

	fetch_return = mysql_stmt_fetch(select_sites);

	// insert it
	if (fetch_return == MYSQL_NO_DATA) 
	{
		if (MySAR_execute_stmt(insert_sites) == 0)
			snprintf(record.siteid, sizeof(record.siteid), "%u", (unsigned int)mysql_stmt_insert_id(insert_sites));
	}
	else if (fetch_return == 0) 
	{
		if (mysql_stmt_fetch_column(select_sites, bind_output, 0, 0) == 0)
			snprintf(record.siteid, sizeof(record.siteid), "%s", (char *)bind_output[0].buffer);
		else
			MySAR_print(MSG_ERROR, "mysql_stmt_fetch_column in process loop %s", mysql_stmt_error(select_sites));
	} 
	else
		MySAR_print(MSG_ERROR, "Statement Error in MySAR_import_sites(): %s", mysql_stmt_error(select_sites));


	record.l_siteid = strlen(record.siteid);
	mysql_stmt_free_result(select_sites);
}

inline void MySAR_import_users()
{
	int fetch_return;

	// execute the statement to find the desired user
	(void)MySAR_execute_stmt(select_users);
	MySAR_bind_stmt(select_users, bind_output);
	
	fetch_return = mysql_stmt_fetch(select_users);
	
	// insert it
	if (fetch_return == MYSQL_NO_DATA) 
	{
		if (MySAR_execute_stmt(insert_users) == 0)
			snprintf(record.usersid, sizeof(record.usersid), "%u", (unsigned int)mysql_stmt_insert_id(insert_users));
	}
	else if (fetch_return == 0) 
	{
		if (mysql_stmt_fetch_column(select_users, bind_output, 0, 0) == 0)
			snprintf(record.usersid, sizeof(record.usersid), "%s", (char *)bind_output[0].buffer);
		else
			MySAR_print(MSG_ERROR, "mysql_stmt_fetch_column in process loop %s", mysql_stmt_error(select_users));
	} 
	else
		MySAR_print(MSG_ERROR, "Statement Error in MySAR_import_users(): %s", mysql_stmt_error(select_users));
	
	record.l_usersid = strlen(record.usersid);
	mysql_stmt_free_result(select_users);
}

inline void MySAR_import_summaries()
{

	if (record.field == TYPE_IN_CACHE) 
	{
		// if the record exists in database...
		(void)MySAR_execute_stmt(update_sums_in);

		if (mysql_stmt_affected_rows(update_sums_in) == 0)
			(void)MySAR_execute_stmt(insert_sums_in);
	} 
	else 
	{
		(void)MySAR_execute_stmt(update_sums_out);

		if (mysql_stmt_affected_rows(update_sums_out) == 0)
			(void)MySAR_execute_stmt(insert_sums_out);
	}
}

void MySAR_prep_mysql(void)
{

	// All prepares are done here. Statements declarations occupies
	// a lot of lines, but they are really FAST!

	// Initialize the Statements
        if((insert_traffic = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  insert_traffic Failed!()");
        if((insert_resolved = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  insert_resolved Failed!()");
        if((select_resolved = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  select_resolved Failed!()");
        if((insert_sites = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  insert_sites Failed!()");
        if((select_sites = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  select_sites Failed!()");
        if((insert_users = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  insert_users Failed!()");
        if((select_users = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  select_users Failed!()");
        if((update_sums_in = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  update_sums_in Failed!()");
        if((update_sums_out = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  update_sums_out Failed!()");
        if((insert_sums_in = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  insert_sums_in Failed!()");
        if((insert_sums_out = mysql_stmt_init(mysql)) == NULL)		MySAR_print(MSG_ERROR, "Error initializing Statement:  insert_sums_out Failed!()");


// Statement Type:      INSERT
// Statement Name:	xSTMT_INSTRAFFIC	"INSERT INTO traffic(date,time,ip,resultCode,bytes,url,authuser) VALUES (?,?,?,?,?,?,?)"
// Table:               traffic
// Function:            Insert our current flat-file record into the
//                      traffic table for later processing.
//
// Status:		ADAPTED and WORKING

        MySAR_prepare_stmt(insert_traffic, xSTMT_INSTRAFFIC, sizeof(xSTMT_INSTRAFFIC));


        memset(bind_insert_traffic, 0, sizeof(bind_insert_traffic));

	// current date
        bind_insert_traffic[0].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[0].buffer = record.date;
        bind_insert_traffic[0].buffer_length = record.l_date;
        bind_insert_traffic[0].is_null = 0;
        bind_insert_traffic[0].length = &record.l_date;

	// current timestamp
        bind_insert_traffic[1].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[1].buffer = record.time;
        bind_insert_traffic[1].buffer_length = record.l_time;
        bind_insert_traffic[1].is_null = 0;
        bind_insert_traffic[1].length = &record.l_time;

	// current SitesID
        bind_insert_traffic[2].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[2].buffer = record.siteid;
        bind_insert_traffic[2].buffer_length = record.l_siteid;
        bind_insert_traffic[2].is_null = 0;
        bind_insert_traffic[2].length = &record.l_siteid;

	// current UserID
        bind_insert_traffic[3].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[3].buffer = record.usersid;
        bind_insert_traffic[3].buffer_length = record.l_usersid;
        bind_insert_traffic[3].is_null = 0;
        bind_insert_traffic[3].length = &record.l_usersid;

	// current IP in net short format
        bind_insert_traffic[4].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[4].buffer = record.ipns;
        bind_insert_traffic[4].buffer_length = record.l_ipns;
        bind_insert_traffic[4].is_null = 0;
        bind_insert_traffic[4].length = &record.l_ipns;

	// Squid cache Result
        bind_insert_traffic[5].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[5].buffer = record.result;
        bind_insert_traffic[5].buffer_length = record.l_result;
        bind_insert_traffic[5].is_null = 0;
        bind_insert_traffic[5].length = &record.l_result;

	// Total bytes used
        bind_insert_traffic[6].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[6].buffer = record.bytes;
        bind_insert_traffic[6].buffer_length = record.l_bytes;
        bind_insert_traffic[6].is_null = 0;
        bind_insert_traffic[6].length = &record.l_bytes;

	// The URL
        bind_insert_traffic[7].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[7].buffer = record.url;
        bind_insert_traffic[7].buffer_length = record.l_url;
        bind_insert_traffic[7].is_null = 0;
        bind_insert_traffic[7].length = &record.l_url;

	// if an user has been authenticated with squid...
        bind_insert_traffic[8].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_traffic[8].buffer = record.authuser;
        bind_insert_traffic[8].buffer_length = record.l_authuser;
        bind_insert_traffic[8].is_null = 0;
        bind_insert_traffic[8].length = &record.l_authuser;


        if(mysql_stmt_bind_param(insert_traffic, bind_insert_traffic) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(insert_traffic));


// Statement Type:	SELECT
// Statement Name:	xSTMT_SELRESOLVED	"SELECT isResolved FROM hostnames WHERE ip=?"
// Table: 		hostnames
// Function:		Make an attempt to retrieve the host in the table to 
//			determine if our record is already present.
//
// Status:		ADAPTED and WORKING

        MySAR_prepare_stmt(select_resolved,xSTMT_SELRESOLVED, sizeof(xSTMT_SELRESOLVED));


        memset(bind_select_resolved, 0, sizeof(bind_select_resolved));

	// get the ID of the hostname
	// ipns is a short for IP NetShort, not the dotted one
        bind_select_resolved[0].buffer_type = MYSQL_TYPE_STRING;
        bind_select_resolved[0].buffer = record.ipns;
        bind_select_resolved[0].buffer_length = record.l_ipns;
        bind_select_resolved[0].is_null = 0;
        bind_select_resolved[0].length = &record.l_ipns;

        if (mysql_stmt_bind_param(select_resolved, bind_select_resolved) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(select_resolved));


// Statement Type:      INSERT
// Statement Name:	xSTMT_INSRESOLVED	"INSERT INTO hostnames (ip, hostname, isResolved) VALUES (?,?)"
// Table:               hostnames
// Function:            Statement select_resolved has returned nothing
//                      or an invalid ID. Insert our record into the database.
//
// Status:		ADAPTED and WORKING

	
        MySAR_prepare_stmt(insert_resolved,xSTMT_INSRESOLVED, sizeof(xSTMT_INSRESOLVED));


        memset(bind_insert_resolved, 0, sizeof(bind_insert_resolved));

	// IP net short
        bind_insert_resolved[0].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_resolved[0].buffer = record.ipns;
        bind_insert_resolved[0].buffer_length = record.l_ipns;
        bind_insert_resolved[0].is_null = 0;
        bind_insert_resolved[0].length = &record.l_ipns;

	// the host name, or the dotted IP, if not DNS resolved
        bind_insert_resolved[1].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_resolved[1].buffer = record.hostname;
        bind_insert_resolved[1].buffer_length = record.l_hostname;
        bind_insert_resolved[1].is_null = 0;
        bind_insert_resolved[1].length = &record.l_hostname;

	// mark the IP record as DNS resolved?
        bind_insert_resolved[2].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_resolved[2].buffer = record.isResolved;
        bind_insert_resolved[2].buffer_length = record.l_isResolved;
        bind_insert_resolved[2].is_null = 0;
        bind_insert_resolved[2].length = &record.l_isResolved;

        if (mysql_stmt_bind_param(insert_resolved, bind_insert_resolved) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(insert_resolved));


// Statement Type:      SELECT
// Statement Name:	xSTMT_SELSITES		"SELECT id FROM sites WHERE date=? AND site=?"
// Table:               sites
// Function:            Search the table for an id where the date
//                      and site name match.
//
// Status:		ADAPTED and WORKING


        MySAR_prepare_stmt(select_sites,xSTMT_SELSITES, sizeof(xSTMT_SELSITES));

	// yeah
        memset(bind_select_sites, 0, sizeof(bind_select_sites));

	// date
        bind_select_sites[0].buffer_type = MYSQL_TYPE_STRING;
        bind_select_sites[0].buffer = record.date;
        bind_select_sites[0].buffer_length = record.l_date;
        bind_select_sites[0].is_null = 0;
        bind_select_sites[0].length = &record.l_date;

	// site URL
        bind_select_sites[1].buffer_type = MYSQL_TYPE_STRING;
        bind_select_sites[1].buffer = record.site;
        bind_select_sites[1].buffer_length = record.l_site;
        bind_select_sites[1].is_null = 0;
        bind_select_sites[1].length = &record.l_site;

        if (mysql_stmt_bind_param(select_sites, bind_select_sites) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(select_sites));


// Statement Type:      INSERT
// Statement Name:	xSTMT_INSSITES		"INSERT INTO sites(site,date) VALUES (?,?)"
// Table:               sites
// Function:            Insert record into table after failure of SELECT.
//
// Status:		ADAPTED and WORKING

        MySAR_prepare_stmt(insert_sites, xSTMT_INSSITES, sizeof(xSTMT_INSSITES));


        memset(bind_insert_sites, 0, sizeof(bind_insert_sites));

	// Site URL
        bind_insert_sites[0].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sites[0].buffer = record.site;
        bind_insert_sites[0].buffer_length = record.l_site;
        bind_insert_sites[0].is_null = 0;
        bind_insert_sites[0].length = &record.l_site;

	// Date
        bind_insert_sites[1].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sites[1].buffer = record.date;
        bind_insert_sites[1].buffer_length = record.l_date;
        bind_insert_sites[1].is_null = 0;
        bind_insert_sites[1].length = &record.l_date;


        if (mysql_stmt_bind_param(insert_sites, bind_insert_sites) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(insert_sites));


// Statement Type:	INSERT
// Statement Name:	xSTMT_INSUSERS		"INSERT INTO users(authuser,date) VALUES (?,?)"
// Table:               users
// Function:            Insert record into table users, if not found
//
// Status:		ADAPTED, WORKING but missing isResolved field

        MySAR_prepare_stmt(insert_users, xSTMT_INSUSERS, sizeof(xSTMT_INSUSERS));


        memset(bind_insert_users, 0, sizeof(bind_insert_users));

	// Authenticated user, or default user if no authentication present
        bind_insert_users[0].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_users[0].buffer = record.authuser;
        bind_insert_users[0].buffer_length = record.l_authuser;
        bind_insert_users[0].is_null = 0;
        bind_insert_users[0].length = &record.l_authuser;

	// current date
        bind_insert_users[1].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_users[1].buffer = record.date;
        bind_insert_users[1].buffer_length = record.l_date;
        bind_insert_users[1].is_null = 0;
        bind_insert_users[1].length = &record.l_date;


        if (mysql_stmt_bind_param(insert_users, bind_insert_users) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(insert_users));


// Statement Type:	SELECT
// Statement Name:	xSTMT_SELUSERS		"SELECT id FROM users WHERE date=? AND authuser=?"
// Table:               users
// Function:            Select a record on the table users
//
// Status:		ADAPTED and WORKING

        MySAR_prepare_stmt(select_users, xSTMT_SELUSERS, sizeof(xSTMT_SELUSERS));


        memset(bind_select_users, 0, sizeof(bind_select_users));

	// current date
        bind_select_users[0].buffer_type = MYSQL_TYPE_STRING;
        bind_select_users[0].buffer = record.date;
        bind_select_users[0].buffer_length = record.l_date;
        bind_select_users[0].is_null = 0;
        bind_select_users[0].length = &record.l_date;

	// Authenticated user, or default user if no authentication present
        bind_select_users[1].buffer_type = MYSQL_TYPE_STRING;
        bind_select_users[1].buffer = record.authuser;
        bind_select_users[1].buffer_length = record.l_authuser;
        bind_select_users[1].is_null = 0;
        bind_select_users[1].length = &record.l_authuser;


        if (mysql_stmt_bind_param(select_users, bind_select_users) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(select_users));


// Statement Type:      UPDATE
// Statement Name:	xSTMT_UPDSUMS_IN	"UPDATE trafficSummaries SET inCache=inCache+? WHERE date=? AND ip=? AND sitesID=? AND usersID=? AND summaryTime=?"
// Table:               trafficSummaries
// Function:            Update the inCache fields.
//
// Status:		ADAPTED and WORKING

        MySAR_prepare_stmt(update_sums_in, xSTMT_UPDSUMS_IN, sizeof(xSTMT_UPDSUMS_IN));


        memset(bind_update_sums_in, 0, sizeof(bind_update_sums_in));

	// Data Size
        bind_update_sums_in[0].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_in[0].buffer = record.bytes;
        bind_update_sums_in[0].buffer_length = record.l_bytes;
        bind_update_sums_in[0].is_null = 0;
        bind_update_sums_in[0].length = &record.l_bytes;

	// Date
        bind_update_sums_in[1].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_in[1].buffer = record.date;
        bind_update_sums_in[1].buffer_length = record.l_date;
        bind_update_sums_in[1].is_null = 0;
        bind_update_sums_in[1].length = &record.l_date;

	// IP in net short format
        bind_update_sums_in[2].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_in[2].buffer = record.ipns;
        bind_update_sums_in[2].buffer_length = record.l_ipns;
        bind_update_sums_in[2].is_null = 0;
        bind_update_sums_in[2].length = &record.l_ipns;

	// The site ID
        bind_update_sums_in[3].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_in[3].buffer = record.siteid;
        bind_update_sums_in[3].buffer_length = record.l_siteid;
        bind_update_sums_in[3].is_null = 0;
        bind_update_sums_in[3].length = &record.l_siteid;

	// The User ID
        bind_update_sums_in[4].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_in[4].buffer = record.usersid;
        bind_update_sums_in[4].buffer_length = record.l_usersid;
        bind_update_sums_in[4].is_null = 0;
        bind_update_sums_in[4].length = &record.l_usersid;

	// Summary Time
        bind_update_sums_in[5].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_in[5].buffer = record.sumtime;
        bind_update_sums_in[5].buffer_length = record.l_sumtime;
        bind_update_sums_in[5].is_null = 0;
        bind_update_sums_in[5].length = &record.l_sumtime;

        if (mysql_stmt_bind_param(update_sums_in, bind_update_sums_in) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(update_sums_in));


// Statement Type:      UPDATE
// Statement Name:	xSTMT_UPDSUMS_OUT	"UPDATE trafficSummaries SET outCache=outCache+? WHERE date=? AND ip=? AND sitesID=? AND usersID=? AND summaryTime=?"
// Table:               trafficSummaries
// Function:            Update the outCache fields.
//
// Status:		ADAPTED and WORKING

        MySAR_prepare_stmt(update_sums_out, xSTMT_UPDSUMS_OUT, sizeof(xSTMT_UPDSUMS_OUT));


        memset(bind_update_sums_out, 0, sizeof(bind_update_sums_out));

	// data size
        bind_update_sums_out[0].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_out[0].buffer = record.bytes;
        bind_update_sums_out[0].buffer_length = record.l_bytes;
        bind_update_sums_out[0].is_null = 0;
        bind_update_sums_out[0].length = &record.l_bytes;

	// date
        bind_update_sums_out[1].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_out[1].buffer = record.date;
        bind_update_sums_out[1].buffer_length = record.l_date;
        bind_update_sums_out[1].is_null = 0;
        bind_update_sums_out[1].length = &record.l_date;

	// ip net short
        bind_update_sums_out[2].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_out[2].buffer = record.ipns;
        bind_update_sums_out[2].buffer_length = record.l_ipns;
        bind_update_sums_out[2].is_null = 0;
        bind_update_sums_out[2].length = &record.l_ipns;

	// sites ID
        bind_update_sums_out[3].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_out[3].buffer = record.siteid;
        bind_update_sums_out[3].buffer_length = record.l_siteid;
        bind_update_sums_out[3].is_null = 0;
        bind_update_sums_out[3].length = &record.l_siteid;

	// users ID
        bind_update_sums_out[4].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_out[4].buffer = record.usersid;
        bind_update_sums_out[4].buffer_length = record.l_usersid;
        bind_update_sums_out[4].is_null = 0;
        bind_update_sums_out[4].length = &record.l_usersid;

	// summary time
        bind_update_sums_out[5].buffer_type = MYSQL_TYPE_STRING;
        bind_update_sums_out[5].buffer = record.sumtime;
        bind_update_sums_out[5].buffer_length = record.l_sumtime;
        bind_update_sums_out[5].is_null = 0;
        bind_update_sums_out[5].length = &record.l_sumtime;

        if (mysql_stmt_bind_param(update_sums_out, bind_update_sums_out) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(update_sums_out));


// Statement Type:      INSERT
// Statement Name:	xSTMT_INSSUMS_IN	"INSERT INTO trafficSummaries(date,ip,inCache,sitesID,usersID,summaryTime) VALUES (?,?,?,?,?,?)"
// Table:               trafficSummaries
// Function:            Add a record to table when UPDATE fails a positive affected row count.
//
// Status:		ADAPTED and WORKING

        MySAR_prepare_stmt(insert_sums_in,xSTMT_INSSUMS_IN, sizeof(xSTMT_INSSUMS_IN));


        memset(bind_insert_sums_in, 0, sizeof(bind_insert_sums_in));

	// date
        bind_insert_sums_in[0].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_in[0].buffer = record.date;
        bind_insert_sums_in[0].buffer_length = record.l_date;
        bind_insert_sums_in[0].is_null = 0;
        bind_insert_sums_in[0].length = &record.l_date;

	// IP in net short format
        bind_insert_sums_in[1].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_in[1].buffer = record.ipns;
        bind_insert_sums_in[1].buffer_length = record.l_ipns;
        bind_insert_sums_in[1].is_null = 0;
        bind_insert_sums_in[1].length = &record.l_ipns;

	// bytes to sum inCache
        bind_insert_sums_in[2].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_in[2].buffer = record.bytes;
        bind_insert_sums_in[2].buffer_length = record.l_bytes;
        bind_insert_sums_in[2].is_null = 0;
        bind_insert_sums_in[2].length = &record.l_bytes;

	// Sites ID
        bind_insert_sums_in[3].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_in[3].buffer = record.siteid;
        bind_insert_sums_in[3].buffer_length = record.l_siteid;
        bind_insert_sums_in[3].is_null = 0;
        bind_insert_sums_in[3].length = &record.l_siteid;

	// Users ID
        bind_insert_sums_in[4].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_in[4].buffer = record.usersid;
        bind_insert_sums_in[4].buffer_length = record.l_usersid;
        bind_insert_sums_in[4].is_null = 0;
        bind_insert_sums_in[4].length = &record.l_usersid;

	// Summary Time
        bind_insert_sums_in[5].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_in[5].buffer = record.sumtime;
        bind_insert_sums_in[5].buffer_length = record.l_sumtime;
        bind_insert_sums_in[5].is_null = 0;
        bind_insert_sums_in[5].length = &record.l_sumtime;

        if (mysql_stmt_bind_param(insert_sums_in, bind_insert_sums_in) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(insert_sums_in));


// Statement Type:      INSERT
// Statement Name:	xSTMT_INSSUMS_OUT	"INSERT INTO trafficSummaries(date,ip,outCache,sitesID,usersID,summaryTime) VALUES (?,?,?,?,?,?)"
// Table:               trafficSummaries
// Function:            Add a record to table when UPDATE fails a positive affected row count.
//
// Status:		ADAPTED and WORKING

        MySAR_prepare_stmt(insert_sums_out,xSTMT_INSSUMS_OUT, sizeof(xSTMT_INSSUMS_OUT));


        memset(bind_insert_sums_out, 0, sizeof(bind_insert_sums_out));

	// date
        bind_insert_sums_out[0].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_out[0].buffer = record.date;
        bind_insert_sums_out[0].buffer_length = record.l_date;
        bind_insert_sums_out[0].is_null = 0;
        bind_insert_sums_out[0].length = &record.l_date;

	// IP in net short format
        bind_insert_sums_out[1].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_out[1].buffer = record.ipns;
        bind_insert_sums_out[1].buffer_length = record.l_ipns;
        bind_insert_sums_out[1].is_null = 0;
        bind_insert_sums_out[1].length = &record.l_ipns;

	// bytes to sum outCache
        bind_insert_sums_out[2].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_out[2].buffer = record.bytes;
        bind_insert_sums_out[2].buffer_length = record.l_bytes;
        bind_insert_sums_out[2].is_null = 0;
        bind_insert_sums_out[2].length = &record.l_bytes;

	// Sites ID
        bind_insert_sums_out[3].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_out[3].buffer = record.siteid;
        bind_insert_sums_out[3].buffer_length = record.l_siteid;
        bind_insert_sums_out[3].is_null = 0;
        bind_insert_sums_out[3].length = &record.l_siteid;

	// Users ID
        bind_insert_sums_out[4].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_out[4].buffer = record.usersid;
        bind_insert_sums_out[4].buffer_length = record.l_usersid;
        bind_insert_sums_out[4].is_null = 0;
        bind_insert_sums_out[4].length = &record.l_usersid;

	// Summary Time
        bind_insert_sums_out[5].buffer_type = MYSQL_TYPE_STRING;
        bind_insert_sums_out[5].buffer = record.sumtime;
        bind_insert_sums_out[5].buffer_length = record.l_sumtime;
        bind_insert_sums_out[5].is_null = 0;
        bind_insert_sums_out[5].length = &record.l_sumtime;

        if (mysql_stmt_bind_param(insert_sums_out, bind_insert_sums_out) != 0)
                MySAR_print(MSG_ERROR, "mysql_stmt_bind_param Failed!() %s", mysql_stmt_error(insert_sums_out));


	// select statements return values
        memset(bind_output, 0, sizeof(bind_output));

        bind_output[0].buffer_type = MYSQL_TYPE_STRING;
        bind_output[0].buffer = bind_data;
        bind_output[0].buffer_length = 50; //strlen(&bind_data);
        bind_output[0].is_null = 0;
        bind_output[0].length = &len[0];

	return;
}
