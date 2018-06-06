#!/usr/bin/env python

from xml.dom import minidom
import requests,sys

url='http://operations-portal.egi.eu/xml/voIDCard/public/voname/'
HTTPOK=200

def usage():
    sys.stderr.write('lsc.py <VO>\n')

def get_lsc_info(vo):

    try:
        r=requests.get(url+vo)
    except:
        e=sys.exc_info()[1]
        sys.stderr.write(str(e)+'\n')
        sys.exit(1)

    if r.status_code!=HTTPOK:
        sys.stderr.write('Unable to get information for VO: '+vo+'\n')
        sys.exit(1)

    try:
        xmldoc = minidom.parseString(r.text)
    except:
        return None
    voms_servers  = xmldoc.getElementsByTagName('VOMS_Server')

    lscs={}
    for voms_server in voms_servers:

        hostname  = voms_server.getElementsByTagName('hostname')[0]
        lsc_file_name= hostname.firstChild.nodeValue+'.lsc'

        X509  = voms_server.getElementsByTagName('X509Cert')[0]
        DN=X509.getElementsByTagName('DN')[0].firstChild.nodeValue
        CA_DN=X509.getElementsByTagName('CA_DN')[0].firstChild.nodeValue

        lscs.update({lsc_file_name: {'DN':DN, 'CA_DN':CA_DN} })

    return lscs

if __name__ == '__main__':

    if len(sys.argv)!=2:
        usage()
        sys.exit(1)

    vo=sys.argv[1]

    print get_lsc_info(vo)
