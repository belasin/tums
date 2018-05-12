#! /usr/bin/perl

#  RRGrapher.cgi - Round Robin Grapher, a Graph Construction Set for RRDTOOL
#  Copyright (C) 1999-2003  Dave Plonka
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# $Id: RRGrapher.cgi,v 1.32 2003/09/18 18:22:34 dplonka Exp $
# Dave Plonka <plonka@doit.wisc.edu>

use FindBin;
use CGI::Carp qw(fatalsToBrowser);
use File::Find;
use Sys::Hostname;
use POSIX; # for mktime, strftime, SEEK_SET
use IO::Handle; # for sysopen
use Fcntl ':flock'; # for flock

# { OS detection snarfed from mrtg, by Tobias Oetiker <oetiker@ee.ethz.ch>,
#   Dave Rand <dlr@bungi.com>, Stuart Schneider <schneis@testlab.orst.edu>, etc.

BEGIN {
    # Automatic OS detection ... do NOT touch
    if ( $^O =~ /^(?:(ms)?(dos|win(32|nt)?))/i ) {
        $OS = 'NT';
        $SL = '\\';
        $PS = ';';
    } elsif ( $^O =~ /^VMS$/i ) {
        $OS = 'VMS';
        $SL = '.';
        $PS = ':';
    } else {
        $OS = 'UNIX';
        $SL = '/';
        $PS = ':';
    }
}

# }

# { CONFIGURATION SECTION: #####################################################

# DIRECTORIES IN WHICH TO FIND ".RRD" FILES (will be find'ed [sic] recursively):
@rrddirs = (
'/var/local/flows/graphs',
'/var/local/stats/cricket/cricket-data',
);

# YOU MUST SET THESE CORRECTLY TO GET WORKING ON-LINE HELP BUTTONS IN RRGRAPHER!
# THE DIRECTORY IN WHICH THE RRDTOOL DOCS (e.g. "rrdgraph.pod") ARE INSTALLED:
$docdir = '/usr/local/rrdtool-1.0.33/doc'; # '/usr/local/src/rrdtool-ver/doc'
# THE FULL PATH TO THE PERL pod2html COMMAND:
$pod2html = '/usr/bin/pod2html'; # e.g. '/usr/local/bin/pod2html'

# NOTE! If using Apache version < 1.3, rename this script to have the "nph-"
# prefix in the name and change the following line to:
#    use CGI qw(:nph :standard :html3);
use CGI qw(:standard :html3);

# If you've installed "RRDs.pm" in an unusual place, add a "use lib" here:
# use lib '/my/secret/perl/lib/dir';

# image format (under Windows, note OPTIONAL CONFIGURATION which sets to gif):
$imgformat = 'png'; # or 'gif'

# If using mod_perl under apache, set $tmpfile to the path to a file in a
# directory to which the apache user can write, such as:
# $tmpfile = "/tmp/rrgtmp.${imgformat}";
$tmpfile = '';

# }{ OPTIONAL CONFIGURATION ####################################################

# Set this if you want to be able to fetch the time-series data for a single DS:
# (this is an obscure feature that I originally added just for my personal use,
#  No warranties, no documentation. - Dave):
$fetch = 0;

# FlowScan "events" FILE(S) - another obscure feature, used to specify the
# start and end times and title based on events specified in files of the
# format understood by the "event2vrule" script included with FlowScan:
@event_files = (
# '/var/local/flows/graphs/events.txt',
);

$errfile = ''; # standard error file - useful for IIS which discards STDERR?!

# This script must write graph images to temporary file under platforms
# where STDOUT between perl libraries and the web server is broken
# (such as Apache w/mod_perl or Windows 2000 running IIS).
#
# For IIS, this autoconfiguration should work:
# (If you'd like the temporary image file to be written to some specific
#  directory, you might want to prepend a path...)
if ('NT' eq $OS) {
   # image format - still use GIF on Windows for now...
   $imgformat = 'gif';
   $tmpfile = "rrgtmp.${imgformat}";
}

# } END CONFIGURATION SECTION ##################################################

# { try to autoconfigure for mod_perl:
if ('' eq $tmpfile && $ENV{GATEWAY_INTERFACE} =~ m/cgi-perl/i) {
   # info about GATEWAY_INTERFACE value found at:
   # http://www.perldoc.com/perl5.6.1/lib/Apache/Registry.html
   $tmpfile = "/tmp/rrgtmp.${imgformat}";
}
# }

use RRDs; # FIXME? if no RRDs, then use RRDp?

'$Revision: 1.32 $' =~ m/(\d+)\.(\d+)/ && (( $VERSION ) = sprintf("%d.%03d", $1, $2));

if ($errfile) {
   open(STDERR, ">$errfile") or warn "open \"$errfile\", \"w\": $!"
}

if (param('COPYING')) { # just generate the license and exit
   print header('text/plain');
   print <<'_EOF_'
		    GNU GENERAL PUBLIC LICENSE
		       Version 2, June 1991

 Copyright (C) 1989, 1991 Free Software Foundation, Inc.
                          675 Mass Ave, Cambridge, MA 02139, USA
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

			    Preamble

  The licenses for most software are designed to take away your
freedom to share and change it.  By contrast, the GNU General Public
License is intended to guarantee your freedom to share and change free
software--to make sure the software is free for all its users.  This
General Public License applies to most of the Free Software
Foundation's software and to any other program whose authors commit to
using it.  (Some other Free Software Foundation software is covered by
the GNU Library General Public License instead.)  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
this service if you wish), that you receive source code or can get it
if you want it, that you can change the software or use pieces of it
in new free programs; and that you know you can do these things.

  To protect your rights, we need to make restrictions that forbid
anyone to deny you these rights or to ask you to surrender the rights.
These restrictions translate to certain responsibilities for you if you
distribute copies of the software, or if you modify it.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must give the recipients all the rights that
you have.  You must make sure that they, too, receive or can get the
source code.  And you must show them these terms so they know their
rights.

  We protect your rights with two steps: (1) copyright the software, and
(2) offer you this license which gives you legal permission to copy,
distribute and/or modify the software.

  Also, for each author's protection and ours, we want to make certain
that everyone understands that there is no warranty for this free
software.  If the software is modified by someone else and passed on, we
want its recipients to know that what they have is not the original, so
that any problems introduced by others will not reflect on the original
authors' reputations.

  Finally, any free program is threatened constantly by software
patents.  We wish to avoid the danger that redistributors of a free
program will individually obtain patent licenses, in effect making the
program proprietary.  To prevent this, we have made it clear that any
patent must be licensed for everyone's free use or not licensed at all.

  The precise terms and conditions for copying, distribution and
modification follow.

		    GNU GENERAL PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. This License applies to any program or other work which contains
a notice placed by the copyright holder saying it may be distributed
under the terms of this General Public License.  The "Program", below,
refers to any such program or work, and a "work based on the Program"
means either the Program or any derivative work under copyright law:
that is to say, a work containing the Program or a portion of it,
either verbatim or with modifications and/or translated into another
language.  (Hereinafter, translation is included without limitation in
the term "modification".)  Each licensee is addressed as "you".

Activities other than copying, distribution and modification are not
covered by this License; they are outside its scope.  The act of
running the Program is not restricted, and the output from the Program
is covered only if its contents constitute a work based on the
Program (independent of having been made by running the Program).
Whether that is true depends on what the Program does.

  1. You may copy and distribute verbatim copies of the Program's
source code as you receive it, in any medium, provided that you
conspicuously and appropriately publish on each copy an appropriate
copyright notice and disclaimer of warranty; keep intact all the
notices that refer to this License and to the absence of any warranty;
and give any other recipients of the Program a copy of this License
along with the Program.

You may charge a fee for the physical act of transferring a copy, and
you may at your option offer warranty protection in exchange for a fee.

  2. You may modify your copy or copies of the Program or any portion
of it, thus forming a work based on the Program, and copy and
distribute such modifications or work under the terms of Section 1
above, provided that you also meet all of these conditions:

    a) You must cause the modified files to carry prominent notices
    stating that you changed the files and the date of any change.

    b) You must cause any work that you distribute or publish, that in
    whole or in part contains or is derived from the Program or any
    part thereof, to be licensed as a whole at no charge to all third
    parties under the terms of this License.

    c) If the modified program normally reads commands interactively
    when run, you must cause it, when started running for such
    interactive use in the most ordinary way, to print or display an
    announcement including an appropriate copyright notice and a
    notice that there is no warranty (or else, saying that you provide
    a warranty) and that users may redistribute the program under
    these conditions, and telling the user how to view a copy of this
    License.  (Exception: if the Program itself is interactive but
    does not normally print such an announcement, your work based on
    the Program is not required to print an announcement.)

These requirements apply to the modified work as a whole.  If
identifiable sections of that work are not derived from the Program,
and can be reasonably considered independent and separate works in
themselves, then this License, and its terms, do not apply to those
sections when you distribute them as separate works.  But when you
distribute the same sections as part of a whole which is a work based
on the Program, the distribution of the whole must be on the terms of
this License, whose permissions for other licensees extend to the
entire whole, and thus to each and every part regardless of who wrote it.

Thus, it is not the intent of this section to claim rights or contest
your rights to work written entirely by you; rather, the intent is to
exercise the right to control the distribution of derivative or
collective works based on the Program.

In addition, mere aggregation of another work not based on the Program
with the Program (or with a work based on the Program) on a volume of
a storage or distribution medium does not bring the other work under
the scope of this License.

  3. You may copy and distribute the Program (or a work based on it,
under Section 2) in object code or executable form under the terms of
Sections 1 and 2 above provided that you also do one of the following:

    a) Accompany it with the complete corresponding machine-readable
    source code, which must be distributed under the terms of Sections
    1 and 2 above on a medium customarily used for software interchange; or,

    b) Accompany it with a written offer, valid for at least three
    years, to give any third party, for a charge no more than your
    cost of physically performing source distribution, a complete
    machine-readable copy of the corresponding source code, to be
    distributed under the terms of Sections 1 and 2 above on a medium
    customarily used for software interchange; or,

    c) Accompany it with the information you received as to the offer
    to distribute corresponding source code.  (This alternative is
    allowed only for noncommercial distribution and only if you
    received the program in object code or executable form with such
    an offer, in accord with Subsection b above.)

The source code for a work means the preferred form of the work for
making modifications to it.  For an executable work, complete source
code means all the source code for all modules it contains, plus any
associated interface definition files, plus the scripts used to
control compilation and installation of the executable.  However, as a
special exception, the source code distributed need not include
anything that is normally distributed (in either source or binary
form) with the major components (compiler, kernel, and so on) of the
operating system on which the executable runs, unless that component
itself accompanies the executable.

If distribution of executable or object code is made by offering
access to copy from a designated place, then offering equivalent
access to copy the source code from the same place counts as
distribution of the source code, even though third parties are not
compelled to copy the source along with the object code.

  4. You may not copy, modify, sublicense, or distribute the Program
except as expressly provided under this License.  Any attempt
otherwise to copy, modify, sublicense or distribute the Program is
void, and will automatically terminate your rights under this License.
However, parties who have received copies, or rights, from you under
this License will not have their licenses terminated so long as such
parties remain in full compliance.

  5. You are not required to accept this License, since you have not
signed it.  However, nothing else grants you permission to modify or
distribute the Program or its derivative works.  These actions are
prohibited by law if you do not accept this License.  Therefore, by
modifying or distributing the Program (or any work based on the
Program), you indicate your acceptance of this License to do so, and
all its terms and conditions for copying, distributing or modifying
the Program or works based on it.

  6. Each time you redistribute the Program (or any work based on the
Program), the recipient automatically receives a license from the
original licensor to copy, distribute or modify the Program subject to
these terms and conditions.  You may not impose any further
restrictions on the recipients' exercise of the rights granted herein.
You are not responsible for enforcing compliance by third parties to
this License.

  7. If, as a consequence of a court judgment or allegation of patent
infringement or for any other reason (not limited to patent issues),
conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot
distribute so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you
may not distribute the Program at all.  For example, if a patent
license would not permit royalty-free redistribution of the Program by
all those who receive copies directly or indirectly through you, then
the only way you could satisfy both it and this License would be to
refrain entirely from distribution of the Program.

If any portion of this section is held invalid or unenforceable under
any particular circumstance, the balance of the section is intended to
apply and the section as a whole is intended to apply in other
circumstances.

It is not the purpose of this section to induce you to infringe any
patents or other property right claims or to contest validity of any
such claims; this section has the sole purpose of protecting the
integrity of the free software distribution system, which is
implemented by public license practices.  Many people have made
generous contributions to the wide range of software distributed
through that system in reliance on consistent application of that
system; it is up to the author/donor to decide if he or she is willing
to distribute software through any other system and a licensee cannot
impose that choice.

This section is intended to make thoroughly clear what is believed to
be a consequence of the rest of this License.

  8. If the distribution and/or use of the Program is restricted in
certain countries either by patents or by copyrighted interfaces, the
original copyright holder who places the Program under this License
may add an explicit geographical distribution limitation excluding
those countries, so that distribution is permitted only in or among
countries not thus excluded.  In such case, this License incorporates
the limitation as if written in the body of this License.

  9. The Free Software Foundation may publish revised and/or new versions
of the General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

Each version is given a distinguishing version number.  If the Program
specifies a version number of this License which applies to it and "any
later version", you have the option of following the terms and conditions
either of that version or of any later version published by the Free
Software Foundation.  If the Program does not specify a version number of
this License, you may choose any version ever published by the Free Software
Foundation.

  10. If you wish to incorporate parts of the Program into other free
programs whose distribution conditions are different, write to the author
to ask for permission.  For software which is copyrighted by the Free
Software Foundation, write to the Free Software Foundation; we sometimes
make exceptions for this.  Our decision will be guided by the two goals
of preserving the free status of all derivatives of our free software and
of promoting the sharing and reuse of software generally.

			    NO WARRANTY

  11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN
OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
REPAIR OR CORRECTION.

  12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGES.

		     END OF TERMS AND CONDITIONS

	Appendix: How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
convey the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) 19yy  <name of author>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

Also add information on how to contact you by electronic and paper mail.

If the program is interactive, make it output a short notice like this
when it starts in an interactive mode:

    Gnomovision version 69, Copyright (C) 19yy name of author
    Gnomovision comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.

The hypothetical commands `show w' and `show c' should show the appropriate
parts of the General Public License.  Of course, the commands you use may
be called something other than `show w' and `show c'; they could even be
mouse-clicks or menu items--whatever suits your program.

You should also get your employer (if you work as a programmer) or your
school, if any, to sign a "copyright disclaimer" for the program, if
necessary.  Here is a sample; alter the names:

  Yoyodyne, Inc., hereby disclaims all copyright interest in the program
  `Gnomovision' (which makes passes at compilers) written by James Hacker.

  <signature of Ty Coon>, 1 April 1989
  Ty Coon, President of Vice

This General Public License does not permit incorporating your program into
proprietary programs.  If your program is a subroutine library, you may
consider it more useful to permit linking proprietary applications with the
library.  If this is what you want to do, use the GNU Library General
Public License instead of this License.
_EOF_
   ;
   exit 0
} elsif (param('rrdgraph')) {
   $|=1;
   print header();
   chdir '/tmp' || die; # pod2html likes to write temp files
   my $command = "${pod2html} ${docdir}/rrdgraph.pod";
   exec $command;
   die "exec \"$command\": $!"
} elsif (param('rrdfetch')) {
   $|=1;
   print header();
   chdir '/tmp' || die; # pod2html likes to write temp files
   my $command = "${pod2html} ${docdir}/rrdfetch.pod";
   exec $command;
   die "exec \"$command\": $!"
} elsif (param('rpntutorial')) {
   $|=1;
   print header();
   chdir '/tmp' || die; # pod2html likes to write temp files
   $command = "${pod2html} ${docdir}/rpntutorial.pod";
   exec $command;
   die "exec \"$command\": $!"
} elsif (param('cdeftutorial')) {
   $|=1;
   print header();
   chdir '/tmp' || die; # pod2html likes to write temp files
   $command = "${pod2html} ${docdir}/cdeftutorial.pod";
   exec $command;
   die "exec \"$command\": $!"
}

# { "globals":
# color list wasn generated from X11 "rgb.txt" with:
# perl -lane 'print(sprintf("\"#%02X%02X%02X\"", $F[0..2]), " => \"",
#             join(" ", @F[3 .. $#F]), "\",") unless $F[0] =~ m/\s*!/' rgb.txt

$Script = $FindBin::Script;
$Script =~ s/\..*$//;

%colors = (

"#FFFAFA" => "snow",
"#F8F8FF" => "ghost white",
"#F5F5F5" => "white smoke",
"#DCDCDC" => "gainsboro",
"#FFFAF0" => "floral white",
"#FDF5E6" => "old lace",
"#FAF0E6" => "linen",
"#FAEBD7" => "antique white",
"#FFEFD5" => "papaya whip",
"#FFEBCD" => "blanched almond",
"#FFE4C4" => "bisque",
"#FFDAB9" => "peach puff",
"#FFDEAD" => "navajo white",
"#FFE4B5" => "moccasin",
"#FFF8DC" => "cornsilk",
"#FFFFF0" => "ivory",
"#FFFACD" => "lemon chiffon",
"#FFF5EE" => "seashell",
"#F0FFF0" => "honeydew",
"#F5FFFA" => "mint cream",
"#F0FFFF" => "azure",
"#F0F8FF" => "alice blue",
"#E6E6FA" => "lavender",
"#FFF0F5" => "lavender blush",
"#FFE4E1" => "misty rose",
"#FFFFFF" => "white",
"#000000" => "black",
"#2F4F4F" => "dark slate gray",
"#696969" => "dim gray",
"#708090" => "slate gray",
"#778899" => "light slate gray",
"#BEBEBE" => "gray",
"#D3D3D3" => "light gray",
"#191970" => "midnight blue",
"#000080" => "navy",
"#000080" => "navy blue",
"#6495ED" => "cornflower blue",
"#483D8B" => "dark slate blue",
"#6A5ACD" => "slate blue",
"#7B68EE" => "medium slate blue",
"#8470FF" => "light slate blue",
"#0000CD" => "medium blue",
"#4169E1" => "royal blue",
"#0000FF" => "blue",
"#1E90FF" => "dodger blue",
"#00BFFF" => "deep sky blue",
"#87CEEB" => "sky blue",
"#87CEFA" => "light sky blue",
"#4682B4" => "steel blue",
"#B0C4DE" => "light steel blue",
"#ADD8E6" => "light blue",
"#B0E0E6" => "powder blue",
"#AFEEEE" => "pale turquoise",
"#00CED1" => "dark turquoise",
"#48D1CC" => "medium turquoise",
"#40E0D0" => "turquoise",
"#00FFFF" => "cyan",
"#E0FFFF" => "light cyan",
"#5F9EA0" => "cadet blue",
"#66CDAA" => "medium aquamarine",
"#7FFFD4" => "aquamarine",
"#006400" => "dark green",
"#556B2F" => "dark olive green",
"#8FBC8F" => "dark sea green",
"#2E8B57" => "sea green",
"#3CB371" => "medium sea green",
"#20B2AA" => "light sea green",
"#98FB98" => "pale green",
"#00FF7F" => "spring green",
"#7CFC00" => "lawn green",
"#00FF00" => "green",
"#7FFF00" => "chartreuse",
"#00FA9A" => "medium spring green",
"#ADFF2F" => "green yellow",
"#32CD32" => "lime green",
"#9ACD32" => "yellow green",
"#228B22" => "forest green",
"#6B8E23" => "olive drab",
"#BDB76B" => "dark khaki",
"#F0E68C" => "khaki",
"#EEE8AA" => "pale goldenrod",
"#FAFAD2" => "light goldenrod yellow",
"#FFFFE0" => "light yellow",
"#FFFF00" => "yellow",
"#FFD700" => "gold",
"#EEDD82" => "light goldenrod",
"#DAA520" => "goldenrod",
"#B8860B" => "dark goldenrod",
"#BC8F8F" => "rosy brown",
"#CD5C5C" => "indian red",
"#8B4513" => "saddle brown",
"#A0522D" => "sienna",
"#CD853F" => "peru",
"#DEB887" => "burlywood",
"#F5F5DC" => "beige",
"#F5DEB3" => "wheat",
"#F4A460" => "sandy brown",
"#D2B48C" => "tan",
"#D2691E" => "chocolate",
"#B22222" => "firebrick",
"#A52A2A" => "brown",
"#E9967A" => "dark salmon",
"#FA8072" => "salmon",
"#FFA07A" => "light salmon",
"#FFA500" => "orange",
"#FF8C00" => "dark orange",
"#FF7F50" => "coral",
"#F08080" => "light coral",
"#FF6347" => "tomato",
"#FF4500" => "orange red",
"#FF0000" => "red",
"#FF69B4" => "hot pink",
"#FF1493" => "deep pink",
"#FFC0CB" => "pink",
"#FFB6C1" => "light pink",
"#DB7093" => "pale violet red",
"#B03060" => "maroon",
"#C71585" => "medium violet red",
"#D02090" => "violet red",
"#FF00FF" => "magenta",
"#EE82EE" => "violet",
"#DDA0DD" => "plum",
"#DA70D6" => "orchid",
"#BA55D3" => "medium orchid",
"#9932CC" => "dark orchid",
"#9400D3" => "dark violet",
"#8A2BE2" => "blue violet",
"#A020F0" => "purple",
"#9370DB" => "medium purple",
"#D8BFD8" => "thistle",
"#A9A9A9" => "dark gray",
"#00008B" => "dark blue",
"#008B8B" => "dark cyan",
"#8B008B" => "dark magenta",
"#8B0000" => "dark red",
"#90EE90" => "light green",

);

# Default colors - these are from gnuplot:
my @def_colors =
   qw(#0000FF #00FFFF #00FF00 #A0522D #FFA500 #FF7F50 #FF0000 #FF00FF);

%files = ();

@chr = ('A' .. 'Z', 'a' .. 'z');
@ord{@chr} = (0 .. $#chr);

@files = (); # list of rrd file names (used by the File::Find "wanted" sub)

my $image; # the HTML that displays the image image in the upper "view port"
my $text; # the HTML that displays the text in lower "view port"

my $event; # the selected event description (if @event_files is used)

my $IMGFORMAT = uc($imgformat);

# }

if (param('event')) {
   my @event = param('event');
   my $window = param('window');
   if (!$window) {
      $window = 2*86400; # default to 48 hours
   }
   @F = split(m/[\t ]+/, $event[0]);
   my $whence = shift(@F);
   $event = "@F";
   if (!param('start')) {
      param('start',
	    strftime("%b %d %Y %H:%M", localtime($whence - int($window/2))));
   }
   if (!param('end')) {
      param('end',
	    strftime("%b %d %Y %H:%M", localtime($whence + int($window/2))));
   }
   if (!param('title')) {
      param('title', $event);
   }
}

if (param('logo')) {
   $|=1;
   print header('image/gif');
} elsif (param('graph')) {
   $|=1;
   print header("image/$imgformat");
} elsif (param('fetch')) {
   print header('text/plain')
} else {
   print header();
   # { Do a title for this page
   if (param('command')) {
      if (param('title')) {
         print title("$Script: " . param('title')), "\n"
      } else {
         print title("$Script: Untitled"), "\n"
      }
   } else {
      print title("$Script"), "\n";
   }
   # }

   $image = "<IMG SRC=\"?logo=1\" alt=\"[$Script logo]\">\n";

   if (param('rgb_file')) { # user specified a color file
      %colors = ();
      my $rgb_txt = param('rgb_file');
      if (open(COLORS, "<${rgb_txt}")) {
         while (<COLORS>) {
	    next if (m/\s*!/); # skip comments
	    @F = split(m/\s+/);
	    # skip names with whitespace (these are duplicates anyway):
	    next if $#F > 3;
	    $name = join(' ', @F[3 .. $#F]);
	    # skip names with numbers in them (for brevity):
	    next if $name =~ m/\d$/;
	    $colors{sprintf("#%02X%02X%02X", $F[0], $F[1], $F[2])} = $name
         }
         close(COLORS)
      } else {
         warn "open \"${rgb_txt}\", \"r\": $!"
      }
   }
   if (!%colors) { # be sure there are some colors...
      $colors{'#000000'} = 'black';
      $colors{'#FF0000'} = 'red';
      $colors{'#00FF00'} = 'green';
      $colors{'#0000FF'} = 'blue';
      $colors{'#FFFFFF'} = 'white'
   }
   @colors = sort {
                my $aye = join(' ', reverse(split(m/\s+/, $colors{$a})));
                my $bee = join(' ', reverse(split(m/\s+/, $colors{$b})));
                $aye cmp $bee
             } keys(%colors)
}

# { build a DS (Data Source) hash from the CGI params:
%DS = ();
{
foreach my $DS (param('DS')) {
   my($var, $database, $db, $cf, $name, $rpn, $type, $color, $label) =
      split(m/:/, $DS);
   if (param("${var}_type")) {
      $type = param("${var}_type");
   }
   if (param("${var}_color")) {
      $color = param("${var}_color");
   }
   if (param("${var}_label")) {
      $label = param("${var}_label");
   }
   $DS{$var} = { database => $database,
		 db => $db,
		 cf => $cf,
		 name => $name,
		 rpn => $rpn,
		 type => $type,
		 color => $color,
		 label => $label }
}
}
# FIXME - show an error if first DS with a plot $type other than 'NONE' has
#         a $type of 'STACK' (because the first DS can't be a 'STACK')
# }

if (param('add')) {
   my $def = 0; # index into @def_colors
   my @database = param('database');
   my $cf = param('CF');
   die unless $cf;
   if (@database) {
   foreach $database (@database) {
      # Since we're just trying to determine the DS names, we specificy as
      # little a range of time as possible *and* one that will be tolerated
      # by RRDs::fetch at the time of this writing (RRDTOOL 1.0.13).
      my ($start, $step, $names, $data) = RRDs::fetch($database,
						      $cf,
						      '-s', 0,
						      '-e', 0);
      my $error;
      if ($error = RRDs::error) {
         $text = <<_EOF_
An error occured while $FindBin::Script was trying to determine DS names:<br>
_EOF_
         ;
         $text .= pre("RRDs::fetch('$database', '$cf', '-s', 0, '-e', 0): ",
		      $error)
      } else {
	 my $name;
	 $source_regexp = param('source_regexp');
	 my $ord = 0;
	 foreach $name (@$names) {
	    next if $source_regexp && $name !~ m/$source_regexp/i;
	    my $chr = $chr[$ord];
	    while (defined($DS{$chr})) { # skip passed defined DSes...
	       $ord++;
	       $chr = $chr[$ord]
	    }
	    if (!grep($database eq $_->{database} && 
		      $cf eq $_->{cf} &&
		      $name eq $_->{name},
		      values(%DS))) {
	       if ($def == $#def_colors) {
		  $def = 0
	       }
	       $DS{$chr} = { database => $database,
			     cf => $cf,
			     name => $name,
			     color => $def_colors[$def],
			     type => 'LINE1' };
	       $ord++;
	       $def++
	    }
	 }
      }
   }
      if ('' eq $text) {
         $text = <<_EOF_
Please examine the "Data Sources" and optionally change the "Plot Type"<br>
and/or color for each, then choose either "Graph Data Sources" or<br>
"Graph Data Sources to $IMGFORMAT" to produce the graph.
_EOF_
      }
   } else {
      $text = <<_EOF_
Please select one or more items from the list of "Available Databases" and<br>
then choose "Add &gt;&gt;".
_EOF_
   }
} elsif (param('fetch')) {
   my $def = 0; # index into @def_colors
   my @database = param('database');
   my $cf = param('CF');
   die unless $cf;
   if (1 == @database) {
      my $database = $database[0];
      my @args = ($database, $cf);
      my ($start, $step, $names, $data) = RRDs::fetch(@args);
      my $error;
      if ($error = RRDs::error) {
         $text = <<_EOF_
An error occured while $FindBin::Script was trying to determine DS names:
_EOF_
         ;
         $text .= pre("RRDs::fetch(@args): ",
		      $error)
      } else {
	 my $name;
	 my @columns;
	 my @names;
	 $source_regexp = param('source_regexp');
	 my $lcv = 0;
	 foreach $name (@$names) {
	    if ('' eq $source_regexp or $name =~ m/$source_regexp/i) {
	       push(@columns, $lcv);
	       push(@names, $name)
	    }
	    $lcv++
	 }
	 if (0 == @columns) {
	    $text = "ERROR: RegExp did not match any Data Source names: (@$names).\n";
            goto fetch_error
	 }
         my @args = ($database, $cf);
	 if (param('start')) {
	    push(@args, '-s', param('start'))
	 }
	 if (param('end')) {
	    push(@args, '-e', param('end'))
	 }
         my ($start, $step, $names, $data) = RRDs::fetch(@args);
         if ($error = RRDs::error) {
            $text = <<_EOF_
An error occured while $FindBin::Script was trying to determine DS names:
_EOF_
            ;
            $text .= pre("RRDs::fetch(@args): ",
		         $error);
         } else {
	    printf("# Generated by %s v$VERSION on %s, %s\n",
		   $FindBin::Script, hostname, scalar localtime);
	    print "#\n";
	    print "# rrdtool fetch arguments: '", join ("', '", @args), "'\n";
	    print "# event: \"$event\"\n" if $event;
	    printf("# start time: %s \n", scalar localtime $start);
	    printf("# end   time: %s \n",
		   scalar localtime $start+@$data*$step);
	    printf("# (%ld data points, %ld second interval",
		   scalar @$data, $step);
	    my $time_t = $start;
	    # { make a first pass at the data duplicating the previous value
	    #   into positions that would otherwise be "not a number" (nan).
	    my @prevrow = ();
	    my $replaced = 0;
	    foreach my $row (@$data) {
	       if (@prevrow) {
		  foreach my $column (@columns) {
		     if ('' eq $row->[$column]) {
			# if this value is undefined (i.e. "nan"),
			# repeat the previous value:
			$row->[$column] = $prevrow[$column];
			$replaced++
		     }
		  }
	       }
	       @prevrow = @$row;
	       $time_t += $step
	    }
	    if ($replaced) {
	       printf(", replicated %ld value(s) in \"nan\" positions",
		      $replaced)
	    }
	    print ")\n#\n";
	    print "# columns: @names\n";
	    foreach my $row (@$data) {
	       my @vals = ();
	       foreach my $n (@columns) {
		  push(@vals,
		       ('' eq $row->[$n])? 'nan' : sprintf("%e", $row->[$n]))
	       }
	       print "@vals\n"
	    }
	    # }
	 }
      }
   } else {
      $text = <<_EOF_
Please select ONE of the "Available Databases" and then choose "Fetch".
_EOF_
   }
fetch_error:
   print($text) if $text;
   exit 0
} elsif (param('remove')) {
   my $type = param('action_type');
   if ('all' eq $type) {
      grep(delete($DS{$_}), keys(%DS))
   } else { # delete selected DSes
      my $ord;
      for ($ord = 0; $ord < $ord{param('add_chr')}; $ord++) {
	 my $chr = $chr[$ord];
	 next unless defined($DS{$chr});
         delete($DS{$chr}) if param("${chr}_selected")
      }
   }
} elsif (param('add_cdef')) {
   my $chr = param('add_chr');
   my $rpn = param('add_rpn');
   if ($chr && $rpn) {
      $DS{$chr} = { rpn => $rpn,
		    color => $def_colors[0],
		    type => 'LINE1' }
   }
} elsif (param('default_colors')) {
   my $def = 0;
   foreach my $chr (sort keys(%DS)) {
      next if ('NONE' eq $DS{$chr}{type}); # don't bother with unplotted DSes
      if ($def == $#def_colors) {
	 # wrap-around, since we don't have an unlimited number of colors
         $def = 0
      }
      $DS{$chr}{color} = $def_colors[$def];
      $def++;
   }
} elsif (param('command') || param('graph')) {
   my $type = param('action_type');
   my ($chr, @DEF, @CDEF, @PLOT, @LEGEND, @options);
   my $statfmt = param('statfmt');
   if ('' eq $statfmt) {
      $statfmt = '%lf' # default
   }

   foreach $chr (sort keys(%DS)) {
      # DEF:vname=rrd:ds-name:CF
      if ($DS{$chr}{database}) { # it's a DEF (rather than CDEF)
         push(@DEF, "DEF:${chr}=" . join(':',
					 $DS{$chr}{database},
					 $DS{$chr}{name},
					 $DS{$chr}{cf}))
      } else { # RPN expression
         push(@DEF, "CDEF:${chr}=" . $DS{$chr}{rpn})
      }
      # next unless ('all' eq $type || param("${chr}_selected"));
      if ('NONE' ne $DS{$chr}{type}) {
	 my $label;
	 if ($DS{$chr}{label}) {
	    $label = $DS{$chr}{label}
	 } elsif ($DS{$chr}{rpn}) {
	    $label = "$chr) $DS{$chr}{rpn}"
	 } else {
	    $label = "$chr) $DS{$chr}{db} $DS{$chr}{cf} $DS{$chr}{name}"
	 }
         push(@PLOT,
	    $DS{$chr}{type} . ":${chr}" . $DS{$chr}{color} . ":${label}");
	 if (param('statistics')) {
            push(@PLOT,
	       "GPRINT:${chr}:MIN:(min=${statfmt}",
	       "GPRINT:${chr}:AVERAGE:ave=${statfmt}",
	       "GPRINT:${chr}:MAX:max=${statfmt})",
	       'COMMENT:\n');
	 }
      } else {
         push(@PLOT,
	      "COMMENT:$chr) $DS{$chr}{db} $DS{$chr}{cf} $DS{$chr}{name}",
	      'COMMENT:\n')
      }
   }
   my($option, $opt);
   foreach $opt ('start', 'end',
		 'x-grid', 'y-grid', 
                 'vertical-label',
		 'width', 'height',
		 'interlaced',
		 'logarithmic',
		 'upper-limit', 'lower-limit',
                 'rigid',
		 'base',
		 'color',
		 'title') {
      if (param($opt)) {
         push(@options, "--${opt}", param($opt))
      }
   }
   if (param('graph')) { # just generate the graph to standard output

      # On Windows with IIS the standard output to which RRDs::graph writes
      # its output doesn't seem to get tranferred over to the web browser...
      # I don't understand this, nor do I really care to.  Instead, under
      # windows we'll write the output to a temporary file (blocking as
      # necessary in case another instance of this script is using the
      # temporary file) then read the file content, and print it to perl's
      # STDOUT (which, luckily does seem to get tranferred over to the web
      # browser).

      # If "/dev/fd/1" exists and is writable (such as under Solaris and Linux)
      # we use it rather than specifying standard output using '-' as the file-
      # name, since older versions of RRDTOOL did not support filename as "-".
      # If a broken graph results because you're on a platform that doesn't
      # support accessing standard output as "/dev/fd/1" and your RRDTOOL is
      # so old that it doesn't understand "-" (e.g. ".99.20") then you must
      # upgrade RRDTOOL.

      my $file;
      if ($tmpfile) {
	 $file = $tmpfile
      } elsif (-w '/dev/fd/1') {
	 $file = '/dev/fd/1'
      } else {
	 $file = '-'
      }

      if ($tmpfile) {
         if (!sysopen(OUTPUT, $file, O_RDWR|O_CREAT, 0777)) {
            die "sysopen \"$file\": $!";
         }
         binmode(OUTPUT);
         flock(OUTPUT, LOCK_EX) or warn "flock: $!";
	 truncate(OUTPUT, 0) or warn "truncate: $!";
         OUTPUT->autoflush(1);
      }

      RRDs::graph($file,
		  '--imgformat', $IMGFORMAT,
		  @options,
		  @DEF, @PLOT, @LEGEND);

      my $error=RRDs::error;
      my $status = 0;
      if ($error){
         warn $error;
	 $status = 1
      }

      if ($tmpfile) {
	 my @stat = stat($tmpfile);
	 warn "RRDs::graph produced empty file \"$tmpfile\"?" if 0 == $stat[7];
	 # unnecessary? # seek(OUTPUT, 0, SEEK_SET) or warn "seek: $!";
	 open(OUTPUT_TOO, "<$tmpfile") or die "open: $!";
	 select(OUTPUT_TOO);
         $/ = undef;
         print STDOUT <OUTPUT_TOO>;
	 close(OUTPUT_TOO);
	 flock(OUTPUT, LOCK_UN) or warn "flock: $!";
	 close(OUTPUT);
	 unlink($tmpfile) or warn "unlink \"$tmpfile\": $!";
      }

      exit $status

   } else { # command
      $image = "<IMG SRC=\"?" . query_string() .
         "&graph=1\" alt=\"[what you asked for]\">\n";
      if ('NT' ne $OS) {
         $text = pre("rrdtool graph /your/file/name/here.$imgformat \\\n'" .
	             join("' \\\n'", '--imgformat', $IMGFORMAT, @options, @DEF,
		     @PLOT, @LEGEND) . "'\n");
	 # join "'--opt' \\\n'optarg'" lines
         $text =~ s/\n'(--.*?)'\s+\\\n/\n$1 /g;
      } else {
	 # join into one _long_ line for the Windows CLI and use double-quotes:
         $text = pre("rrdtool graph /your/file/name/here.$imgformat \"" .
	             join("\" \"", '--imgformat', $IMGFORMAT, @options, @DEF,
		     @PLOT, @LEGEND) . "\"\n");
      }
   }
} elsif (param('logo')) {
   printlogo();
   exit 0
}

if (!param('graph')) { # show the whole form
      print <<_EOF_
<CENTER>
<TABLE BGCOLOR=WHITE BORDER=1 CELLSPACING=4 CELLPADDING=8>
<TR>
<TD>
_EOF_
      ;
      print $image;
      print <<_EOF_
</TD>
</TR>
<TR>
<TD>
_EOF_
      ;
      if ('' eq $text) {
	 my $licurl = url() . '?COPYING=1';
         print <<_EOF_

    $Script version $VERSION, Copyright (C) 1999-2003 Dave Plonka<br>
    $Script comes with ABSOLUTELY NO WARRANTY.<br>
    This is free software, and you are welcome to redistribute it<br>
    under certain conditions; read `<a href="$licurl">COPYING</a>' for details.

_EOF_
         ;
      } else {
         print $text;
      }
      print <<_EOF_
</TD>
</TR>
</TABLE>
</CENTER>
_EOF_
   ;
   # We skip files with ":" in the name because RRDTOOL graph can't handle them:
   find(sub { -f $_ &&
	      /^.*\.rrd$/ &&
	      !/:/ &&
	      push(@files, "$File::Find::dir/$_") },
        @rrddirs);
   @files = sort by_number_kludge @files;
   if (0) {
      %files = munglabels2(@files);
   } else {
      foreach my $file (@files) {
         my $label = $file;
         $label =~ s|^.*/||;
         $label =~ s|\.rrd$||;
         $files{$file} = $label
      }
   }

   print startform('get'), "\n";

   print <<_EOF_
<TABLE>

<TR>
<TH>Available Databases<br><hr></TH>
<TH></TH>
<TH>Data Sources<br><hr></TH>
</TR>
_EOF_
   ;

   print("<TR>\n");

   print("<TD>\n");
   CGI::delete('database');
   print scrolling_list(-name => 'database',
			'-values' => \@files,
			-default => [],
			-size => 10,
			-height => '100%',
			-width => '100%',
			-multiple => 'true',
			-labels => \%files), br(), "\n";
   print("</TD>\n");

   print("<TD>\n");
   print submit(-name => 'add', -value => 'Add >>'), "\n";
   print("<br>\n");
   if ($fetch) {
      print submit(-name => 'fetch', -value => 'Fetch'), "\n";
      print("</TD>\n");
   }

   print("<TD>\n");

   if (%DS) {
   print <<_EOF_
<TABLE BORDER=1 CELLSPACING=4 CELLPADDING=8>
<TR>
<TH>Name</TH>
<TH>Label</TH>
<TH>Plot Type</TH>
_EOF_
   ;
   print "<TH>Colors:",
      submit(-name => 'update_colors', -value => 'Refresh'),
      "</TH>\n";
   # The default colors button doesn't work right (yet)
   # submit(-name => 'default_colors', -value => 'Default'),
   print "</TR>\n";
   my $first = 1;
   foreach my $chr (sort keys(%DS)) {
      print "<TR>\n";
      print "<TD>", checkbox(-name => "${chr}_selected", -label => $chr),
	 "</TD>\n";
      print "<TD>",
	 # We abbreviate "AVERAGE" to "AVE" in the label:
	 textfield(-name => "${chr}_label",
	           -default => $DS{$chr}{rpn}?
		$DS{$chr}{rpn} :
		$files{$DS{$chr}{database}} . " " .
		   ('AVERAGE' eq $DS{$chr}{cf}? 'AVE' : $DS{$chr}{cf}) .
		   " $DS{$chr}{name}"),
	 "</TD>\n";
      print "<TD>";
      if ($first) { # don't allow 'STACK' for 1st DS:
	 print popup_menu(-name => "${chr}_type",
                    '-values' => ['LINE1', 'LINE2', 'LINE3', 'AREA', 'NONE'],
                    '-default' => $DS{$chr}{type})
      } else {
	 print popup_menu(-name => "${chr}_type",
                    '-values' => ['LINE1', 'LINE2', 'LINE3',
				  'AREA', 'STACK', 'NONE'],
                    '-default' => $DS{$chr}{type})
      }
      print "</TD>\n";
      print "<TD BGCOLOR=$DS{$chr}{color}>",
	 popup_menu(-name => "${chr}_color",
		    '-values' => \@colors,
		    -default => $DS{$chr}{color},
		    -labels => \%colors), "</TD>\n";
      print "</TR>\n";
      $first = 0
   }
   print <<_EOF_
</TABLE>
_EOF_
   ;
   print submit(-name => 'remove', -value => 'Remove Data Sources:'), "\n";
   print radio_group(-name => 'action_type',
		     '-values' => ['selected', 'all'],
		     -default => 'selected'), br(), "\n";

   CGI::delete('add_chr');
   my($ord, $chr);
   for ($ord = 0; ($chr = $chr[$ord]) && defined($DS{$chr}); $ord++) {}
   $chr = $chr[$ord];
   print hidden(-name => 'add_chr', -value => $chr), "\n";

   CGI::delete('DS');
   my @DS = ();
   grep(push(@DS, join(':', $_,
                       $DS{$_}{database},
                       $files{$DS{$_}{database}},
                       $DS{$_}{cf},
                       $DS{$_}{name},
                       $DS{$_}{rpn},
                       $DS{$_}{type},
                       $DS{$_}{color})), sort keys(%DS));
   print hidden(-name => 'DS', -value => \@DS), "\n";
   print submit(-name => 'add_cdef', -value => "Add Data Source \"$chr\" as RPN Expression:"), "\n";
   print textfield(-name => 'add_rpn', -default => '0'), br(), "\n";
   if (0) {
   print radio_group(-name => 'add_cdef_type',
		     '-values' => ['Binomial Expression', 'RPN Expression'],
		     -default => 'Binomial Expression'), br(), "\n";
   }
   }

   print("</TD>\n");

   print("</TR>\n");

   print("<TR>\n");
   print("<TD><CENTER>\n");
   print radio_group(-name => 'CF',
		     '-values' => ['AVERAGE', 'MIN', 'MAX', 'LAST'],
		     -default => 'AVERAGE'), br(), "\n";
   print 'Data Source Filter RegExp', textfield(-name => 'source_regexp');
   print("</CENTER></TD>\n");
   print("<TD></TD>\n");
   print("<TD><CENTER>\n");

   if (%DS) {
      print submit(-name => 'command', -value => 'Graph Data Sources'), "\n";
      print submit(-name => 'graph',
		   -value => "Graph Data Sources to $IMGFORMAT"), "\n";
   }

   print("</CENTER></TD>\n");
   print("</TR>\n");

   print <<_EOF_
<TR>
<TH><hr></TH>
<TH></TH>
<TH><hr></TH>
</TR>
</TABLE>
_EOF_
   ;

   if ($fetch or %DS) {
      print <<_EOF_
<center><b>Options</b></center><br>
<CENTER>
<TABLE>
_EOF_
   ;
   }
   if (%DS) {
      print '<TR><TH ALIGN=right><a href="',
	    url(),
	    '?rrdgraph=1#item__t_title">Title</a>:</TH><TD>',
	    textfield(-name => 'title'),
	    "</TD></TR>\n";
      print '<TR><TH ALIGN=right><a href="',
	    url(),
	    '?rrdgraph=1#item__v_vertical_label">Vertical Label</a>:</TH><TD>',
	    textfield(-name => 'vertical-label', -default => ''),
	    "</TD><TR>\n";
   }
   if ($fetch or %DS) {
      print '<TR><TH ALIGN=right><a href="',
	    url(),
	    '?rrdgraph=1#item__s_start">Start Time</a>:</TH><TD>',
	    textfield(-name => 'start'),
	    "</TD></TR>\n";
      print '<TR><TH ALIGN=right><a href="',
            url(),
	    '?rrdgraph=1#item__e_end">End Time</a>:</TH><TD>',
	    textfield(-name => 'end'),
	    "</TD></TR>\n";
      if (@event_files) {
	 foreach my $file (@event_files) {
	    open(FILE, "<$file") || die "open: \"$file\": $!\n";
            while (<FILE>) {
               @F = split;
               my $date = shift(@F);
               my $time = shift(@F);
               if ("$date $time" !~
                   m|^(\d\d\d\d)/(\d\d)/(\d\d) (\d\d):?(\d\d)$|) {
                  warn "bad date/time: \"$date $time\"! (skipping)\n";
                  next
               }
            
               my $whence = mktime(0,$5,$4,$3,$2-1,$1-1900,0,0,-1);
               my $val = "$date $time @F";
               push(@events, "$whence $val");
               $events{"$whence $val"} = $val;
            }
	    close(FILE);
	    # FIXME - sort @events by time_t
	 }
         print '<TR><TH ALIGN=right>Event:</TH><TD>',
	       scrolling_list('-name' => 'event',
			      '-values' => \@events,
			      '-default' => [],
			      '-size' => 5,
			      '-height' => '100%',
			      '-width' => '100%',
			      '-labels' => \%events),
               "</TD></TR>\n";
      }
   }
   if (%DS) {
      print '<TR><TH ALIGN=right><a href="',
            url(),
            '?rrdgraph=1#item__w_width">Width</a>:</TH><TD>',
            textfield(-name => 'width'),
            "</TD></TR>\n";
      print '<TR><TH ALIGN=right><a href="',
            url(),
            '?rrdgraph=1#item__h_height">Height</a>:</TH><TD>',
            textfield(-name => 'height'),
            "</TD></TR>\n";

      print "<TR><TH ALIGN=right>",
	    checkbox(-name => 'statistics',
		     -label => ' Show statistics using this format:'),
	    "</TH><TD>";
      print textfield(-name => 'statfmt', -default => '%.0lf'),
	    "</TD></TR>\n";
   }
   if ($fetch or %DS) {
      print <<_EOF_
</TABLE>
</CENTER>
_EOF_
      ;
      print br(), "<hr>\n";
   }

   print endform, "\n";
   goto trailer_label
}

trailer_label:

if (!param('graph')) {
   my $url = url();
   print <<_EOF_
<center><b>Help</b></center><br>
<table width=100%>
_EOF_
   ;
   print("<td width=20%>\n",
	 "<a href=\"${url}?rrdgraph=1\"><kbd>rrdgraph</kbd></a>\n",
	 "</td>\n")
      if (-r "${docdir}/rrdgraph.pod");
   print("<td width=20%>\n",
	 "<a href=\"${url}?rrdfetch=1\"><kbd>rrdfetch</kbd></a>\n",
	 "</td>\n")
      if (-r "${docdir}/rrdfetch.pod");
   print("<td width=20%>\n",
         "<a href=\"${url}?cdeftutorial=1\"><kbd>cdeftutorial</kbd></a>\n",
	 "</td>\n")
      if (-r "${docdir}/cdeftutorial.pod");
   print("<td width=20% align=right>\n",
         "<a href=\"${url}?rpntutorial=1\"><kbd>rpntutorial</kbd></a>\n",
         "</td>\n")
      if (-r "${docdir}/rpntutorial.pod");
   print <<_EOF_
<td width=20% align=right>
<a href="http://net.doit.wisc.edu/~plonka/RRGrapher/">RRGrapher</a>
</td>
</table>
_EOF_
}

# This subrotine is used to perform numeric sorting of items that can contain
# both numeric and non-numeric characters.
# It sorts by collating sequence except that sequences of digits are evaluated
# to determine their numerical value and that compared to either the character
# or sequence of digits in the corresponding position of the other string.
# E.g. it will sort "A2" before "A10" as determined by first comparing
# "A" to "A" then by comparing 2 to 10.
sub by_number_kludge {
   my ($stra, $strb, @a, @b, $val) = ($a, $b);
   @a = $stra =~ m/(\d+|\D+)/g;
   @b = $strb =~ m/(\d+|\D+)/g;

   while (1) {
      if ($a[0] =~ m/^\d+$/ && $b[0] =~ m/^\d+$/ &&
	  ($val = ($a[0] <=> $b[0]))) {
         return $val
      } elsif ($val = ($a[0] cmp $b[0])) {
         return $val
      }
      shift @a;
      shift @b
   }

   return 0
}

# Massage labels using the Bertelson Algorithm
sub munglabels {
   my (@files) = @_;
   my (%files, $label);
   my ($lcp);

   $lcp = lcp(@files);
   foreach my $file (@files) {
      my $label = $file;
      $label =~ s|^$lcp||;
      $label =~ s|\.rrd$||;
      $files{$file} = $label
   }

   return %files;
}

# Find the longest common prefix to a list of strings
# There must be a better way to do this!
sub lcp {
   my (@list) = @_;
   my ($lcp, $newlcp, $i);

   $lcp = shift(@list);
   foreach $_ (@list) {
      $newlcp = "";
      for ($i = 0; ; $i++) {
	 if (substr($lcp, $i, 1) eq substr($_, $i, 1)) {
	    $newlcp .= substr($lcp, $i, 1);
	 } else {
	    last;
	 }
      }
      $lcp = $newlcp;
   }
   return $lcp;
}

# Massage labels using the Plonka Algorithm
sub munglabels2 {
   my (@files) = @_;
   my (%files, %label, @components, $label, $otherlabel);

# %label = (
#	    "foo"	-> [ "/path/to/foo", "path", "to" ],
#	    "bar"	-> [ "/path/to/bar", "path", "to" ],
#	    "to/baz"	-> [ "/path/to/baz", "path" ],
#	    "from/baz"	-> [ "/path/from/baz", "path" ],
#	    );

   foreach my $file (@files) {
      (@components) = split(/\//, $file);
      $label = pop(@components);
      if (exists($label{$label})) {
	 $otherlabel = $label;
	 # Loop until the existing and current entries differ
	 while ($label eq $otherlabel) {
	    # Add a directory component to the existing entry
	    $otherlabel = pop(@{$label{$label}}) . "/$otherlabel";
	    # Change the existing entry's key
	    $label{$otherlabel} = $label{$label};
	    delete($label{$label});
	    # Add a directory component to the current entry
	    $label = pop(@components) . "/$label";
	 }
      }
      # Label is unique, any previously matching label has been adjusted
      # Save the data
      $label{$label} = [ $file, @components ];
   }

   foreach my $label (keys %label) {
      ($files{$label{$label}->[0]} = $label) =~ s|\.rrd$||;
   }

   return %files;
}

sub printlogo {
   print unpack("u", <<'_EOF_');
M1TE&.#EA(@*I .,      .[Z___6 '\P /___P". &!=2%A-+_^>$       
M                     "'Y! $   0 +      B JD   3^D,A)J[TXZ\V[
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
H*$$2Z_JN]DH#]>H*\GJO[IJO_/JOZ."O #NPX+"O!'NP"/L2$0  .XH5
_EOF_
}

exit
