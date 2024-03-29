#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2006,2007 marco.s - http://www.advproxy.net/update-accelerator
#
# $Id: lscache,v 1.0 2007/09/11 00:00:00 marco.s Exp $
#

use strict;
use Getopt::Std;

my $swroot='/etc/squid3';
my $apphome="/usr/local/tcs/tums";
my $repository='/var/lib/samba/updates';
my $updatefile='';
my $sourceurl='';
my $filesize=0;
my $totalfilesize=0;
my $cachedtraffic=0;
my @updatelist=();
my @sources=();
my @requests=();
my @filelist=();
my $objectdir='';
my @tmp;
my $counts=0;
my $filedate;
my $lastaccess;
my $vendorid;
my @vendors=();
my $numfiles=0;
my $cachehits=0;
my $efficiency='0.0';
my %vendorstats=();
my $maxlength_filesize=0;
my $maxlength_request=0;
my $maxlength_vendorid=0;


getopts('adfs');

foreach (<$repository/*>)
{
	if (-d $_)
	{
		unless ((/^$repository\/download$/) || (/^$repository\/lost\+found$/)) { push(@sources,$_); }
	}
}

foreach (@sources)
{
	$vendorid=substr($_,rindex($_,'/')+1,length($_));
	push(@vendors,$vendorid);
	@updatelist=<$_/*>;
	foreach $objectdir (@updatelist)
	{
		if (-e "$objectdir/source.url")
		{
			open (FILE,"$objectdir/source.url");
			$sourceurl=<FILE>;
			close FILE;
			chomp($sourceurl);
			$updatefile = substr($sourceurl,rindex($sourceurl,'/')+1,length($sourceurl));
		#
		# Get filesize and calculate max length for output
		#
			$filesize = (-s "$objectdir/$updatefile");
			if (length($filesize) > $maxlength_filesize) { $maxlength_filesize = length($filesize); }
		#
		# Total file size
		#
			$totalfilesize += $filesize;
		#
		# File size for this source
		#
			$vendorstats{$vendorid . "_filesize"} += $filesize;
		#
		# Number of requests from cache for this source
		#
			open (FILE,"$objectdir/access.log");
			@requests=<FILE>;
			close FILE;
			chomp(@requests);
			$counts = @requests;
			$counts--;
			$vendorstats{$vendorid . "_requests"} += $counts;
			$cachehits += $counts;
		#
		# Calculate cache hits max length for output
		#
			if (length($cachehits) > $maxlength_request) { $maxlength_request = length($cachehits); }
		#
		# Get last cache access date
		#
			my ($SECdt,$MINdt,$HOURdt,$DAYdt,$MONTHdt,$YEARdt) = localtime($requests[-1]);
			$DAYdt   = sprintf ("%.02d",$DAYdt);
			$MONTHdt = sprintf ("%.02d",$MONTHdt+1);
			$YEARdt  = sprintf ("%.04d",$YEARdt+1900);
			if (($counts) && ($requests[-1] =~ /^\d+/) && ($requests[-1] >= 1))
			{
				$lastaccess = $YEARdt."-".$MONTHdt."-".$DAYdt;
			} else {
				$lastaccess = 'Unknown   ';
			}
		#
		# Get file modification time
		#
			($SECdt,$MINdt,$HOURdt,$DAYdt,$MONTHdt,$YEARdt) = localtime(&getmtime("$objectdir/$updatefile"));
			$DAYdt   = sprintf ("%.02d",$DAYdt);
			$MONTHdt = sprintf ("%.02d",$MONTHdt+1);
			$YEARdt  = sprintf ("%.04d",$YEARdt+1900);
			$filedate = $YEARdt."-".$MONTHdt."-".$DAYdt;
		#
		# Total number of files in cache
		#
			$numfiles++;
		#
		# Number of files for this source
		#
			$vendorstats{$vendorid . "_files"}++;
		#
		# Count cache status occurences
		#
			open (FILE,"$objectdir/status");
			$_=<FILE>;
			close FILE;
			chomp;
			$vendorstats{$vendorid . "_" . $_}++;
		#
		# Calculate cached traffic for this source
		#
			$vendorstats{$vendorid . "_cachehits"} += $counts * $filesize;
		#
		# Calculate total cached traffic
		#
			$cachedtraffic += $counts * $filesize;
		#
		# Calculate vendor ID max length for output
		#
			if (length($vendorid) > $maxlength_vendorid) { $maxlength_vendorid = length($vendorid); }
		#
		# Add record to filelist
		#
			push (@filelist,"$filesize;$filedate;$counts;$lastaccess;$vendorid;$objectdir;$updatefile");
		}
	}
}

@filelist || die "No matching files found in cache\n";

#
# Process statistics for output
#

if ($Getopt::Std::opt_s)
{
	foreach (@vendors)
	{
		print "$_\n";
		printf "%5d %s", $vendorstats{$_ . "_files"}, "files in cache\n";
		printf "%5d %s", $vendorstats{$_ . "_requests"}, "files from cache\n";
		printf "%5d %s", $vendorstats{$_ . "_1"}, "files 'Ok'\n";
		printf "%5d %s", $vendorstats{$_ . "_3"}, "files 'No source'\n";
		printf "%5d %s", $vendorstats{$_ . "_2"}, "files 'Outdated'\n";
		printf "%5d %s", $vendorstats{$_ . "_0"}, "files 'Unknown'\n";
		unless ($vendorstats{$_ . "_filesize"}) { $vendorstats{$_ . "_filesize"} = '0'; }
		1 while $vendorstats{$_ . "_filesize"} =~ s/^(-?\d+)(\d{3})/$1.$2/;
		printf "%15s %s", $vendorstats{$_ . "_filesize"}, "bytes in cache\n";
		unless ($vendorstats{$_ . "_cachehits"}) { $vendorstats{$_ . "_cachehits"} = '0'; }
		1 while $vendorstats{$_ . "_cachehits"} =~ s/^(-?\d+)(\d{3})/$1.$2/;
		printf "%15s %s", $vendorstats{$_ . "_cachehits"}, "bytes from cache\n\n";
	}

	if ($numfiles) { $efficiency = sprintf("%.1f", $cachehits / $numfiles); }
	1 while $totalfilesize =~ s/^(-?\d+)(\d{3})/$1.$2/;
	1 while $cachedtraffic =~ s/^(-?\d+)(\d{3})/$1.$2/;
	print "\nTotal files in cache:   $numfiles\n";
	print "Total cache size:       $totalfilesize bytes\n";
	print "Delivered from cache:   $cachedtraffic bytes\n";
	print "Cache efficiency index: $efficiency\n";

	exit;
}

#
# Process filelist for output
#

foreach (@filelist)
{
	@tmp = split(';');
	printf "%$maxlength_filesize\d %s ",$tmp[0],$tmp[1];
	if ($Getopt::Std::opt_a) { printf "%$maxlength_request\d %s ",$tmp[2],$tmp[3]; }
	if ($Getopt::Std::opt_d) { printf "%-$maxlength_vendorid\s ",$tmp[4]; }
	if ($Getopt::Std::opt_f) { print "$tmp[5]/"; }
	print "$tmp[6]\n";
}


# -------------------------------------------------------------------

sub getmtime
{
        my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($_[0]);

        return $mtime;
}

# -------------------------------------------------------------------

sub VERSION_MESSAGE
{
	$Getopt::Std::STANDARD_HELP_VERSION=1;
	print <<EOM
lscache (Update Accelerator coreutils) 1.00
Copyright (c) 2006,2007 marco.s - http://www.advproxy.net/update-accelerator
EOM
;
}

# -------------------------------------------------------------------

sub HELP_MESSAGE
{
	print <<EOM

Usage: lscache [-adf | -s]

Shows details about the Update Accelerator cache content

File listing:
  -a         list number of cache hits and last access date
  -d         list download source
  -f         list full cache path

Statistics:
  -s         show statistics by source

  --help     display this help
  --version  output version information
EOM
;
}

# -------------------------------------------------------------------
