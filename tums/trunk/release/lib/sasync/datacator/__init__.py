"""
Datacator
=========

Remote data access within the sAsync package: 'SQLAlchemy done Asynchronously'


License
-------

Copyright (C) 2006 by Edwin A. Suominen, http://www.eepatents.com

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the file COPYING for more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 51
Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA


TCP Protocol
------------

Local data stores connected to a remote data manager via a TCP client using a
simple, line-based protocol::

    <session>       ::= <login> <reply-simple> <requests>
                        =====>> <<------------

    <login>         ::= 'login' WS account WS password

    <reply-simple>  ::= 'OK' | 'Fail' | Number_of_result_rows

    <requests>      ::= <request> | <request> <requests>

    <request>       ::= <simple> LB <list>
                      | ======>>    <<----
                      | 
                      | <complex> LB <list> <reply-simple>
                      | =======>>    ====>> <<------------
                        
    <simple>        ::= 'get' WS item WS flavor
                      | 'items'
                      | 'flavors'
                      | 'updates'
                      | 'results' WS row

    <complex>       ::= 'set' WS item WS flavor
                      | 'sql'

    <list>          ::= N LB N*N(element LB)

    -----------------------------------------------------------------------

    ===========>>   Line sent from client
    <<-----------   Reply line sent from server

    Strings with no internal whitespace:
    item            == An item of the data store
    flavor          == A flavor of data store items
    account         == A data-access account
    password        == An account password

    element         == Newline-terminated string defining a list element
                        - 'get'     <- string_element_of_value_list
                        - 'set'     => string_element_of_value_list
                        - 'items'   <- item_name
                        - 'flavors' <- flavor_name
                        - 'updates' <- item flavor
                        - 'sql'     => SQL_query_line
                        - 'results' <- Items_of_query_result_row
    
    N               == Integer defining number of list values to follow
    LB              == line break
    WS              == whitespace

"""
