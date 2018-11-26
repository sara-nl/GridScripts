#!/usr/bin/env python

# Written by Ron Trompert.
# Some small modifications by Onno Zweers, inspired by https://gitlab.cern.ch/dmc/gfal2-bindings/tree/develop/example/python.

import pythonpath
import errno
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
        This script will display the status of each file listed
        in the file specified with '--file'. The paths should be
        listed with the following format:
        /pnfs/grid.sara.nl/data/...

        Script output:
        ONLINE: means that the file is only on disk
        NEARLINE: means that the file in only on tape
        ONLINE_AND_NEARLINE: means that the file in on disk and tape.

        If --token is specified, the output will be:
        QUEUED: the file is being fetched from tape
        FAILED: could not get the file from tape
        READY: file is online.
        '''))

parser.add_argument('--file', action="store", dest="file", required=True,
    help='File containing file names to be staged starting with: /pnfs/grid.sara.nl/...')

parser.add_argument('--token', action="store", dest="token", required=False,
    help='Token printed by stage.py. Optional. If used, might be a bit faster.')

args=parser.parse_args()


m=re.compile('/pnfs')
nf=100

f=open(args.file,'r')
urls=f.readlines()
f.close()

context = gfal2.creat_context()

if args.token is None:

    # Method 1: get status for each file.

    for u in urls:
        surl = m.sub('srm://srm.grid.sara.nl:8443/srm/managerv2?SFN=/pnfs',strip(u))
        status = context.getxattr(surl, 'user.status')
        print surl, status

else:

    # Method 2: use the request token to ask the SRM what the status of the stage request is.

    def evaluate_errors(errors, surls, polling):
        n_terminal = 0
        for surl, error in zip(surls, errors):
            if error:
                if error.code != errno.EAGAIN:
                    print "%s => FAILED: %s" % (surl, error.message)
                    n_terminal += 1
                else:
                    print "%s QUEUED" % surl
            elif not polling:
                print "%s QUEUED" % surl
            else:
               n_terminal += 1
               print "%s READY" % surl
        return n_terminal

    surls=[]
    for u in urls:
        surls.append(m.sub('srm://srm.grid.sara.nl:8443/srm/managerv2?SFN=/pnfs',strip(u)))

    sleep_time = 1

    errors = context.bring_online_poll(surls, args.token)
    n_terminal = evaluate_errors(errors, surls, polling=True)
