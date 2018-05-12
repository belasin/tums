/*
 Program: mysar, File: utils.c
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

#include <time.h>
#include <stdio.h>
#include <string.h>
#include "mysar.h"

// Top Level Domains listing
// from: http://data.iana.org/TLD/tlds-alpha-by-domain.txt
const char *gTLD[] = {
"ac","ad","ae","aero","af","ag","ai","al","am","an","ao","aq","ar","arpa","as","asia",
"at","au","aw","ax","az","ba","bb","bd","be","bf","bg","bh","bi","biz","bj","bm",
"bn","bo","br","bs","bt","bv","bw","by","bz","ca","cat","cc","cd","cf","cg","ch",
"ci","ck","cl","cm","cn","co","com","coop","cr","cu","cv","cx","cy","cz","de","dj",
"dk","dm","do","dz","ec","edu","ee","eg","er","es","et","eu","fi","fj","fk","fm",
"fo","fr","ga","gb","gd","ge","gf","gg","gh","gi","gl","gm","gn","gov","gp","gq",
"gr","gs","gt","gu","gw","gy","hk","hm","hn","hr","ht","hu","id","ie","il","im",
"in","info","int","io","iq","ir","is","it","je","jm","jo","jobs","jp","ke","kg","kh",
"ki","km","kn","kr","kw","ky","kz","la","lb","lc","li","lk","lr","ls","lt","lu",
"lv","ly","ma","mc","md","mg","mh","mil","mk","ml","mm","mn","mo","mobi","mp","mq",
"mr","ms","mt","mu","museum","mv","mw","mx","my","mz","na","name","nc","ne","net","nf",
"ng","ni","nl","no","np","nr","nu","nz","om","org","pa","pe","pf","pg","ph","pk",
"pl","pm","pn","pr","pro","ps","pt","pw","py","qa","re","ro","ru","rw","sa","sb",
"sc","sd","se","sg","sh","si","sj","sk","sl","sm","sn","so","sr","st","su","sv",
"sy","sz","tc","td","tel","tf","tg","th","tj","tk","tl","tm","tn","to","tp","tr",
"travel","tt","tv","tw","tz","ua","ug","uk","um","us","uy","uz","va","vc","ve","vg",
"vi","vn","vu","wf","ws","ye","yt","yu","za","zm","zw", NULL
};

int MySAR_isTLD(const char *domain)
{
	register int i=0;

	// is a valid domain?
	while(strcmp(domain, gTLD[i])!=0)
	{
		if (gTLD[i+1]==NULL)
			return 0;
		i++;
	};

	return i;
}

int MySAR_check_empty(char *value)
{
	if ((strlen(value)==0)&&(!(*value)))
		return 0;
	else
		return 1;
}

// reads keystrokes from the console
int MySAR_readconsole(char *mline)
{
	char *p = mline;
	
	while((*p=(char)getchar())!='\n')
		if (*p) p++;
	
	*p = '\0';
	
	return 1;
}

// return the current time sinc epoch
int MySAR_current_time()
{
	struct tm ntime;
	time_t set;
	time ( & set);
	
	ntime = *localtime (& set);
	return mktime(& ntime);
}

// split a string in array of pointers
int MySAR_split(char *string, char *c_fields[], int nc_fields, char *sep)
{
	register char *p = string;
	register char c;			/* latest character */
	register char sepc = sep[0];
	register char sepc2;
	register int fn;
	register char **fp = c_fields;
	register char *sepp;
	register int trimtrail;

	/* white space */
	if (sepc == '\0') {
		while ((c = *p++) == ' ' || c == '\t')
			continue;
		p--;
		trimtrail = 1;
		sep = " \t";	/* note, code below knows this is 2 long */
		sepc = ' ';
	} else
		trimtrail = 0;
		sepc2 = sep[1];		/* now we can safely pick this up */

		/* catch empties */
		if (*p == '\0')
			return(0);

		/* single separator */
		if (sepc2 == '\0') {
			fn = nc_fields;
			for (;;) {
				*fp++ = p;
				fn--;
				if (fn == 0)
					break;
				while ((c = *p++) != sepc)
					if (c == '\0')
						return(nc_fields - fn);
				*(p-1) = '\0';
			}
			/* we have overflowed the c_fields vector -- just count them */
			fn = nc_fields;
			for (;;) {
				while ((c = *p++) != sepc)
					if (c == '\0')
						return(fn);
				fn++;
			}
			/* not reached */
		}

		/* two separators */
		if (sep[2] == '\0') {
			fn = nc_fields;
			for (;;) {
				*fp++ = p;
				fn--;
				while ((c = *p++) != sepc && c != sepc2)
					if (c == '\0') {
					if (trimtrail && **(fp-1) == '\0')
						fn++;
					return(nc_fields - fn);
					}
					if (fn == 0)
						break;
					*(p-1) = '\0';
					while ((c = *p++) == sepc || c == sepc2)
						continue;
					p--;
			}
			/* we have overflowed the c_fields vector -- just count them */
			fn = nc_fields;
			while (c != '\0') {
				while ((c = *p++) == sepc || c == sepc2)
					continue;
				p--;
				fn++;
				while ((c = *p++) != '\0' && c != sepc && c != sepc2)
					continue;
			}
			/* might have to trim trailing white space */
			if (trimtrail) {
				p--;
				while ((c = *--p) == sepc || c == sepc2)
					continue;
				p++;
				if (*p != '\0') {
					if (fn == nc_fields+1)
						*p = '\0';
					fn--;
				}
			}
			return(fn);
		}

		/* n separators */
		fn = 0;
		for (;;) {
			if (fn < nc_fields)
				*fp++ = p;
			fn++;
			for (;;) {
				c = *p++;
				if (c == '\0')
					return(fn);
				sepp = sep;
				while ((sepc = *sepp++) != '\0' && sepc != c)
					continue;
				if (sepc != '\0')	/* it was a separator */
					break;
			}
			if (fn < nc_fields)
				*(p-1) = '\0';
			for (;;) {
				c = *p++;
				sepp = sep;
				while ((sepc = *sepp++) != '\0' && sepc != c)
					continue;
				if (sepc == '\0')	/* it wasn't a separator */
					break;
			}
			p--;
		}

		/* not reached */
}

// return string until delimiter
char *MySAR_copy_delimited(char *from, char *delimiter)
{
        char *target = strstr(from, delimiter);

        if (target==NULL)
                return 0;

	return (char *)(target);

        //ptr = (int)(target-from);
}


// return how many bytes to copy until delimiter
int MySAR_copy_until(char *from, int delimiter)
{
        char *target = strchr(from, delimiter);

        if (target==NULL)
                return 0;

        return (int)(target-from);
}
