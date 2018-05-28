#!/bin/sh

{
echo "my_hdr From: EY <>"
echo "my_hdr Sender: EY <>"
} > ~/.muttrc

address=""

tmpfile=`mktemp`

/usr/local/bin/gorilla.py username password -l SARA-MATRIX open 1>${tmpfile} 2>/dev/null
echo >>${tmpfile}
/usr/local/bin/gorilla.py username password -l NIKHEF-ELPROD open 1>>${tmpfile} 2>/dev/null
echo >>${tmpfile}

/usr/bin/mutt -s "Open GGUS tickets overview" $address <${tmpfile}
username
/usr/local/bin/gorilla.py username password -l SARA-MATRIX terminal 1>${tmpfile} 2>/dev/null
echo >>${tmpfile}
/usr/local/bin/gorilla.py username password -l NIKHEF-ELPROD terminal 1>>${tmpfile} 2>/dev/null
echo >>${tmpfile}

/usr/bin/mutt -s "Overview GGUS tickets that were closed last month" $address <${tmpfile}

rm -f ${tmpfile}
