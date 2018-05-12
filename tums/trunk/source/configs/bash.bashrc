# System-wide .bashrc file for interactive bash(1) shells.

# To enable the settings / commands in this file for login shells as well,
# this file has to be sourced in /etc/profile.

# If not running interactively, don't do anything
[ -z "$PS1" ] && return
alias ls="ls --color=auto"

# tv* aliases
alias tv2='tail -f /var/log/l2tpns'
alias tva='tail -f /var/log/squid/access.log'
alias tvc='tail -f /var/log/cron.log'
alias tve='tail -f /var/log/exim4/mainlog'
alias tce='tve'
alias tbe='tve'
alias tvc='tve'
alias tvf='tail -f /var/log/vsftpd.log'
alias tvk='tail -f /var/log/kern.log'
alias tvl='tail -f /var/log/slapd.log'
alias tvm='tail -f /var/log/mail.log'
alias tvp='tail -f /var/log/ppp.log'
alias tvs='tail -f /var/log/syslog'
alias tvt='tail -f /var/log/tums.log'
alias tvu='tail -f /var/log/auth.log'
alias tvv='tail -f /var/log/clamav/clamav.log'
alias tvw='tail -f /var/log/shorewall.log'

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, overwrite the one in /etc/profile)
PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '

# Commented out, don't overwrite xterm -T "title" -n "icontitle" by default.
# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PROMPT_COMMAND='echo -ne "\033]0;${USER}@`hostname -f`:${PWD} from ${SSH_CLIENT%% *} - Vulani\007"'
    ;;
*)
    ;;
esac

if [[ ${EUID} == 0 ]] ; then
    PS1='\[\033[01;31m\]\h\[\033[01;34m\] \W \$\[\033[00m\] '
else
    PS1='\[\033[01;32m\]\u@\h\[\033[01;34m\] \w \$\[\033[00m\] '
fi

# enable bash completion in interactive shells
if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi
