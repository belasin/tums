#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2006,2007 marco.s - http://www.advproxy.net/update-accelerator
#
# $Id: download,v 2.0 2007/07/07 00:00:00 marco.s Exp $
#

use strict;
use HTTP::Date;

my $swroot='/etc/squid3';
my $apphome="/usr/local/tcs/tums";
my $logfile="/var/log/squid/accelerate.download.log";
my $logging=1;
my $repository='/var/lib/samba/updates';
my $login='';
my $dlrate='';
my $uuid='';
my $wget="/usr/bin/wget";
my $useragent="Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)";
my %xlratorsettings=();
my %proxysettings=();
my @http_header=();
my $remote_mtime=0;
my $updatefile='';
my $unique=0;
my $mirror=1;

my $sfOk="1";

my $vendorid  = @ARGV[0]; if ($vendorid  eq '') { exit; }
my $sourceurl = @ARGV[1]; if ($sourceurl eq '') { exit; }
my $cfmirror  = @ARGV[2]; if ($cfmirror  eq '') { exit; }

umask(0002);

$sourceurl =~ s@\%2f@/@ig;
$updatefile = substr($sourceurl,rindex($sourceurl,"/")+1);
$updatefile =~ s@\%20@ @ig;
my $oldfilename = $updatefile;
$updatefile =~ s@\?.*@@ig;
$vendorid =~ tr/A-Z/a-z/;

unless (-d "$repository/download/$vendorid")
{
	system("mkdir -p $repository/download/$vendorid");
	system("$apphome/bin/setperms.pl download/$vendorid");
}

exit if (-e "$repository/download/$vendorid/$updatefile");

system("touch $repository/download/$vendorid/$updatefile");

if ($cfmirror)
{
	$uuid = `echo $updatefile | md5sum`;
} else {
	$uuid = `echo $sourceurl  | md5sum`;
}

$uuid =~ s/[^0-9a-f]//g;
$uuid =~ s/([a-f\d]{8})([a-f\d]{4})([a-f\d]{4})([a-f\d]{4})([a-f\d]{12})/$1-$2-$3-$4-$5/;

if (-e "$swroot/accelerator.conf")
{
	&readhash("$swroot/accelerator.conf", \%xlratorsettings);
	if ($xlratorsettings{'ENABLE_LOG'} eq 'on') { $logging=1; };
	if ($xlratorsettings{'MAX_DOWNLOAD_RATE'} ne '') { $dlrate = "--limit-rate=" . int($xlratorsettings{'MAX_DOWNLOAD_RATE'} / 8) . "k" };
}

#if (-e "$swroot/proxy/settings") { &readhash("$swroot/proxy/settings", \%proxysettings); }

#if (-e "$swroot/proxy/advanced/settings")
#{
#	%proxysettings=();
#	&readhash("$swroot/proxy/advanced/settings", \%proxysettings);
#}

if (($xlratorsettings{'UPSTREAM_PROXY'}) && ($xlratorsettings{'UPSTREAM_USER'}))
{
	$login = "--proxy-user=\"$proxysettings{'UPSTREAM_USER'}\"";
	if ($xlratorsettings{'UPSTREAM_PASSWORD'})
	{
		$login .= " --proxy-password=\"$proxysettings{'UPSTREAM_PASSWORD'}\"";
	}
}

if ($xlratorsettings{'MAX_DOWNLOAD_RATE'} eq '')
{
	&writelog("Retrieving file for local cache: $updatefile");
} else {
	&writelog("Retrieving file for local cache at max. " . $xlratorsettings{'MAX_DOWNLOAD_RATE'} . " kBit/s: $updatefile");
}

$ENV{'http_proxy'} = $xlratorsettings{'UPSTREAM_PROXY'};
@http_header = `$wget $login --user-agent="$useragent" --spider -S $sourceurl 2>&1`;
$ENV{'http_proxy'} = '';

foreach (@http_header)
{
	chomp;
	if (/^\s*Content-Length:\s/) { s/[^0-9]//g; &writelog("Remote file size: $_ bytes"); }
	if (/^\s*Last-Modified:\s/) { s/^\s*Last-Modified:\s//; $remote_mtime = HTTP::Date::str2time($_); &writelog("Remote file date: $_"); }
}

$ENV{'http_proxy'} = $xlratorsettings{'UPSTREAM_PROXY'};
unlink "$repository/download/$vendorid/$updatefile";
$_ = system("$wget $login $dlrate --user-agent=\"$useragent\" -q -nc -P $repository/download/$vendorid '$sourceurl'");
if($updatefile ne $oldfilename) {
	rename("$repository/download/$vendorid/$oldfilename","$repository/download/$vendorid/$updatefile");
}
$ENV{'http_proxy'} = '';

if ($_ == 0)
{
	&writelog("Download finished with result code: OK");

	unless (-d "$repository/$vendorid")
	{
		system("mkdir -p $repository/$vendorid");
		system("$apphome/bin/setperms.pl $vendorid");
	}

	unless (-d "$repository/$vendorid/$uuid")
	{
		system("mkdir -p $repository/$vendorid/$uuid");
		system("$apphome/bin/setperms.pl $vendorid/$uuid");
	}

	&writelog("Moving file to the cache directory: $vendorid/$uuid");
	$updatefile =~ s@ @\\ @ig;
	system("mv $repository/download/$vendorid/$updatefile $repository/$vendorid/$uuid");
	# Workaround for IPCop's mv bug:
	utime time,$remote_mtime,"$repository/$vendorid/$uuid/$updatefile";
	$updatefile =~ s@\\ @ @ig;

	&setcachestatus("$repository/$vendorid/$uuid/source.url",$sourceurl);
	&setcachestatus("$repository/$vendorid/$uuid/status",$sfOk);
	&setcachestatus("$repository/$vendorid/$uuid/checkup.log",time);
	&setcachestatus("$repository/$vendorid/$uuid/access.log",time);

	system("$apphome/bin/setperms.pl $vendorid/$uuid/*");

} else {
	&writelog("Download finished with result code: ERROR");
	if (-e "$repository/download/$vendorid/$updatefile") { unlink ("$repository/download/$vendorid/$updatefile"); }
}


# -------------------------------------------------------------------

sub readhash
{
	my $filename = $_[0];
	my $hash = $_[1];
	my ($var, $val);

	if (-e $filename)
	{
		open(FILE, $filename) or die "Unable to read file $filename";
		while (<FILE>)
		{
			chop;
			($var, $val) = split /=/, $_, 2;
			if ($var)
			{
				$val =~ s/^\'//g;
				$val =~ s/\'$//g;

				# Untaint variables read from hash
				$var =~ /([A-Za-z0-9_-]*)/; $var = $1;
				$val =~ /([\w\W]*)/; $val = $1;
				$hash->{$var} = $val;
			}
		}
		close FILE;
	}
}

# -------------------------------------------------------------------

sub writelog
{
	print "$_[0]\n";
	if ($logging)
	{ 
        	open (LOGFILE,">>$logfile");
	        my @now = localtime(time);
        	printf LOGFILE "%04d-%02d-%02d %02d:%02d:%02d [%d] %s\n",$now[5]+1900,$now[4]+1,$now[3],$now[2],$now[1],$now[0],$$,$_[0];
	        close LOGFILE;
	}
}

# -------------------------------------------------------------------

sub setcachestatus
{
	open (FILE,">$_[0]");
	print FILE "$_[1]\n";
	close FILE;
}

# -------------------------------------------------------------------
