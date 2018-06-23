#!/usr/bin/env python
# Snel inelkaar gehackte meuk. RT

import requests,json,datetime,os,re,sys

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
sender='malgorzata@surfsara.nl'
to=['']

temp_url='http://argo.egi.eu/lavoisier/site_ar?month=%(month)s&granularity=daily&report=Critical&site=%(site)s&accept=json'
sites=['SARA-MATRIX']

mail_text="""

Hi folkes ,

Here is the EGI availability and reliability data of %s %s.

%s

Cheers,

Malgorzata
"""

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

def get_lastdayoflastmonth():

    today=datetime.date.today()
    first=datetime.date(day=1,month=today.month,year=today.year)
    lastdayoflastmonth=first-datetime.timedelta(days=1)

    return lastdayoflastmonth

def get_jsonparsed_data(url):

    response = requests.get(url)
    if response.status_code!=200: sys.exit(1)

    data = response.text.decode("utf-8")

    return json.loads(data)

def get_result (site,url):

    AV=0
    REL=0
    UNK=0

    try:
        dict=get_jsonparsed_data(url)
    except:
        sys.exit(1)
    
    dates=dict['entries'][0]['Entity']
    days=len(dates)

    for day in dates:

        AV+=float(day['availability'])
        REL+=float(day['reliability'])
        UNK+=float(day['unknown'])

    
    availability=round(AV/float(days),2)
    reliability=round(REL/float(days),2)

    return {'availability':availability,'reliability':reliability}

if __name__ == '__main__':

    timestruct=get_lastdayoflastmonth()

    month_name=timestruct.strftime('%B')
    month=timestruct.strftime('%Y-%m')
    year=timestruct.strftime('%Y')

# Create the output
    text='%-16s'%'site'+' '+'%-16s'%'availability %'+' '+'%-16s'%'reliability %'+'\n\n'
    for site in sites:

        url=temp_url%{'month':month,'site':site}
        result=get_result(site,url)
        text+='%-16s'%site+' '+'%-16s'%str(result['availability'])+' '+'%-16s'%str(result['reliability'])+'\n'
    text+='\n'

#    print (mail_text%(month_name,year,text))
    send_mail(sender,to,'EGI availability and reliability '+month_name+' '+str(year),mail_text%(month_name,year,text))
