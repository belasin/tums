echo "Usage: ldap-import.sh filename.ldif"
ldapadd -c -D "cn=Manager,o=BPEXAMPLE" -x -w wsbpexample -f $1
