# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Piotr Macuk <piotr@macuk.pl>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.csv import CSV
from itools.resources import get_resource
from itools.datatypes import Integer, Unicode, Date


class MyClients:

    # clients.csv columns definition
    columns = ['client_id', 'surname', 'name', 'address', 'email', 
               'last_pay_date', 'num_of_computers', 'register_date', 
               'discount']

    # clients.csv schema (columns and its types)
    # the indexed columns: client_id, surname, email, last_pay_date
    schema = {'client_id': Integer(index=True), 'surname': Unicode(index=True), 
              'name': Unicode, 'address': Unicode, 'email': Unicode(index=True), 
              'last_pay_date': Date(index=True), 'num_of_computers': Integer, 
              'register_date': Date, 'discount': Integer}


    def __init__(self, file_name):
        self.resource = get_resource(file_name)
        self.clients = CSV()
        self.clients.columns = self.columns
        self.clients.schema = self.schema
        self.clients.load_state(self.resource)


    # Get data for client_id
    def get(self, client_id):
        indexes = self.clients.search(client_id=client_id)
        # Shoult be only one client with ID = client_id
        return self.clients.get_row(indexes[0])


    # Add a new client
    # client -- the list of new row's data
    def add(self, client):
        # Decode dates entered as strings into the Date objects
        p_index = self.columns.index('last_pay_date')
        r_index = self.columns.index('register_date')
        client[p_index] = Date.decode(client[p_index])
        client[r_index] = Date.decode(client[r_index])
        self.clients.add_row(client)


    # Delete client with client_id 
    def delete(self, client_id):
        indexes = self.clients.search(client_id=client_id)
        # Shoult be only one client with ID = client_id
        self.clients.del_row(indexes[0])


    # Change client's data
    # client_id - ID
    # client -- the list of new row's data
    def modify(self, client_id, client):
        self.delete(client_id)
        self.add(client)


    # Get data to send payment email reminders for date (default today)
    def reminders(self, date=None):
        indexes = self.clients.search(last_pay_date=Date.decode(date))
        reminders = self.clients.get_rows(indexes)
        reminders_with_price = []
        for r in reminders:
            reminders_with_price.append(r + [self.get_price()])
        return reminders_with_price
        

    # Calculate price according to:
    # -- number of years using the network
    # -- number of computers connected
    # -- current discount rate
    def get_price(self, register_date=None, num_of_computers=None, discount=None):
        # TODO should return the calculated price
        return 100

    # Save changes to the resource csv file
    def save(self):
        self.clients.save_state()
