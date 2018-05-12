/*
 Program: mysar, File: mysar.c
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
#include <string.h>
#include <time.h>
#include <limits.h>
#include <mysql/mysql.h>
#include <arpa/inet.h>
#include <signal.h>
#include <ctype.h>

#include "mysar.h"

extern char 		output_buffer[LINE_MAX];
extern data_store	record;

FILE *input;


// http://wiki.squid-cache.org/SquidFaq/SquidLogs#head-2914f3a846d41673d4ae34018142e672b8f258ce
//
char *inCacheCodes[] = { "TCP_HIT", "TCP_REFRESH_HIT", "TCP_DENIED", "TCP_REF_FAIL_HIT",
			 "TCP_NEGATIVE_HIT", "TCP_MEM_HIT", "TCP_OFFLINE_HIT" };

void MySAR_signal_handler(int signal)
{
	psignal(signal, "FATAL: MySAR Received Signal: ");

	if (signal==SIGINT || signal==SIGTERM)
	{
		// rollback last operation
		MySAR_db_rollback();
		MySAR_free_mysql_statements();

		if (!config->logfile.compressed)
		{
			// write last file position, prevent duplicationg records
			MySAR_update_config(record.stamp, "lastTimestamp");
			MySAR_update_config_long(ftell(input), "lastLogOffset");
		}

		// close db
		MySAR_db_shutdown();

		// dont forget to remove the lock...
		MySAR_unlock_host();

		exit(EXIT_FAILURE);
	}
}

int main(int argc, char *argv[])
{
	char runtime[15];
	char *mws[MAX_TOKENS];
	
	char *xurl[3];
	char *domain[16];
	int domx;

	signed int lerror=0, inc=0, minor=0, major=0;
	unsigned int cacheCodesCount=0;

	long int start_time;
	long int finish_time;
	time_t time_tm_cycle;
	time_t time_tm_finish;
	struct tm time_result;

	// Setup the program defaults
	MySAR_config_defaults(); 

	// parse command line arguments
	MySAR_parse_args(argc, argv);


	// a small banner 8^)
	MySAR_print(MSG_NOTICE, "MySAR %s Log importer", VERSION);
	MySAR_print(MSG_NOTICE, "Copyright 2007 Cassiano Martin\n");


	// read configuration from file
	MySAR_parse_config_file(config->filename);

	// create the lock file
	MySAR_lock_host();

	// these routines does not return
	if (config->db_generate)
		MySAR_db_create();
	else if (config->show_help)
		MySAR_print_help();

	// starts connection with database
	MySAR_db_startup();

	// Last values to be read are from the database.
	MySAR_read_db_config();

	// Wrong version... get out, or we could do nasty things...
	if (config->schemaVersion != CURRENT_SCHEMA_VERSION) {
		MySAR_print(MSG_NOTICE, "ERROR: Your current MySAR version is not supported!");
		MySAR_print(MSG_NOTICE, "Please, make sure you are running the last version of the report Viewer. (%s)\n", VERSION);
		MySAR_print(MSG_ERROR, "Current detected Schema: %d. Supported Schema: %d", config->schemaVersion, CURRENT_SCHEMA_VERSION);
	}

	// Optimize tables if enabled
	// the routine quits the program on the end.
	if (config->optimize_tables)
		MySAR_db_optimize();

	if (config->offline_mode)
		MySAR_print(MSG_NOTICE, "\nOffline mode enabled.\n");

	// Get out if disabled, but accept if in offline mode
	if (!config->importenabled && !config->offline_mode)
		MySAR_print(MSG_ERROR, "\nMySar importer is currently disabled. to enable, change settings on the Administration page.\n");

	// warn if not importing to table traffic
	if (!config->importtraffic)
		MySAR_print(MSG_NOTICE, "\nImporting only domains. Traffic details are disabled.\n");

	// warn if DNS resolver is disabled...
	if (!config->resolver)
		MySAR_print(MSG_NOTICE, "\nDNS name resolver is disabled. hosts will show up only IP addresses on report.\n");
	
	// Get current time
	start_time = MySAR_current_time();

	// Do the cleanup routine
	MySAR_db_cleanup();
	
	// gzip compressed log support
	if (!config->logfile.compressed)
	{
		MySAR_print(MSG_NOTICE, "Loading plain text log file...");
		if ((input = fopen(config->logfile.name, "r")) == NULL)
			MySAR_print(MSG_ERROR, "FATAL: Unable to open the log file: %s", config->logfile.name);
	}
	else {
		MySAR_print(MSG_NOTICE, "Loading compressed log file...");
		MySAR_gzip_open(config->logfile.name);
		if(MySAR_gzip_uncompress_block()==M_EOF)
			MySAR_print(MSG_ERROR, "Gzip block too small! at least 64k of data is needed!");
	}

	// this routine will prevent the importer from running thru all logfile searching
	// for the last time stamp. it does some test to see if the file changed, and set
	// the file pointer on the last seen record.
	if (!config->logfile.compressed && !config->offline_mode)
	{
		// error in file? null file?
		if (fgets(output_buffer, LINE_MAX, input) == NULL)
			MySAR_print(MSG_ERROR, "Error: could not get data from file! is it a blank file?");
		if (MySAR_split(output_buffer, mws, MAX_TOKENS, "")!=MAX_TOKENS)
			MySAR_print(MSG_ERROR, "Invalid number of tokens, or error in logfile!");

		// compare with the first seen timestamp
		if (strcmp(mws[0], config->firststamp) == 0)
		{
			MySAR_print(MSG_DEBUG, "Timestamp match.");

			// alright, move file pointer
			if (fseek (input, config->logfile.offset, SEEK_SET) != 0)
				MySAR_print(MSG_ERROR, "FATAL: fseek() failed!");

			MySAR_print(MSG_DEBUG, "Logfile offset is now at: %ld", config->logfile.offset);
		}
		else {
			// new file, update the first timestamp
			MySAR_print(MSG_DEBUG, "Timestamp does not match, this is a new logfile");
			MySAR_update_config(mws[0], "firstLogTimestamp");

			// move file pointer to the start again
			(void)fseek(input, 0L, SEEK_SET);
		}
	}

	// just prepare the statements if everything went ok
	MySAR_prep_mysql();

	// install signals catchers..
	signal(SIGINT, MySAR_signal_handler);
	signal(SIGTERM, MySAR_signal_handler);

	for (;;)
	{
		if (config->logfile.compressed) 
		{
			// get more data
			if (MySAR_gzip_get_next_line()==M_EOF)
				break;
		}
		else if (fgets(output_buffer, LINE_MAX, input) == NULL)
				break;

		// This is our minor line counter, this keeps track of every
		// line we run through, regardless if it's processed or not.
		minor++;

		memset(mws,0,sizeof(mws));
		inc=MySAR_split(output_buffer, mws, MAX_TOKENS, "");
		if (inc!=MAX_TOKENS) 
		{
			MySAR_print(MSG_NOTICE, "Error detected at line %d: Split tokens %s!", minor, (inc>MAX_TOKENS ? "overflow":"underflow"));

			// dump tokens
			int xx;
			for(xx=0;xx<(inc>MAX_TOKENS ? MAX_TOKENS:inc);xx++)
				MySAR_print(MSG_DEBUG, "Token%d: %s", xx, mws[xx]);

			lerror++;
			continue;
		}

		// check last timestamp, memcmp sucked.
		// this prevents from importing duplicated entries
		if ((strcmp(mws[0], config->laststamp) <= 0) && !config->offline_mode)
			continue;

		// discard tokens with cache_object
		if (strstr(mws[6], "cache_object") != NULL) 
			continue;

		// dont waste processing power if the record is zero bytes...
		if (memcmp(mws[4], "0", 1) == 0)
			continue;

		// This is a record we're going to process, thus, increase the counter so that we
		// know to update the timestamp later.
		major++;
		memset(&record, 0, sizeof(record));

		// Do our date/time calculations on the timestamp provided by the record.
		time_tm_cycle = strtol((char *)mws[0], NULL, 0);
		localtime_r(&time_tm_cycle, &time_result);

		// and record them respectively.
		strftime(record.date, 11, "%F", &time_result);
		record.l_date = 10;
		strftime(record.time, 10, "%T", &time_result);
		record.l_time = 10;
		strftime(record.sumtime, 3, "%H", &time_result);
		record.l_sumtime = 3;

		record.l_stamp = strlen(mws[0]);
		record.l_ip = strlen(mws[2]);
		record.l_result = strlen(mws[3]);
		record.l_bytes = strlen(mws[4]);
		record.l_url = strlen(mws[6]);
		record.l_authuser = strlen(mws[7]);

		memcpy(record.stamp, mws[0], record.l_stamp+1);
		memcpy(record.ip, mws[2], record.l_ip+1);
		memcpy(record.result, mws[3], record.l_result+1);
		memcpy(record.s_result, mws[3], MySAR_copy_until(mws[3], '/'));
		memcpy(record.bytes, mws[4], record.l_bytes+1);
		memcpy(record.url, mws[6], record.l_url+1);
		memcpy(record.xurl, mws[6], record.l_url+1);		//used by the split function
		memcpy(record.authuser, mws[7], record.l_authuser+1);
		record.l_s_result = strlen(record.s_result);


		// split the URL, give it an extra token
		// the function will overflow, but we need just two records.
		if (MySAR_split(record.xurl, xurl, 4, "/") >= 4)
		{
			if (config->group_domains && !isdigit(xurl[2][0]))
			{
				domx=MySAR_split(xurl[2], domain, 16, ".");
				domx--;
			
				if (domx<=1)
				{
					//one dot is "domain.com" so leave it.
					snprintf(record.site, sizeof(record.site), "%s//%s/", xurl[0], xurl[2]);
				}
				else {
					// we can have subdomains appended, but the two last parts are iana valid ones
					// as we have country domain division, we need to parse it.
					if (MySAR_isTLD(domain[domx-1])==0)
						snprintf(record.site, sizeof(record.site), "%s//www.%s.%s", xurl[0], domain[domx-1], domain[domx]);
					else
						snprintf(record.site, sizeof(record.site), "%s//www.%s.%s.%s", xurl[0], domain[domx-2], domain[domx-1], domain[domx]);
				}
			}
			else {
				snprintf(record.site, sizeof(record.site), "%s//%s/", xurl[0], xurl[2]);
			}
		}
		else {
			memcpy(record.site, record.url, sizeof(record.site));
		}
		record.l_site = strlen(record.site);

		// convert the quad dotted Ip format to the netshort format
		snprintf(record.ipns, sizeof(record.ipns), "%u", inet_network(record.ip));
		record.l_ipns = strlen(record.ipns);

		// It will always be out cache, until we test.
		record.field=TYPE_OUT_CACHE;

		// TCP_MISS is our most often cache result field, coming in at 500 thousand entries
		// out of 1.2 million records (TCP_IMS_HIT is second). So if we're already TCP_MISS, 
		// is outCache. This saves from running through the cacheCodes loop 50% of the time.
		if (!memcmp(record.s_result, "TCP_MISS", record.l_s_result) == 0) 
		{
			for(cacheCodesCount=0; cacheCodesCount<=sizeof(inCacheCodes)/4-1; cacheCodesCount++) 
			{
				if (memcmp(record.s_result, inCacheCodes[cacheCodesCount], record.l_s_result) == 0)
				{
					record.field=TYPE_IN_CACHE;
					break;
				}
			}
		}

		if ((config->show_status) && (major % 1000 == 0) && (MySAR_current_time() - start_time)>0) {	
			// for every 1000 entered records, give status output.
			MySAR_print(MSG_NOTICE, "Processed: %4d records at %3lu/sec Runtime: %lu seconds",
				major, (major / (MySAR_current_time() - start_time)), (MySAR_current_time() - start_time));
		}

		// must follow the right sequence
		MySAR_import_sites();		// import the sites
		MySAR_import_users();		// import the usernames
		MySAR_import_hostnames();	// import the hostnames

		MySAR_import_traffic();		// import the whole traffic

		MySAR_import_summaries();	// now do the summaries
	}


	if (config->logfile.compressed)
		MySAR_gzip_close();
	else {
		// save file position pointer
		config->logfile.offset=ftell(input);
		fclose(input);
	}

	// free the used memory
	MySAR_free_mysql_statements();

	if (major>0 && !config->offline_mode)
	{
		// store values only if valid records were processed
		MySAR_update_config(record.stamp, "lastTimestamp");
		MySAR_update_config_long(config->logfile.offset, "lastLogOffset");
	}

	finish_time = MySAR_current_time();
	time_tm_finish = finish_time - start_time;

	localtime_r(&time_tm_finish, &time_result);
	strftime(runtime, sizeof(runtime), "%M:%S", &time_result);

	MySAR_print(MSG_NOTICE, "Total runtime: %u seconds. Processed: %d Imported: %d Read errors: %d", (unsigned int)time_tm_finish, minor, major, lerror);
	MySAR_db_shutdown();

	// remove the lock after finish
	MySAR_unlock_host();

	return M_OK;
}

