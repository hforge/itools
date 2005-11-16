#!/usr/bin/env python

import itools.csv
from itools.resources import get_resource

resource = get_resource('clients.csv')
clients = itools.csv.CSV(resource)

print clients.get_row(0)
# [u'1', u'Piotr', u'Macuk', u'Starowiejska 25/2 81-465 Gdynia',
# u'piotr@macuk.pl', u'2004-11-30', u'2', u'2001-01-05', u'35']

clients.add_row([4, 'Hanna', 'Nowak', 'Dlugi Targ 32 80-112 Gdansk',
'hanka@onet.pl', '2005-11-12', 1, '2005-11-12', 0])

clients.del_row(2)

from itools.datatypes import *
columns = ['client_id', 'surname', 'name', 'address', 'email',
           'last_pay_date', 'num_of_computers', 'register_date',
           'discount']
schema = {'client_id': Integer(index=True), 'surname': Unicode(index=True),
          'name': Unicode, 'address': Unicode, 'email': Unicode(index=True),
          'last_pay_date': Date(index=True), 'num_of_computers': Integer,
          'register_date': Date, 'discount': Integer}
clients.columns = columns
clients.schema = schema
clients.load_state(resource)

print clients.get_row(0)
# [1, u'Piotr', u'Macuk', u'Starowiejska 25/2 81-465 Gdynia',
# u'piotr@macuk.pl', datetime.date(2004, 11, 30), 2, datetime.date(2001, 1, 5), 35] 

indexes = clients.search([('client_id', 1)])
print clients.get_row(indexes[0])

indexes = clients.search([('last_pay_date', Date.decode('2004-11-30'))])
print clients.get_rows(indexes)
