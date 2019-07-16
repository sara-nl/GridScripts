#!/usr/bin/env python

# Get the latest version from the following URL:
#     https://github.com/alvarolopez/ggus_report_generator
# AUTHOR: Alvaro Lopez <aloga@ifca.unican.es>

from __future__ import print_function

import argparse
import requests
import xml.parsers.expat

from xml.dom import minidom

__version__ = 20141002

# Change it if you want to use it for your NGI without specifing
# it in the command-line
SUPPORT_UNIT = "NGI_NL"
SITE = "SARA-MATRIX"

#message_header = """
### Status GGUS tickets ###
#There are %(ticket count)s open tickets under %(support_unit)s scope. Please
#find below a short summary of them. Please take the appropriate actions:
#    - Change the ticket status from "ASSIGNED" to "IN PROGRESS".
#    - Provide feedback on the issue as regularly as possible.
#    - In case of problems, ask for help in <ibergrid-ops@listas.cesga.es>
#    - For long pending issues, put your site/node in downtime.
#    - Do not forget to close the ticket when you have solved the problem.
#"""

message_header = """
### GGUS tickets for %(site_title)s ###
There are %(ticket count)s tickets %(text)s for %(site)s.
"""

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
           "&keyword=&involvedsupporter=&assignedto=&affectedsite=%(site)s"
           "&specattrib=none&status=%(status)s&priority=&typeofproblem=all"
           "&ticket_category=all&mouarea=&date_type=creation+date"
           "&tf_radio=1&timeframe=%(timeframe)s&from_date=&to_date=&untouched_date="
           "&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%%21"
           "&writeFormat=XML")
#https://ggus.eu/?mode=ticket_search&show_columns_check%5B%5D=TICKET_TYPE&show_columns_check%5B%5D=AFFECTED_VO&show_columns_check%5B%5D=AFFECTED_SITE&show_columns_check%5B%5D=PRIORITY&show_columns_check%5B%5D=RESPONSIBLE_UNIT&show_columns_check%5B%5D=STATUS&show_columns_check%5B%5D=DATE_OF_CHANGE&show_columns_check%5B%5D=SHORT_DESCRIPTION&show_columns_check%5B%5D=SCOPE&ticket_id=&supportunit=&su_hierarchy=0&former_su=&vo=&user=&keyword=&involvedsupporter=&assignedto=&affectedsite=SARA-MATRIX&specattrib=none&status=terminal&priority=&typeofproblem=all&ticket_category=all&mouarea=&date_type=closing+date&tf_radio=1&timeframe=lastmonth&from_date=28+May+2018&to_date=29+May+2018&untouched_date=&scope=&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%21

    def __init__(self, user, password, support_unit, site, status):
        self.session = None
        self.user = user
        self.password = password
        self.support_unit = support_unit

        if status=='open':
            timeframe='any'
        else:
            timeframe='lastmonth'

        self.url = self.url % {"support_unit": support_unit, "site": site, "status": status, "timeframe": timeframe}

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
    global SITE
    parser = argparse.ArgumentParser(description='TBD.')
    parser.add_argument('username',
                        metavar='USERNAME',
                        type=str,
                        help='GGUS username.')

    parser.add_argument('password',
                        metavar='PASSWORD',
                        type=str,
                        help='GGUS user password.')

    parser.add_argument('status',
                        metavar='STATUS',
                        type=str,
                        help='State of tickets.')

    parser.add_argument('-s', '--support-unit',
                        dest='support_unit',
                        metavar='SUPPORT_UNIT',
                        default=SUPPORT_UNIT,
                        help=('Only tickets belonging to this support unit '
                              'will be collected'))

    parser.add_argument('-l', '--site',
                        dest='site',
                        metavar='SITE',
                        default=SITE,
                        help=('Only tickets belonging to this site '
                              'will be collected'))

    parser.add_argument('-r', '--reverse',
                        dest='reverse',
                        default=False,
                        action='store_true',
                        help='Sort tickets in reverse chronological order.')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.status!='open':
        args.status='terminal'

    ggus = GGUSConnection(args.username,
                          args.password,
                          args.support_unit,
                          args.site,
                          args.status)

    tickets = ggus.tickets()

    if args.reverse:
        tickets.reverse()

    if args.status=='open':
        text='still open'
    else:
        text='set to closed last month'

    print (message_header % {"site_title": args.site, "ticket count": len(tickets), "text": text, "site": args.site})

    separator = "-" * 80
    su_tickets = []
    for ticket in tickets:
        if not ticket.affected_site:
            su_tickets.append(ticket)
            continue
        print(separator, ticket.render(), sep='\n')

    for ticket in su_tickets:
        print(separator, ticket.render(), sep='\n')

    print("-" * 80)

if __name__ == "__main__":
    main()
