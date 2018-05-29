#!/bin/sh

{
echo "my_hdr From: EY <>"
echo "my_hdr Sender: EY <>"
} > ~/.muttrc

datestring=`env LC_TIME=C date --date="15 days ago" '+%B %Y'`
timestring=`env LC_TIME=C date '+%F'`

address=""

tmpfile=`mktemp`

/usr/local/bin/gorilla.py username password -l SARA-MATRIX open 1>${tmpfile} 2>/dev/null
echo >>${tmpfile}
/usr/local/bin/gorilla.py username password -l NIKHEF-ELPROD open 1>>${tmpfile} 2>/dev/null
echo >>${tmpfile}

/usr/bin/mutt -s "Open GGUS tickets overview "$timestring $address <${tmpfile}
username
/usr/local/bin/gorilla.py username password -l SARA-MATRIX terminal 1>${tmpfile} 2>/dev/null
echo >>${tmpfile}
/usr/local/bin/gorilla.py username password -l NIKHEF-ELPROD terminal 1>>${tmpfile} 2>/dev/null
echo >>${tmpfile}

/usr/bin/mutt -s "Overview GGUS tickets that were closed in "$datestring $address <${tmpfile}

rm -f ${tmpfile}
