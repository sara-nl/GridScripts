#!/usr/bin/env python

import lsc
import os,sys,string,hashlib

vomsdir='/etc/grid-security/vomsdir'

try:
    vos=os.listdir(vomsdir)
except:
    e=sys.exc_info()[1]
    sys.stderr.write(str(e)+'\n')
    sys.exit(1)

for vo in vos:
    r=lsc.get_lsc_info(vo)
    if r==None or r=={}: continue

    voms_servers=r.keys()
    for voms_server in voms_servers:
        lsc_path=vomsdir+'/'+vo+'/'+voms_server.encode('ascii')
        if os.path.isfile(lsc_path):

            f=open(lsc_path,'r')
            textlist=map(string.strip,f.readlines())
            f.close()
            
            text=''.join(textlist)
            hash_file=hashlib.sha256(text).hexdigest()

            textlist=[ r[voms_server]['DN'], r[voms_server]['CA_DN'] ]
            text=''.join(textlist)
            hash_portal=hashlib.sha256(text).hexdigest()

            if hash_portal!=hash_file:
                
                print ('discrepancy')
                print (vo)
                print (lsc_path)
                print (r[voms_server]['DN'])
                print (r[voms_server]['CA_DN'])
                print ('\n')

        else:

            print ('missing')
            print (vo)
            print (lsc_path)
            print (r[voms_server]['DN'])
            print (r[voms_server]['CA_DN'])
            print ('\n')
