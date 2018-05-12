/*
 Program: mysar, File: debug.c
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
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <syslog.h>

#include "mysar.h"

void MySAR_syslog(char *mlog)
{
	openlog ("mysar", LOG_CONS | LOG_PID | LOG_NDELAY, LOG_LOCAL1);

	syslog (LOG_ERR, "%s", mlog);

	closelog ();
}

void MySAR_macro_print_msg(char *file, int line, unsigned char level, const char *fmt, ...)
{
	char *result;
	va_list ap;
        time_t now;
	struct tm time_result;
        char today[15];
        char time[15];

	// get current time and date
        now = MySAR_current_time();

	localtime_r(&now, &time_result);

        strftime(today, sizeof(today), "%Y-%m-%d", &time_result);
        strftime(time, sizeof(time), "%H:%M:%S", &time_result);

	// print variables on string
	va_start (ap, fmt);
	vasprintf (&result,fmt,ap);
	va_end (ap);

	if (config->quiet_mode)
	{
	 	if (level & MSG_ERROR)
		{
			MySAR_syslog(result);
			free(result);

			if (config->db_conn_open) 
				MySAR_db_shutdown();
			exit(EXIT_FAILURE);
		}

		return;
	}

	// bitwise comparsion
	if (level & MSG_NOTICE)
	{
		if (level & MSG_NO_CRLF)
			printf("%s", result);
		else	printf("%s\n", result);

		free(result);
		return;
	} 
	else if (level & MSG_ERROR) {
		if (config->debug_enabled)
		{
			if (level & MSG_NO_CRLF)
				printf("%s %s %s:%-3d -->> %s", today, time, file, line, result);
			else	printf("%s %s %s:%-3d -->> %s\n", today, time, file, line, result);
		}
		else {
		
			if (level & MSG_NO_CRLF)
				printf("%s", result);
			else	printf("%s\n", result);
		}

		printf("Execution Aborted!\n");

		free(result);
	
		// close mysql connection
		if (config->db_conn_open) 
			MySAR_db_shutdown();

		exit(EXIT_FAILURE);
	} 
	else if (level & MSG_DEBUG && config->debug_enabled) {
		if (level & MSG_NO_CRLF)
			printf("DEBUG--->>: %s", result);
		else	printf("DEBUG--->>: %s\n", result);

		free(result);
		return;
	}
}

void MySAR_print_help(void)
{
        char *help_msg = {
		"MySQL Squid Access Report (importer).\n"
		"Adapted from code taken from the MySAR log importer.\n"
		"Copyright 2007 Cassiano Martin\n"
		"\n"
		"Available Options:\n\n"
		"--resolver                     this enables the DNS resolver\n"
		"--noresolver                   this disables the DNS resolver (*default)\n"
		"--traffic                      enable full traffic import from logfile (*default)\n"
		"--notraffic                    disable full traffic import. navigation details wont be imported.\n"
		"--zip          <file>          load a gzipped logfile for importing. the import is done in \"offline\" mode.\n"
		"--logfile      <file>          load a plain text logfile. the import is also done in \"offline\" mode.\n"
		"--debug                        enable some debug functionality. useful to find obscure problems.\n"
		"--config       <file>          load an alternative configuration file, instead of /etc/mysar.conf\n"
		"--help                         show the help, with command line options.\n"
		"--generatedb                   shows the database creator. create or replace MySAR databases.\n"
		"--stats                        show records status when importing.\n"
		"--optimizedb                   force database optimizator to run\n"
		"--groupdomains                 group domains on the site viewer. More accurate traffic sizes too. (slow)\n"
		"--offline                      use to import data from older logfiles. implies --logfile or --zip\n"
		"--quiet                        does not show any message. all error messages are logged within syslog."
		"--kill                         send a kill signal to a running importer. the running importer will shutdown"
		};

        MySAR_print(MSG_NOTICE, "%s", help_msg);

        exit(EXIT_SUCCESS);
}

