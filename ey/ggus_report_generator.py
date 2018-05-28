#!/usr/bin/env python

from __future__ import print_function

import argparse
import requests
import xml.parsers.expat

from xml.dom import minidom

__version__ = 20141002

# Change it if you want to use it for your NGI without specifing
# it in the command-line
SUPPORT_UNIT = "NGI_NL"

message_header = """
### Open GGUS tickets ###
There are %(ticket count)s open tickets under %(support_unit)s scope.
"""

class GGUSReportException(Exception):
    pass


class GGUSTicket(object):
    support_unit_tag = "SUPPORT UNIT"
    site_tag = "SITE"

    body_template = """%(title)s: %(affected_site)s
      GGUS ID     : %(request_id)s
      Open since  : %(date_of_creation)s UTC
      Status      : %(status)s
      Description : %(subject)s
      Link        : https://ggus.eu/ws/ticket_info.php?ticket=%(request_id)s"""

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
        return self._get_by_xml_tag("affected_site")

    @property
    def date_of_creation(self):
        return self._get_by_xml_tag("date_of_creation")

    @property
    def status(self):
        return self._get_by_xml_tag("status")

    @property
    def subject(self):
        return self._get_by_xml_tag("subject")

    @property
    def request_id(self):
        return self._get_by_xml_tag("request_id")

    def render(self):
        d = {
            "request_id": self.request_id,
            "date_of_creation": self.date_of_creation,
            "status": self.status,
            "subject": self.subject
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
           "&specattrib=none&status=open&priority=&typeofproblem=all"
           "&ticket_category=all&mouarea=&date_type=creation+date"
           "&tf_radio=1&timeframe=any&from_date=&to_date=&untouched_date="
           "&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%%21"
           "&writeFormat=XML")

    def __init__(self, user, password, support_unit):
        self.session = None
        self.user = user
        self.password = password
        self.support_unit = support_unit
        self.url = self.url % {"support_unit": support_unit}

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

    ggus = GGUSConnection(args.username,
                          args.password,
                          args.support_unit)

    tickets = ggus.tickets()

    if args.reverse:
        tickets.reverse()

    print (message_header % {"support_unit": args.support_unit,
                             "ticket count": len(tickets)})

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
