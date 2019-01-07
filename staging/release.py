#!/usr/bin/env python

# Authors:
#    Written by Natalie Danezi, based on state.py/stage.py scripts.
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
        This script will release (UNPIN) all files listed in the 
        file specified with '--file' and the '--token' identifier. 
        The paths should be listed with the following format:
        srm://...

        Usage:
        $ python release.py --file [srmlist] --token [token_id]
        The [token_id] is the unique identifier printed by stage.py
        for a certain [srmlist].
        Script output:
        "UNPINNED" or "FAILED to UNPIN" ==>
        Returns for each file in the [srmlist] whether it was 
        successfully released.
        '''))

parser.add_argument('--file', action="store", dest="file", required=True,
    help='File containing file names already staged starting with: srm://...')

parser.add_argument('--token', action="store", dest="token", required=True,
    help='Stage request token printed by stage.py upon staging.')

args=parser.parse_args()

surls=[]
f=open(args.file,'r')
surls=f.read().splitlines()
f.close()

context = gfal2.creat_context()

try:
    #check if the [token_id] corresponds to the correct [srmlist] brought online, else exit
    for surl in surls:
        context.bring_online_poll(surl, args.token)

    # release(surls, token)
    # Parameters:
    #   surls is the given [srmlist] argument
    #   token is the given [token_id] argument (returned by stage.py)
    errors=context.release(surls, args.token)
    for surl, error in zip(surls, errors):
        if error:
             print "%s => FAILED to UNPIN : %s" % (surl, error.message)
        else:
             print "%s UNPINNED " % surl
except gfal2.GError as e:
    print("Could not release the files:")
    print("\t", e.message)
    print("\t Code", e.code)
    sys.exit(2)
