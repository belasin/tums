/*
 Program: mysar, File: config.c
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

#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <string.h>
#include "mysar.h"

#define IFIS(x,str,param) if(!memcmp(x,str,sizeof(str)-1) && MySAR_config_isblank(x,param))

c_config	*config;

static int m_op_resolver;
static int m_op_traffic;
static int m_op_logfile;
static int m_op_optimize;
static int m_op_groupdomains;


void MySAR_config_defaults()
{
	// initialize the configuration structure
	config=(c_config *)malloc(sizeof(c_config));
	memset(config,0,sizeof(c_config));

	// set the default configuration file
	//strncpy(config->filename, "/etc/mysar.conf", sizeof(config->filename));
	snprintf(config->filename, sizeof(config->filename), "%s/mysar.conf", SYSCONFDIR);

	// set some default values for proper working
	// they are overwritten when config file is read
	config->offline_mode=0;
	config->optimize_tables=0;
	config->importtraffic=1;
	config->logfile.compressed=0;
	config->resolver=0;
	config->importenabled=1;
	config->debug_enabled=0;
	config->show_help=0;
	config->show_status=0;
	config->db_generate=0;
	config->schemaVersion=0;
	config->quiet_mode=0;
	config->db_conn_open=0;
	config->group_domains=0;

	// configuration values should not overwrite command line values
	m_op_resolver=99;
	m_op_traffic=99;
	m_op_logfile=99;

}

int MySAR_parse_args(int argc, char **argv)
{
	int res;
	static struct option long_options[] = {
		{"config", required_argument, 0, 'f'},
		{"debug", no_argument, 0, 'd'},
		{"generatedb", no_argument, 0, 'g'},
		{"groupdomains", no_argument, &m_op_groupdomains, 1},
		{"help", no_argument, 0, 'h'},
		{"kill", no_argument, 0, 'k'},
		{"logfile", required_argument, 0, 'l'},
		{"resolver", no_argument, &m_op_resolver, 1},
		{"noresolver", no_argument, &m_op_resolver, 0},
		{"offline", no_argument, 0, 'o'},
		{"optimizedb", no_argument, &m_op_optimize, 1},
		{"quiet", no_argument, 0, 'q'},
		{"stats", no_argument, 0, 's'},
		{"traffic", no_argument, &m_op_traffic, 1},
		{"notraffic", no_argument, &m_op_traffic, 0},
		{"zip", required_argument, 0, 'z'},
		{0,0,0,0}
	};

	MySAR_print(MSG_DEBUG, "Parsing command lines values...");

	while ((res=getopt_long(argc, argv, "f:dghkl:oqsz:", long_options, NULL))!=-1)
	{
		switch(res)
		{
			case 0:
				// quit if parameter is a flag.
				break;
			case 'f':
				// load a specific configuration file
				strncpy(config->filename, optarg, sizeof(config->filename));
				break;
			case 'd':
				config->debug_enabled=1;
				break;
			case 'g':
				config->db_generate=1;
				break;
			case 'h':
				config->show_help=1;
				break;
			case 'k':
				config->kill_lock=1;
				break;
			case 'l':
				m_op_logfile=1;
				config->logfile.compressed=0;
				strncpy(config->logfile.name, optarg, sizeof(config->logfile.name));
				break;
			case 'o':
				config->offline_mode=1;
				break;
			case 'q':
				config->quiet_mode=1;
				break;
			case 's':
				config->show_status=1;
				break;
			case 'z':
				m_op_logfile=1;
				config->logfile.compressed=1;
				strncpy(config->logfile.name, optarg, sizeof(config->logfile.name));
				break;
			default:
				MySAR_print(MSG_ERROR | MSG_NO_CRLF, "Error processing command line: ");
		}
	}

	// dont allow offline mode without specifying a logfile
	if (config->offline_mode && m_op_logfile==99)
		MySAR_print(MSG_ERROR, "Error: you need to supply a log file to import in offline mode!");

	if (m_op_resolver!=99)
		config->resolver=m_op_resolver;
	if (m_op_traffic!=99)
		config->importtraffic=m_op_traffic;

	if (m_op_optimize)
		config->optimize_tables=m_op_optimize;
	if (m_op_groupdomains)
		config->group_domains=m_op_groupdomains;

	return 0;
}


int MySAR_config_isblank(char *param, char *value)
{
	if ((strlen(value)==0)&&(!(*value)))
		MySAR_print(MSG_ERROR, "ERROR: Bad value in configuration file! %s%s  (cannot be blank)\n", param, value);

	return 1;
}

int MySAR_parse_config_file (char *myname)
{
	char line[512];
	char *p;
	char *param;
	int i;
	FILE *f;

	MySAR_print(MSG_DEBUG, "Parsing configuration file: %s", config->filename);

	// open da file
	f=fopen (myname, "r");

	if (f!=NULL)
	{

		while(!feof(f))
		{
			*line=0;
			fgets(line,512,f);
	
			i=strlen(line);
			if(line[i-1]=='\n') line[i-1]=0;

			p=line;
			while(*p)
			{
				// remove comentarios do conf
				if(p[0]=='#')
				{
					p[0]=0;
					break;
				}
				p++;
			}

			p=line;
			while(*p<=' ' && *p) p++;
	
			if(!*p) continue;
	
			param=line;
	
			while(*param && *param!='=') param++;
				if(*param) param++;
	
				// copy using strncpy, prevent overflowing
				IFIS(line, "username", param)
					strncpy(config->dbuser, param, sizeof(config->dbuser));
				else IFIS(line, "password", param)
					strncpy(config->dbpass, param, sizeof(config->dbpass));
				else IFIS(line, "database", param)
					strncpy(config->dbname, param, sizeof(config->dbname));
				else IFIS(line, "server", param)
					strncpy(config->dbserver, param, sizeof(config->dbserver));
				else IFIS(line, "pidfile", param)
					strncpy(config->pidfile, param, sizeof(config->pidfile));
				else IFIS(line, "logfile", param)
				{
					// dont overwrite the command line filename
					if (m_op_logfile==99)
						strncpy(config->logfile.name, param, sizeof(config->logfile.name));
				}
		}
	}
	else
	{
		MySAR_print(MSG_ERROR, "\nFATAL: Could not find configuration file %s!\n", config->filename);
	}

	return 0;
}

void MySAR_read_db_config()
{
	// Retrieve information from config on the database
	// both config file and database config use the same structure
	config->lastcleanup = MySAR_fetch_configvalue("lastCleanUp");
	config->laststamp = MySAR_fetch_configvalue("lastTimestamp");
	config->firststamp = MySAR_fetch_configvalue("firstLogTimestamp");
	config->historydays = MySAR_fetch_configvalue("keepHistoryDays");

	// no command line given? read database...
	if (m_op_resolver==99)	
		config->resolver = (strcmp(MySAR_fetch_configvalue("resolveClients"),"enabled")==0) ? 1 : 0;
 
	config->importenabled = (strcmp(MySAR_fetch_configvalue("mysarImporter"),"enabled")==0) ? 1 : 0;
	config->schemaVersion = atoi(MySAR_fetch_configvalue("schemaVersion"));

	// get last file offset from db
	config->logfile.offset = MySAR_fetch_config_long("lastLogOffset");

	// fetch last optimization counter
	config->optimize_count = MySAR_fetch_config_long("optimizeCounter");

}
