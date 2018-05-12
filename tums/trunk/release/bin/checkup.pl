#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2006,2007 marco.s - http://www.advproxy.net/update-accelerator
#
# $Id: checkup,v 2.0 2007/06/17 00:00:00 marco.s Exp $
#

use strict;

use HTTP::Date;

my $swroot='/etc/squid3';
my $apphome="/usr/local/tcs/tums/";
my $logfile="/var/log/squid/accelerate.checkup.log";
my $repository='/var/lib/samba/updates';
my $wget="/usr/bin/wget";
my $useragent="Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)";
my %proxysettings=();
my %xlratorsettings=();
my $download=0;
my $updatefile='';
my $sourceurl='';
my @sources=();
my @updatelist=();
my $logging=0;

my $sfUnknown  = "0";
my $sfOk       = "1";
my $sfOutdated = "2";
my $sfNoSource = "3";

if (-e "$swroot/accelerator.conf")
{
	&readhash("$swroot/accelerator.conf", \%xlratorsettings);
	if ($xlratorsettings{'FULL_AUTOSYNC'} eq 'on') { $download=1; };
	if ($xlratorsettings{'ENABLE_LOG'} eq 'on') { $logging=1; };
}

#if (-e "$swroot/proxy/settings") { &readhash("$swroot/proxy/settings", \%proxysettings); }

#if (-e "$swroot/proxy/advanced/settings")
#{
#	%proxysettings=();
#	&readhash("$swroot/proxy/advanced/settings", \%proxysettings);
#}

foreach (<$repository/*>)
{
	if (-d $_)
	{
		unless (/^$repository\/download$/) { push(@sources,$_); }
	}
}

foreach (@sources)
{
	@updatelist=<$_/*>;
	foreach(@updatelist)
	{
		if (-e "$_/source.url")
		{
			open (FILE,"$_/source.url");
			$sourceurl=<FILE>;
			close FILE;
			chomp($sourceurl);
			$updatefile = substr($sourceurl,rindex($sourceurl,'/')+1,length($sourceurl));
			&checksource($_);
		}
	}
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

sub getmtime
{
        my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($_[0]);

        return $mtime;
}

# -------------------------------------------------------------------

sub writelog
{
	print "$_[0]\n";
	if ($logging)
	{
	        open (LOGFILE,">>$logfile");
        	my @now = localtime(time);
	        printf LOGFILE "%04d-%02d-%02d %02d:%02d:%02d %s\n",$now[5]+1900,$now[4]+1,$now[3],$now[2],$now[1],$now[0],$_[0];
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

sub checksource
{
	my @http_header=();
	my $http_result='000 n/a';
	my $returncode=0;
	my $localfile='';
	my $remote_size=0;
	my $remote_mtime=0;
	my $login='';
	my $url='';
	my $cdir=$_[0];

	open (FILE,"$cdir/source.url");
	$url=<FILE>;
	close FILE;
	chomp($url);

	$localfile = $cdir . substr($url,rindex($url,'/'),length($url));

	if (($xlratorsettings{'UPSTREAM_PROXY'}) && ($xlratorsettings{'UPSTREAM_USER'}))
	{
		$login = "--proxy-user=\"$proxysettings{'UPSTREAM_USER'}\"";
		if ($xlratorsettings{'UPSTREAM_PASSWORD'})
		{
			$login .= " --proxy-password=\"$proxysettings{'UPSTREAM_PASSWORD'}\"";
		}
	}

	$ENV{'http_proxy'} = $xlratorsettings{'UPSTREAM_PROXY'};
	@http_header = `$wget $login --user-agent="$useragent" --spider -S $url 2>&1`;
	$ENV{'http_proxy'} = '';

	foreach (@http_header) 
	{
		chomp;
		if (/^\s*HTTP\/\d+\.\d+\s\d+\s+\w+/) { $http_result = $_; $http_result =~ s/^\s*HTTP\/\d+\.\d+\s+//; }
		if (/^\s*Content-Length:\s/) { $remote_size = $_; $remote_size =~ s/[^0-9]//g; }
		if (/^\s*Last-Modified:\s/) { $remote_mtime = $_; $remote_mtime =~ s/^\s*Last-Modified:\s//; $remote_mtime = HTTP::Date::str2time($remote_mtime) }
	}

	&writelog($localfile);
	&writelog("HTTP result: $http_result");
	&writelog("Source size: $remote_size");
	&writelog("Cached size: " . (-s $localfile));
	&writelog("Source time: $remote_mtime");
	&writelog("Cached time: " . getmtime($localfile));

	if ($http_result =~ /\d+\s+OK$/)
	{
		if (($remote_size == -s $localfile) && ($remote_mtime == getmtime($localfile)))
		{
			&writelog("Status: Ok");
			&setcachestatus("$cdir/status",$sfOk);
		} else {
			&writelog("Status: Outdated");
			&setcachestatus("$cdir/status",$sfOutdated);
			if ($download)
			{
				&writelog("Retrieving file from source: $remote_size bytes");
				$_ = system("$wget $login --user-agent=\"$useragent\" -q -O $localfile $url");
				&writelog("Download finished with code: $_");
				if ($_ == 0) { &setcachestatus("$cdir/status",$sfOk); } 
			}
		}
	} else {
		$_ =  $http_result;
		s/\D+//;
		if ($_ eq '404')
		{
			&writelog("Status: No source");
			&setcachestatus("$cdir/status",$sfNoSource);
		} else {
			&writelog("Status: Error");
			&setcachestatus("$cdir/status",$sfUnknown);
		}
	}
	
	&setcachestatus("$cdir/checkup.log",time);
}

# -------------------------------------------------------------------
