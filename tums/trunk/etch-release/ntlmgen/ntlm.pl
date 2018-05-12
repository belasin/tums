#!/usr/bin/perl
use Crypt::SmbHash;
 ( $lm, $nt ) = ntlmgen($ARGV[0]);
print $lm, " ", $nt, "\n";
