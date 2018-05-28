#!/usr/bin/env python

import time
import datetime
import os
import commands
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

mail_text="""

Hi Gridders,

Here is the accounting data from the NIKHEF database from %s.

Cheers,

Ernst and Young
"""

sender=''
to=['']

db=''
dbuser=''
dbhost=''
dbpasswd=''

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
    csv_file='/tmp/nikhef.csv'

    s='select id,name from Sites;'
    conn=mysql.connector.Connect(host=dbhost,user=dbuser,password=dbpasswd,database=db)
    c=conn.cursor()

    c.execute(s)
    site_dict={}
    for o in c:
# Hack to skip misconfiguration
        if o[0]==15: continue
        site_dict.update({unicodedata.normalize('NFKD', o[1]).encode('ascii','ignore'):o[0]})

    f=open(csv_file,'w')
    for site in site_dict.keys():

        siteid=site_dict[site]
        s='select VOid,count(*),sum(WallDuration)/3600.0,sum(CpuDuration)/3600.0,sum(WallDuration*NodeCount*Processors)/3600.0 from JobRecords where SiteID=%s and EndMonth=%s and EndYear=%s group by VOid;'%(siteid,last_month_num,last_year)

        c.execute(s)
        olist=[]
        for o in c:
            olist.append(o)

        dict={}
        for o in olist:
            VOid=o[0]
            s='select VOs.name from VOs where VOs.id='+str(VOid)+';'

            c.execute(s)
            m=c.fetchone()

            list=[]
            for l in o[1:]:
                list.append(l)

            dict.update({m[0]:list})


        pitd=last_month_text+ " "+str(last_year)
        f.write(";\n;\n;\n;\n")
        f.write("Accounting data for "+site+" from the Nikhef database for "+pitd+";\n")
        f.write("VO;# of jobs;Wallclock (hours);CPU hours;Wallclock*nodes*cores (hours)\n")
        for k in dict.keys():
            f.write(str(k)+";"+str(dict[k][0])+";"+str(dict[k][1])+";"+str(dict[k][2])+";"+str(dict[k][3])+";\n")
    f.close()

    send_mail(sender,to,'Accounting data for the Dutch Grid infrastructure from the NIKHEF database for '+pitd,mail_text%(pitd),[ csv_file ])

    cmdstring="curl -u some_random_text -T "+csv_file+" https://surfdrive.surf.nl/files/public.php/webdav/Compute/"+str(last_year)+"/"+last_month_text+ "-"+str(last_year)+"_ey_"+os.path.basename(csv_file)
    a=commands.getstatusoutput(cmdstring)

    os.remove(csv_file)

if __name__ == '__main__':

    main()

