#!/usr/bin/env python
# This script collects the WLCG availability and reliability data every month

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import json,datetime,os,re,sys

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
sender='wlcgwatchdog@surfsara.nl'
to=[]

temp_url='http://wlcg-sam.cern.ch/reports/%s/%s%s/wlcg/WLCG_Tier1_Summary_%s_%s%s.json'
nlt1=['SARA','NIKHEF']
vos=['ATLAS','LHCB','ALICE']

mail_text="""

Hi T1 folkes ,

Here is the WLCG availability and reliability data of %s %s.

%s

Cheers,

Ernst and Young
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

def get_lastdayoflastmonth(ts=None):

    if ts==None:
        today=datetime.date.today()
    else:
        today=ts
    first=datetime.date(day=1,month=today.month,year=today.year)
    lastdayoflastmonth=first-datetime.timedelta(days=1)

    return lastdayoflastmonth

def get_jsonparsed_data(url):

    response = urlopen(url)
    data = response.read().decode("utf-8")

    return json.loads(data)

def get_month_and_year(ts=None):
    
    timestruct=get_lastdayoflastmonth(ts)

    month_abrev_name=timestruct.strftime('%b')
    month_name=timestruct.strftime('%B')
    month_number=timestruct.strftime('%m')
    year=timestruct.strftime('%Y')

    return month_abrev_name,month_name,month_number,year

def get_previous_month_and_year():
    
    ts=get_lastdayoflastmonth()
    return get_month_and_year(ts)

def get_result (site,vo,url):

    CRIT=0
    SCHED=0
    UNKNOWN=0
    OK=0

    try:
        dict=get_jsonparsed_data(url)
    except:
        sys.exit(1)
    
    my_site=re.compile('.*'+site+'.*')
    this_site=None
    for key in dict['T1 Availabilities'].keys():
        if my_site.match(key): this_site=key
    if this_site==None: return None

    sitedict=dict['T1 Availabilities'][this_site]
    dates=sitedict.keys()

    days=len(dates)

    for day in dates:

        CRIT+=sitedict[day]['CRIT']
        UNKNOWN+=sitedict[day]['UNKNOWN']
        OK+=sitedict[day]['OK']
        SCHED+=sitedict[day]['SCHED']

    ntests=CRIT+UNKNOWN+OK+SCHED
    ntests_av=ntests-UNKNOWN
    ntests_re=ntests_av-SCHED
    
    availability=round(OK/float(ntests_av)*100,1)
    reliability=round(OK/float(ntests_re)*100,1)

    return {'availability':availability,'reliability':reliability}

if __name__ == '__main__':

# If there is a new month, then cleanup the old lock file
    month_abrev_name,month_name,month_number,year=get_previous_month_and_year()
    file='/var/lock/subsys/wlcg_av_rel'+month_name+str(year)
    if os.path.isfile(file):
        os.remove(file)
    month_abrev_name,month_name,month_number,year=get_month_and_year()

# Get the previous month over which the reporting is taking place
    a,month_name,b,year=get_month_and_year()
    month_abrev_name,month_name,month_number,year=get_month_and_year()

# Generate new lock file so we only send mail once per month
    file='/var/lock/subsys/wlcg_av_rel'+month_name+str(year)

# Is the lock file already there. We have already sent the email this month.
    if os.path.isfile(file): sys.exit(0)

# Create the output
    text='%-10s'%'vo'+' '+'%-10s'%'site'+' '+'%-16s'%'availability %'+' '+'%-16s'%'reliability %'+'\n\n'
    for vo in vos:
# Generate the url do we have to query at CERN
        VO=vo.upper()
        url=temp_url % (year,year,month_number,VO,month_abrev_name,year)

        for site in nlt1:
            SITE=site.upper()
            result=get_result(SITE,VO,url)
            if result==None: continue
            text+='%-10s'%vo+' '+'%-10s'%site+' '+'%-16s'%str(result['availability'])+' '+'%-16s'%str(result['reliability'])+'\n'
        text+='\n'

#    print (mail_text%(month_name,year,text))
    send_mail(sender,to,'WLCG availability and reliability '+month_name+' '+str(year),mail_text%(month_name,year,text))

# Touch the new lock file
    open(file, 'a').close()
