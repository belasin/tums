/*
 Program: mysar, File: unzip.c
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
#include <string.h>
#include <zlib.h>
#include "mysar.h"

gzFile	f_input_file;
char	*c_fields[0x3ff];	// holds the pointers to the strings at block_buffer
int	field_count=0;
int	line_count=0;
char	block_buffer[0xffff];	// the data is kept here
char	output_buffer[LINE_MAX];

/* report a zlib or i/o error */
void Z_err(int ret)
{
	switch (ret) {
		case Z_ERRNO:
			MySAR_print(MSG_ERROR, "IO error on compressed file!");
			break;
		case Z_STREAM_ERROR:
			MySAR_print(MSG_ERROR, "invalid compression level");
			break;
		case Z_DATA_ERROR:
			MySAR_print(MSG_ERROR, "invalid or incomplete deflate data");
			break;
		case Z_MEM_ERROR:
			MySAR_print(MSG_ERROR, "out of memory");
			break;
		case Z_VERSION_ERROR:
			MySAR_print(MSG_ERROR, "zlib version mismatch!");
	}
}

int MySAR_gzip_uncompress_block()
{
	int len;

	// flush the old records
	memset(&c_fields,0,sizeof(c_fields));
	memset(&block_buffer,0,sizeof(block_buffer));

	// reads are in 64k blocks
	len = gzread(f_input_file, block_buffer, sizeof(block_buffer)-2);
	if (len < 0) Z_err(len);

	// finish the string, so the split wont corrupt it
	block_buffer[strlen(block_buffer)+1]='\0';

	// when splitted, block_buffer is modified!
	// now *c_fields is a array of pointers to block_buffer
	field_count=MySAR_split(block_buffer, c_fields, 1024, "\n");

	// field_count is about 430 ~ 500 records, should never overflow
	if (field_count > (int)sizeof(c_fields)>>0x02)
		MySAR_print(MSG_ERROR, "FATAL: block_buffer overflow in function split()");

	// back off one line
	field_count--;

	if (gzeof(f_input_file))
		return M_EOF;
	else 
		return M_OK;
}

int MySAR_gzip_get_next_line()
{
	static int last_block=0;

	// erase any remaining bytes
	memset(output_buffer,0,sizeof(output_buffer));

	// reached the end of array
	if (line_count==field_count) {
		// get out if there is no more data
		if (last_block)
			return M_EOF;

		// copy the last part
		char xtemp[0x7ff]={0};
		memcpy(xtemp, c_fields[line_count], sizeof(xtemp));

		//its time to get more data from file..
		if (MySAR_gzip_uncompress_block()==M_EOF)
			last_block=1;

		// join the data...
		snprintf(output_buffer,sizeof(output_buffer),"%s%s",xtemp,c_fields[0]);

		// reset line counter
		line_count=0;
	}
	else memcpy(output_buffer, c_fields[line_count], sizeof(output_buffer)); 

	// increment the line counter
	line_count++;

	return M_OK;
}

void MySAR_gzip_close()
{
	if(gzclose(f_input_file) != Z_OK)
		MySAR_print(MSG_ERROR, "Error closing gzipped file!");
}

int MySAR_gzip_open(char *m_file_name)
{
	f_input_file = gzopen(m_file_name, "rb");
	if (f_input_file == NULL) 
		MySAR_print(MSG_ERROR, "Can't open file: %s", m_file_name);

	return M_OK;
}
