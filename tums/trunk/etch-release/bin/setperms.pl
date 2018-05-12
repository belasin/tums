#!/usr/bin/perl
#Set permissions recursively

use strict;

my $chmod_perms_file = '664';
my $chmod_perms_dir  = '775';
my $chown_user 	= 'proxy';
my $chown_group = 'www-data';
my $find  = '/usr/bin/find';
my $chmod = '/bin/chmod';
my $chown = '/bin/chown';

my $setperm_ex = '';

my $directory = shift; #Get the first argument 

if($directory eq "" || !-e $directory) {
	usage();	
}

ch_own($directory);
ch_mod($directory);

sub usage {
	#print "$0 <directory>\n";
	exit();
}

sub ch_own {
	my $directory = shift;
	system($find." $directory -exec $chown $chown_user:$chown_group \{\} \\;");
}


sub ch_mod {
	my $directory = shift;
	system($find." $directory -type f -exec $chmod $chmod_perms_file \{\} \\;");
	system($find." $directory -type d -exec $chmod $chmod_perms_dir \{\} \\;");
}