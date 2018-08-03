#!/usr/bin/env python

import time
import datetime
import os
import commands
import sys
import getopt
import unicodedata
import re

import smtplib, os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

import mysql.connector

mail_text="""

Hi Gridders,

Here is the accounting data from the NIKHEF database from %s.

Cheers,

Ernst and Young
"""

sender='ey@surfsara.nl'
to=['','']
#to=['']

db=''
dbuser=''
dbhost=''
dbpasswd=''

url=""
surfdrivelink=""

uploadfile="curl -s -S -u %s -T %s --head %s"
doesdirectoryexist="curl  -s -S -u %s --head -X PROPFIND %s"
createdirectory="curl  -s -S -u %s --head -X MKCOL %s"
http_code=re.compile('HTTP.*\s+(\d{3})\s*.*\n')

def create_directory(dir):

    r=commands.getoutput(doesdirectoryexist % (surfdrivelink,url+'/'+dir))

    http_status=int(http_code.match(r).group(1))
    if http_status==404:
        r=commands.getoutput(createdirectory % (surfdrivelink,url+'/'+dir))
        http_status=int(http_code.match(r).group(1))
        assert(http_status==201)

    return

def upload_file(dir,src_file,dest_file):

    create_directory(dir)

    r=commands.getoutput(uploadfile % (surfdrivelink,src_file,url+'/'+dir+'/'+dest_file))
    l=http_code.findall(r)
    http_status=int(l[len(l)-1])
    assert(http_status>=200 and http_status<=207)

    return
    
    
    

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

    t=str(time.time())
    csv_file='/tmp/accounting'+t+'.csv'

# SARA-MATRIX=14
# NIKHEF_ELPROD=1
# RUG-CIT=16
    site_dict={'SARA-MATRIX':14,
               'RUG-CIT':16,
               'NIKHEF-ELPROD':1}

    pitd=last_month_text+ " "+str(last_year)
    f=open(csv_file,'w')
    conn=mysql.connector.Connect(host=dbhost,user=dbuser,password=dbpasswd,database=db)
    c=conn.cursor()


    for site in site_dict.keys():

        siteid=site_dict[site]

        s='select VOs.name,VOGroups.name,VORoles.name,count(JobRecords.LocalJobId),sum(JobRecords.WallDuration)/3600.0,sum(JobRecords.CpuDuration)/3600.0,sum(JobRecords.WallDuration*JobRecords.NodeCount*JobRecords.Processors)/3600.0 from JobRecords,VOs,VOGroups,VORoles where JobRecords.SiteID=%s and VOs.id=JobRecords.VOID and VOGroups.id=JobRecords.VOGroupID and VORoles.id=JobRecords.VORoleID and EndMonth=%s and EndYear=%s group by VOs.name,VOGroups.name,VORoles.name;'%(siteid,last_month_num,last_year)


        c.execute(s)

        olist=[]
        for o in c:
            olist.append(o)

        f.write(";\n;\n;\n;\n")
        f.write("Accounting data for "+site+" from the Nikhef database for "+pitd+";\n")
        f.write("VO;VO group;VO role;# of jobs;Wallclock (hours);CPU hours;Wallclock*nodes*cores (hours)\n")

        for o in olist:

            VO=o[0].encode('ascii')
            VOGroup=o[1].encode('ascii')
            VORole=o[2].encode('ascii')
            njobs=str(o[3])
            whours=str(int(round(float(o[4]))))
            CPUhours=str(int(round(float(o[5]))))
            wnchours=str(int(round(float(o[6]))))
            f.write(VO+';'+VOGroup+';'+VORole+';'+njobs+';'+whours+';'+CPUhours+';'+wnchours+';\n')

    f.close()

    send_mail(sender,to,'Accounting data for the Dutch Grid infrastructure from the NIKHEF database for '+pitd,mail_text%(pitd),[ csv_file ])

    
    upload_file(str(last_year),csv_file,last_month_text+ "-"+str(last_year)+"_ey_"+os.path.basename(csv_file))

    os.remove(csv_file)


if __name__ == '__main__':

    main()
