#!/bin/bash
set -e

/usr/sbin/fetch-crl -q 1>/dev/null 2>&1 </dev/null &

/bin/bash
