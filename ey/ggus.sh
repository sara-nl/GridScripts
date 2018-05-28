#!/bin/sh

{
echo "my_hdr From: EY <@>"
echo "my_hdr Sender: EY <@>"
} > ~/.muttrc

address=""

tmpfile=`mktemp`

/usr/local/bin/ggus_report_generator.py username password 1>${tmpfile} 2>/dev/null

/usr/bin/mutt -s "Open GGUS tickets overview" $address <${tmpfile}

rm -f ${tmpfile}
