/*
 Program: mysar, File: globals.h
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
 along with Foobar; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/

#include <limits.h>
#include <config.h>

// arguments are optional
#define MySAR_print(level, fmt, ...)	MySAR_macro_print_msg(__FILE__,__LINE__,level, fmt, ##__VA_ARGS__);

// used for bitwise OR
#define MSG_NOTICE	0x01
#define MSG_ERROR	0x02
#define MSG_DEBUG	0x04

#define MSG_NO_CRLF	0x08

// Which MySAR version the importer works
#define CURRENT_SCHEMA_VERSION 3
#define MAX_TOKENS 10

#define M_OK 1
#define M_ERR 0
#define M_EOF 999

// squid cache results
#define TYPE_IN_CACHE 1
#define TYPE_OUT_CACHE 2

typedef struct c_config
{
	// from plain text config file	
	char dbuser[25];
	char dbpass[25];
	char dbname[25];
	char dbserver[127];
	char pidfile[127];

	// main configuration filename;
	char filename[255];
	
	// option to import from a compressed logfile
	struct logfile
	{
		char name[255];
		short int compressed;
		long offset;
	} logfile;

	// integer compares are faster
	short int offline_mode;
	short int optimize_tables;
	short int importtraffic;
	short int resolver;
	short int importenabled;
	short int schemaVersion;
	short int debug_enabled;
	short int db_generate;
	short int db_conn_open;
	short int show_help;
	short int show_status;
	short int group_domains;
	short int quiet_mode;
	short int kill_lock;

	long optimize_count;

	// pointers from DB config
	char *lastcleanup;
	char *laststamp;
	char *firststamp;
	char *historydays;

}c_config;


typedef struct
{
	char stamp[40];
	char date[11];
	char time[9];
	char sumtime[3];
	char ip[16];
	char result[64];
	char s_result[60];
	char bytes[10];
	char url[LINE_MAX];
	char xurl[LINE_MAX];
	int field;
	char type[128];
	char id[24];
	char siteid[24];
	char ipns[24];
	char site[LINE_MAX];
	char hostname[128];
	
	char usersid[24];
	char authuser[24];
	
	char isResolved[24];
	
	unsigned long l_stamp, l_ip, l_result,
	l_s_result, l_bytes, l_url, l_type, 
	l_date, l_time, l_sumtime, l_ipns, 
	l_hostname, l_site, l_siteid, l_id, 
	l_usersid, l_isResolved, l_authuser;

} data_store;


// functions from sql.c
int MySAR_update_timestamp(char *);
int MySAR_update_config(char *, char *);
int MySAR_push_query(char *);
int MySAR_push_query_free(char *query);
char *MySAR_fetch_configvalue(char *);
char *MySAR_select_field();
void MySAR_prep_mysql();
void MySAR_free_mysql_statements();
inline void MySAR_import_traffic();
inline void MySAR_import_hostnames();
inline void MySAR_import_sites();
inline void MySAR_import_users();
inline void MySAR_import_summaries();
long MySAR_fetch_config_long(char *name);
int MySAR_update_config_long(long value, char *name);

// functions from debug.c
void MySAR_macro_print_msg(char *file, int line, unsigned char level, const char *fmt, ...);
void MySAR_print_help();


// functions from database.c
void MySAR_db_create();
void MySAR_db_startup();
void MySAR_db_cleanup();
void MySAR_db_shutdown();
void MySAR_db_optimize();
void MySAR_db_rollback();


// functions from unzip.c
int MySAR_gzip_open(char *m_file_name);
int MySAR_gzip_get_next_line();
int MySAR_gzip_uncompress_block();
void MySAR_gzip_close();


// functions from utils.c
int MySAR_isTLD(const char *domain);
int MySAR_split(char *string, char *c_fields[], int nc_fields, char *sep);
int MySAR_readconsole(char *mline);
int MySAR_copy_until(char *from, int delimiter);
char *MySAR_copy_delimited(char *from, char *delimiter);
int MySAR_current_time();
int MySAR_check_empty(char *value);


// functions from config.c
int MySAR_parse_config_file (char *myname);
void MySAR_read_db_config();
int MySAR_parse_args(int argc, char **argv);
void MySAR_config_defaults();
int MySAR_config_isblank(char *param, char *value);


// functions from lock.c
int MySAR_lock_host();
void MySAR_unlock_host();

// Global variables.
extern c_config		*config;
