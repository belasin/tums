dnl Process this file with autoconf to produce a configure script.
AC_INIT(mysar, 2.0.12.4, cassiano@polaco.pro.br)
AC_CONFIG_AUX_DIR(config)
AC_CONFIG_SRCDIR(src/mysar.c)
AC_CONFIG_HEADER(src/config.h)

AM_INIT_AUTOMAKE

AC_PROG_CC

AC_CHECK_LIB(z, gzread)

## Determine MySQL library path
# try and find libs without any additional libraries
AC_CHECK_LIB(mysqlclient, mysql_init,
	MYSQL_LIBS=" ",
	MYSQL_LIBS=
)

# hunt through several directories trying to find the libraries
if test "x$MYSQL_LIBS" = "x"; then
	old_LDFLAGS="$LDFLAGS"
	for try in $mysql_lib_dir /usr/lib /usr/lib/mysql /usr/local/lib /usr/local/mysql/lib /usr/local/lib/mysql ; do
		LDFLAGS="$old_LDFLAGS -L$try"
		unset ac_cv_lib_mysqlclient_mysql_init
		AC_CHECK_LIB(mysqlclient, mysql_init,
			MYSQL_LIBS="-L$try",
			MYSQL_LIBS=
		)
		if test "x$MYSQL_LIBS" != "x"; then
			break;
		fi
	done
	LDFLAGS="$old_LDFLAGS $MYSQL_LIBS"
fi

if test "x$MYSQL_LIBS" = "x"; then
	AC_MSG_ERROR([MySQL libraries not found. Check your MySQL installation!])
fi

# check if Mysql support prepared statements
AC_CHECK_LIB(mysqlclient, mysql_stmt_prepare, [], [
        echo "Error! Your MySQL version does not support prepared statements!"
        exit -1
])


# check for headers
AC_HEADER_STDC
AC_HEADER_TIME
AC_CHECK_HEADERS(arpa/inet.h \
		limits.h \
		netdb.h \
		netinet/in.h \
		stdlib.h \
		string.h \
		strings.h \
		sys/socket.h \
		ctype.h \
		signal.h \
		unistd.h
)


## Determine MySQL include path
AC_MSG_CHECKING(for mysql/mysql.h)

# Can we include headers using system include dirs?
AC_TRY_COMPILE([#include <mysql/mysql.h>], [int a = 1;],
	MYSQL_INCLUDE=" ",
	MYSQL_INCLUDE=
)

# hunt through several directories trying to find the includes
if test "x$MYSQL_INCLUDE" = "x"; then
	old_CFLAGS="$CFLAGS"
	for i in $mysql_include_dir /usr/include /usr/local/include /usr/local/mysql/include /usr/local/include/mysql ; do
		CFLAGS="$old_CFLAGS -I$i"
		AC_TRY_COMPILE([#include <mysql/mysql.h>], [int a = 1;],
			MYSQL_INCLUDE="-I$i",
			MYSQL_INCLUDE=
		)
		if test "x$MYSQL_INCLUDE" != "x"; then
			break;
		fi
	done
	CFLAGS="$old_CFLAGS $MYSQL_INCLUDE"
fi

if test "x$MYSQL_INCLUDE" = "x"; then
	AC_MSG_RESULT(no) 
	AC_MSG_ERROR([MySQL headers not found. Check your Mysql Installation!])
fi
AC_MSG_RESULT(yes) 

# check for functions
AC_TYPE_SIGNAL
AC_FUNC_MEMCMP
AC_FUNC_STAT

AC_OUTPUT(Makefile src/Makefile)
