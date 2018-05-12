USE="-java" emerge layman
echo "source /usr/portage/local/layman/make.conf" >> /etc/make.conf
layman -L 
layman -a sunrise