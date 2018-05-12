#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2007 marco.s - http://www.advproxy.net/update-accelerator
#
# $Id: convert,v 1.0 2007/09/12 00:00:00 marco.s Exp $
#

use strict;

my $updcache='/home/httpd/html/updatecache';
my @metadata=();
my $filename='';
my $uuid='';
my $vendorid='';
my @cachedirs=qw(download);
my $i=0;
my $n=0;
my $verbose=1;
my $logging=1;
my $logfile="/var/log/updatexlrator/convert.log";

if (@ARGV[0] eq '-nv') { $verbose = 0; }
if (!-d "/var/log/updatexlrator") { $logging = 0; }

&writelog("Converting cached objects from Update Accelerator 1.0 to 2.x");
&writelog("------------------------------------------------------------");

(-d "$updcache/metadata") || die "No version 1.0 cache found.\n";

if (`ps --no-heading -C wget`)
{
	&writelog("WARNING: Download in progress");
	print "\n";
	system("killall -9 -i wget");
	print "\n";
}

foreach (<$updcache/metadata/*>)
{
	$filename = substr($_,rindex($_,'/')+1,length($_));
	if ((-f "$updcache/$filename") && (-f "$updcache/metadata/$filename"))
	{  
		&writelog("$filename");
		open (FILE,$_);
		@metadata = <FILE>;
		close FILE;
		chomp(@metadata);
		if (@metadata >= 5)
		{
			$uuid = `echo $metadata[0] | md5sum`;
			$uuid =~ s/[^0-9a-f]//g;
			$uuid =~ s/([a-f\d]{8})([a-f\d]{4})([a-f\d]{4})([a-f\d]{4})([a-f\d]{12})/$1-$2-$3-$4-$5/;
			$vendorid = $metadata[1];
			$vendorid =~ tr/A-Z/a-z/;
			unless (-d "$updcache/$vendorid")
			{
				system("mkdir $updcache/$vendorid");
				push(@cachedirs,$vendorid);
			}
			system("chmod 775 $updcache/$vendorid");
			unless (-d "$updcache/$vendorid/$uuid") { system("mkdir $updcache/$vendorid/$uuid"); }
			system("chmod 775 $updcache/$vendorid/$uuid");
			open (FILE,">$updcache/$vendorid/$uuid/source.url");
			print FILE "$metadata[0]\n";
			close FILE;
			open (FILE,">$updcache/$vendorid/$uuid/status");
			print FILE "$metadata[2]\n";
			close FILE;
			open (FILE,">$updcache/$vendorid/$uuid/checkup.log");
			print FILE "$metadata[3]\n";
			close FILE;
			open (FILE,">$updcache/$vendorid/$uuid/access.log");
			for($i=4;$i<@metadata;$i++)
			{
				print FILE "$metadata[$i]\n";
			}
			close FILE;
			system("mv $updcache/$filename $updcache/$vendorid/$uuid");
			system("chmod 664 $updcache/$vendorid/$uuid/*");
			$n++;
		} else { &writelog("WARNING: Insufficient metadata for $filename"); }
	}
}

if (($n) && (-d "$updcache/metadata")) { system("rm -r $updcache/metadata"); }

foreach (@cachedirs) { system("chown -R nobody:squid $updcache/$_"); }

if ($n) { &writelog("------------------------------------------------------------"); }

$verbose=1;
&writelog("$n objects converted.");

# -------------------------------------------------------------------

sub writelog
{
        if ($verbose) { print "$_[0]\n"; }
        if ($logging)
        {
                open (LOGFILE,">>$logfile");
                my @now = localtime(time);
                printf LOGFILE "%04d-%02d-%02d %02d:%02d:%02d %s\n",$now[5]+1900,$now[4]+1,$now[3],$now[2],$now[1],$now[0],$_[0];
                close LOGFILE;
        }
}

# -------------------------------------------------------------------
