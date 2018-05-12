/*
 Program: mysar, File: lock.c
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

#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <sys/types.h>
#include <signal.h>
#include <errno.h>

#include "mysar.h"

int MySAR_create_lock(char * file)
{
	char tmp_file[255], str[20];
	int fd;
	pid_t pid;
	
	pid = getpid();
	
	// Create temp file
	sprintf(tmp_file, "%s_%d_tmp\n", file, pid);
	if((fd = open(tmp_file, O_WRONLY|O_CREAT|O_TRUNC, 0644)) < 0)
	{
		MySAR_print(MSG_NOTICE, "Can't create temp lock file %s", file);
		MySAR_print(MSG_ERROR, "No permission to write file!\n");
	}
	
	pid = sprintf(str, "%d\n", pid);
	if(write(fd, str, pid) == pid)
	{
		// Create lock file
		if(link(tmp_file, file) < 0)
		{
			MySAR_print(MSG_ERROR, "Can't link temp lock file %s", tmp_file);
		}
	} 
	else { 
		MySAR_print(MSG_ERROR, "Can't write to %s", tmp_file);
	}
	close(fd);
	
	// Remove temp file
	unlink(tmp_file);
	
	return 1;
}
	
pid_t MySAR_read_lock(char * file)
{
	char str[20];
	int  fd;
	pid_t pid;
	
	// Read PID from existing lock
	if((fd = open(file, O_RDONLY)) < 0)
		return 0;
	
	pid = read(fd,str,sizeof(str));
	close(fd);
	if(pid <= 0)
		return 0;
	
	str[sizeof(str)-1]='\0';
	pid = strtol(str, NULL, 10);
	
	if(!pid || errno == ERANGE)
	{
		// Broken lock file
		if(unlink(file) < 0)
			MySAR_print(MSG_ERROR, "Unable to remove broken lock %s", file);

		return 0;
	}
	
	// Check if process is still alive
	if(kill(pid, 0) < 0 && errno == ESRCH)
	{
		// Process is dead. Remove stale lock.
		if(unlink(file) < 0)
			MySAR_print(MSG_ERROR, "Unable to remove stale lock %s", file);

		return 0;
	}
	return pid;
}

int MySAR_lock_host()
{
	struct timespec tm;
	int i;
	pid_t pid;

	// Check if lock already exists.
	if((pid = MySAR_read_lock(config->pidfile)) > 0)
	{
		if (!config->kill_lock)
		{
			MySAR_print(MSG_ERROR, "Another copy is already running! use --kill switch if you want to kill the old process!");
		} 
		else {
 
			MySAR_print(MSG_NOTICE, "Killing old connection (process %d)", pid);
	
			if(kill(pid, SIGTERM) < 0 && errno != ESRCH)
			{
				MySAR_print(MSG_ERROR, "Can't kill process %d. %s",pid,strerror(errno));
				return 0;
			}
		
			//Give it a time(up to 5 secs) to terminate
			for(i=0; i < 10 && !kill(pid, 0); i++ )
			{
				tm.tv_sec = 0; tm.tv_nsec = 500000000; 
				nanosleep(&tm, NULL);
			}
	
			// Make sure it's dead
			if(!kill(pid, SIGKILL))
			{
				MySAR_print(MSG_NOTICE, "Process %d ignored TERM, killed with KILL", pid);
				// Remove lock
				if(unlink(config->pidfile) < 0)
					MySAR_print(MSG_ERROR, "Unable to remove lock %s", config->pidfile);
			}
		}
	}

	return MySAR_create_lock(config->pidfile);
}

void MySAR_unlock_host()
{ 
	if(unlink(config->pidfile) < 0)
		MySAR_print(MSG_ERROR, "Unable to remove lock %s", config->pidfile);
}
