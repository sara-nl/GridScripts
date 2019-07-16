#!/usr/bin/env python

# Get the latest version from the following URL:
#     https://github.com/alvarolopez/ggus_report_generator
# AUTHOR: Alvaro Lopez <aloga@ifca.unican.es>

from __future__ import print_function

import argparse
import requests
import xml.parsers.expat
import sqlite3
import re

import smtplib, os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

from xml.dom import minidom

__version__ = 20141002

# Change it if you want to use it for your NGI without specifing
# it in the command-line
SUPPORT_UNIT = "NGI_NL"

#message_header = """
### Open GGUS tickets ###
#There are %(ticket count)s open tickets under %(support_unit)s scope. Please
#find below a short summary of them. Please take the appropriate actions:
#    - Change the ticket status from "ASSIGNED" to "IN PROGRESS".
#    - Provide feedback on the issue as regularly as possible.
#    - In case of problems, ask for help in <ibergrid-ops@listas.cesga.es>
#    - For long pending issues, put your site/node in downtime.
#    - Do not forget to close the ticket when you have solved the problem.
#"""

message_header = """
### new GGUS tickets ###
There are %(ticket count)s new GGUS tickets.
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

class GGUSReportException(Exception):
    pass

class GGUSTicket(object):
    support_unit_tag = "SUPPORT UNIT"
    site_tag = "SITE"

    body_template = """%(title)s: %(affected_site)s
      GGUS ID     : %(ticket_id)s
      Last update : %(last_update)s UTC
      Scope       : %(scope)s
      Type        : %(ttype)s
      Status      : %(status)s
      Description : %(subject)s
      VO          : %(vo)s
      Link        : https://ggus.eu/ws/ticket_info.php?ticket=%(ticket_id)s"""

    def __init__(self, ticket, support_unit):
        self.ticket = ticket
        self.support_unit = support_unit

    def _get_by_xml_tag(self, tag):
        aux = self.ticket.getElementsByTagName(tag)
        if aux:
            try:
                return aux[0].firstChild.nodeValue
            except: pass

        return None

    @property
    def affected_site(self):
        return self._get_by_xml_tag("Site")

    @property
    def last_update(self):
        return self._get_by_xml_tag("Last_Update")

    @property
    def status(self):
        return self._get_by_xml_tag("Status")

    @property
    def subject(self):
        return self._get_by_xml_tag("Subject")

    @property
    def ticket_id(self):
        return self._get_by_xml_tag("Ticket-ID")

    @property
    def ttype(self):
        return self._get_by_xml_tag("Type")

    @property
    def scope(self):
        return self._get_by_xml_tag("Scope")

    @property
    def vo(self):
        return self._get_by_xml_tag("VO")

    def render(self):
        d = {
            "ticket_id": self.ticket_id,
            "last_update": self.last_update,
            "status": self.status,
            "subject": self.subject,
            "scope": self.scope,
            "vo": self.vo,
            "ttype": self.ttype
        }

        if self.affected_site:
            d["title"] = self.site_tag
            d["affected_site"] =  self.affected_site
        else:
            d["title"] = self.support_unit_tag
            d["affected_site"] =  self.support_unit

        return self.body_template % d




class GGUSConnection(object):
    url = ("https://ggus.eu/index.php?mode=ticket_search&ticket_id="
           "&supportunit=%(support_unit)s&su_hierarchy=0&vo=all&user="
           "&keyword=&involvedsupporter=&assignedto=&affectedsite="
           "&specattrib=none&status=%(status)s&priority=&typeofproblem=all"
           "&ticket_category=all&mouarea=&date_type=creation+date"
           "&tf_radio=1&timeframe=lastmonth&from_date=&to_date=&untouched_date="
           "&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%%21"
           "&writeFormat=XML")

    def __init__(self, user, password, support_unit, status='open'):
        self.session = None
        self.user = user
        self.password = password
        self.support_unit = support_unit
        self.status = status
        self.url = self.url % {"support_unit": support_unit,"status": status}

    def _get_ggus_session(self):
        s = requests.Session()
        s.verify = False
        data = {"login": self.user, "password": self.password}
        url = "https://ggus.eu/index.php?mode=login"
        s.post(url, data=data)

        self.session = s

    def login(self):
        self._get_ggus_session()
        if not self.session.cookies:
            raise GGUSReportException("Could not authenticate with GGUS")

    def tickets(self):
        if not self.session:
            self.login()

        r = self.session.get(self.url)

        try:
            aux = minidom.parseString(r.content)
        except xml.parsers.expat.ExpatError:
            raise GGUSReportException("Could not parse XML content")

        tickets = aux.getElementsByTagName('ticket')

        return [GGUSTicket(ticket, self.support_unit) for ticket in tickets]


def parse_args():
    global SUPPORT_UNIT
    parser = argparse.ArgumentParser(description='TBD.')
    parser.add_argument('username',
                        metavar='USERNAME',
                        type=str,
                        help='GGUS username.')

    parser.add_argument('password',
                        metavar='PASSWORD',
                        type=str,
                        help='GGUS user password.')

    parser.add_argument('-s', '--support-unit',
                        dest='support_unit',
                        metavar='SUPPORT_UNIT',
                        default=SUPPORT_UNIT,
                        help=('Only tickets belonging to this support unit '
                              'will be collected'))

    parser.add_argument('-r', '--reverse',
                        dest='reverse',
                        default=False,
                        action='store_true',
                        help='Sort tickets in reverse chronological order.')

    return parser.parse_args()


def main():
    args = parse_args()
    conn=sqlite3.connect('ggus.db')
    c=conn.cursor()
    c.execute('''select id from tickets''')
    result=c.fetchall()
    ids=[]
    for r in result:
        ids.append(str(r[0]))

    ggus = GGUSConnection(args.username,
                          args.password,
                          args.support_unit)

    tickets = ggus.tickets()

    if args.reverse:
        tickets.reverse()


    separator = "-" * 80
    our_tickets = []
    for ticket in tickets:
        if ticket.status=='assigned':
#            if not ticket.affected_site:
#                our_tickets.append(ticket)
#                continue
            if ticket.affected_site=='SARA-MATRIX':
                our_tickets.append(ticket)
                continue
        else:
            c.execute("delete from tickets where id==%s" % ticket.ticket_id)
            conn.commit()

    ggus = GGUSConnection(args.username,
                          args.password,
                          args.support_unit,
                          'terminal')

    closed_tickets = ggus.tickets()
    for ticket in closed_tickets:
        c.execute("delete from tickets where id==%s" % ticket.ticket_id)
        conn.commit()


    new_tickets=[]
    
    for ticket in our_tickets:
        if ticket.ticket_id not in ids:
            new_tickets.append(ticket)
            c.execute("insert into tickets (id) values(%s)" % ticket.ticket_id)
    if len(new_tickets)!=0:
        conn.commit()
    conn.close()


    if len(new_tickets)!=0:
        text=message_header % {"ticket count": len(new_tickets)}+'\n\n'+separator

    su_tickets=[]
    for ticket in new_tickets:
        if not ticket.affected_site:
            su_tickets.append(ticket)
            continue
      
        t=ticket.render()
        text=text+'\n'+t+'\n'+separator
      

    for ticket in su_tickets:
        t=ticket.render()
        text=text+'\n'+t+'\n'+separator

    if len(new_tickets)!=0:
        text=text+'\n'+separator

    subject="GRID: New GGUS tickets:"
    for ticket in new_tickets:
        subject=subject+' '+str(ticket.ticket_id)

    if len(new_tickets)!=0:
#        send_mail('ey@surfsara.nl',['helpdesk@surfsara.nl','grid-adm@surfsara.nl'],subject,text)
        send_mail('ey@surfsara.nl',['ron.trompert@surfsara.nl'],subject,text)
if __name__ == "__main__":
    main()
