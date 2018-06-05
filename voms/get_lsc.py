#!/usr/bin/env python

from xml.dom import minidom
import requests,sys

url='http://operations-portal.egi.eu/xml/voIDCard/public/voname/'
HTTPOK=200

def usage():
    sys.stderr.write('get_lsc.py <VO>\n')

def main(vo):

    r=requests.get(url+vo)
    if r.status_code!=HTTPOK:
        sys.stderr.write('Unable to get information for VO: '+vo+'\n')
        sys.exit(1)

    xmldoc = minidom.parseString(r.text)
    voms_servers  = xmldoc.getElementsByTagName('VOMS_Server')

    for voms_server in voms_servers:

        print ('\n')

        hostname  = voms_server.getElementsByTagName('hostname')[0]
        print (hostname.firstChild.nodeValue+'.lsc')

        X509  = voms_server.getElementsByTagName('X509Cert')[0]
        DN=X509.getElementsByTagName('DN')[0]
        CA_DN=X509.getElementsByTagName('CA_DN')[0]
        print (DN.firstChild.nodeValue)
        print (CA_DN.firstChild.nodeValue)
        print ('\n')

if __name__ == '__main__':

    if len(sys.argv)!=2:
        usage()
        sys.exit(1)

    vo=sys.argv[1]

    main(vo)
