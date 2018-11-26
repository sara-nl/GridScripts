#!/usr/bin/env python

# Written by Ron Trompert.
# Some small modifications by Onno Zweers.

import pythonpath
import gfal2
import sys
import time
import re
from string import strip
import argparse
import textwrap

parser=argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script will stage (bring online) all files listed
        in the file specified with '--file'. The paths should be
        listed with the following format:
        /pnfs/grid.sara.nl/data/...
        '''))

parser.add_argument('--file', action="store", dest="file", required=True,
    help='File containing file names to be staged starting with: /pnfs/grid.sara.nl/...')

args=parser.parse_args()

m=re.compile('/pnfs')

f=open(args.file,'r')
urls=f.readlines()
f.close()

context = gfal2.creat_context()

surls=[]
for u in urls:
    surls.append(m.sub('srm://srm.grid.sara.nl:8443/srm/managerv2?SFN=/pnfs',strip(u)))

try:
    # bring_online(surls, pintime, timeout, async)
    (status, token) = context.bring_online(surls, 604800, 86400, True)
    if token is not None:
        print("Got token %s" % token)
    else:
        print("No token was returned. Are all files online?")
except gfal2.GError as e:
    print("Could not bring the file online:")
    print("\t", e.message)
    print("\t Code", e.code)
    sys.exit(2)
