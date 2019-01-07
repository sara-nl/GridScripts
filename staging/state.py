#!/usr/bin/env python

# Authors: 
#    Written by Ron Trompert.
#    Some small modifications by Onno Zweers, inspired by Cern scripts https://gitlab.cern.ch/dmc/gfal2-bindings/tree/develop/example/python.
#    Modifictions to accept any SURL by Natalie Danezi.
# Support: 
#    Contact <helpdesk@surfsara.nl> 	

import gfal2
import errno
import sys
import time
import argparse
import textwrap

parser=argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\

        This script will display the status of each file listed
        in the file specified with '--file'. The paths should be
        listed with the following format:
        srm://...

        Usage:
	$ python state.py --file [srmlist]
        Script output:
        ONLINE: means that the file is only on disk
        NEARLINE: means that the file in only on tape
        ONLINE_AND_NEARLINE: means that the file in on disk and tape

        If --token is specified, usage:
	$ python state.py --file [srmlist] --token [token_id] 
        The [token_id] is the unique identifier printed by stage.py 
        for a certain [srmlist].
        Script output:
        QUEUED: the file is being fetched from tape (PINNING)
        FAILED: could not get the file from tape
        READY: file is online (PINNED)
        
        To summarize the output, use the script like this:
        python state.py --file myfiles | awk '{print $2}' | sort | uniq --count
        '''))

parser.add_argument('--file', action="store", dest="file", required=True,
    help='File containing file names to be staged starting with: srm://...')

parser.add_argument('--token', action="store", dest="token", required=False,
    help='Stage request token printed by stage.py. Optional. It is faster for large srmlists.')

args=parser.parse_args()

surls=[]
f=open(args.file,'r')
surls=f.read().splitlines()
f.close()

context = gfal2.creat_context()

if args.token is None:

    # Method 1: get status for each file.

    for surl in surls:
        status = context.getxattr(surl, 'user.status')
        print surl, status

else:

    # Method 2: use the request token to ask the SRM what the status of the stage request is.

    def evaluate_errors(errors, surls, polling):
        n_terminal = 0
        for surl, error in zip(surls, errors):
            if error:
                if error.code != errno.EAGAIN:
                    print "%s FAILED : %s" % (surl, error.message)
                    n_terminal += 1
                else:
                    print "%s QUEUED" % surl
            elif not polling:
                print "%s QUEUED" % surl
            else:
                n_terminal += 1
                print "%s READY" % surl
        return n_terminal

    sleep_time = 1

    errors = context.bring_online_poll(surls, args.token)
    n_terminal = evaluate_errors(errors, surls, polling=True)
