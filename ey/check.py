#!/usr/bin/env python

import time
import datetime
import os
import sys
import getopt
import unicodedata

import smtplib, os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

import mysql.connector
from psql import psqlCommand

alert="*****DISCREPANCIES DETECTED!!!!!!!!*****"

mail_text="""

Hi Gridders,

Here is the comparison of SURFsara PWC and the NIKHEF database for %s for the number of jobs that have run.

%s

Cheers,

Ernst and Young
"""

sender=''
to=['']

db=''
dbuser=''
dbhost=''
dbpasswd='koeterwaals'

def get_lastmonth():
    today=datetime.date.today()
    first=datetime.date(day=1,month=today.month,year=today.year)
    lastdayoflastmonth=first-datetime.timedelta(days=1)
    last_month=lastdayoflastmonth.strftime('%B')
    last_year=lastdayoflastmonth.strftime('%Y')
    last_month_n=lastdayoflastmonth.strftime('%-m')

    return last_month,last_year,last_month_n

def send_mail(send_from, send_to, subject, text, files=[], server="localhost"):
    assert isinstance(send_to, list)
    assert isinstance(files, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

def main():

    data=get_lastmonth()
    last_month_text=data[0]
    last_year=data[1]
    last_month_num=data[2]
    conn=mysql.connector.Connect(host=dbhost,user=dbuser,password=dbpasswd,database=db)
    c=conn.cursor()

# SiteID for SARA-MATRIX
    siteid=14

    s='select VOid,count(*) from JobRecords where SiteID=%s and EndMonth=%s and EndYear=%s group by VOid;'%(siteid,last_month_num,last_year)

    c.execute(s)
    olist=[]
    for o in c:
        olist.append(o)

    ndict={}
    for o in olist:
        VOid=o[0]
        s='select VOs.name from VOs where VOs.id='+str(VOid)+';'

        c.execute(s)
        m=c.fetchone()

        ascii_voname=unicodedata.normalize('NFKD', m[0]).encode('ascii','ignore')
        ndict.update({ascii_voname:o[1]})

    s='select vo,count(*) from jobs where end_year='+last_year+' and end_month='+last_month_num+' group by vo;'
    result=psqlCommand('account',s)

    sdict={}
    for r in result:
        sdict.update({r[0]:r[1]})

    VOs=sdict.keys()
    strng="VO".ljust(24," ")+"SURFsara".ljust(14," ")+"NIKHEF".ljust(14," ")+ "\n\n"
    for vo in VOs:
        if vo not in ndict.keys(): continue
        strng=strng+vo.ljust(24," ")+str(sdict[vo]).ljust(14," ")+str(ndict[vo]).ljust(14," ")+"\n"

    ssm=sum(sdict.values())
    nsm=sum(ndict.values())

    pitd=last_month_text+ " "+str(last_year)
    subject='Look at the differences '+pitd

    if nsm==0:
        subject="No SURFsara accounting data in NIKHEF db!!!"

    if ssm==0:
        subject="No accounting data in SURFSARA db!!!"

    if ssm==0 and nsm==0:
        subject="No accounting data in SURFSARA and NIKHEF db!!!"


    if nsm>0 and abs(ssm-nsm)*100.0/nsm >4.0:
        strng=strng+"\n"+alert+"\n"

    sk=sdict.keys()
    nk=ndict.keys()
    for key in sk:
        if key not in nk:
            strng=strng+"VO "+key+" in SURFsara database but not at NIKHEF\n"
    for key in nk:
        if key not in sk:
            strng=strng+"VO "+key+" in NIKHEF database but not at SURFsara\n"

    send_mail(sender,to,subject,mail_text%(pitd,strng),[])

if __name__ == '__main__':

    main()
