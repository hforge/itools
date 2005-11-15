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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

from my_clients import MyClients

clients = MyClients('clients.csv')

# Get client with client_id = 1
print 'The client with ID = 1'
print clients.get(1)

# Add a new client
clients.add([4, 'Hanna', 'Nowak', 'Dlugi Targ 32 80-112 Gdansk', 
             'hanka@onet.pl', '2005-11-12', 1, '2005-11-12', 0])
# And gets its data from database
print 'The client with ID = 4'
print clients.get(4)

# Delete client with client_id = 3
clients.delete(3)

# Change the client data (client_id = 4)
clients.modify(4, [4, 'Hanna', 'Nowak-Albowska', 
                   'Dlugi Targ 32 80-112 Gdansk', 'hanka@onet.pl', 
                   '2005-11-12', 1, '2005-11-12', 0])
# And print the changed data
print 'The client with ID = 4 (modified)'
print clients.get(4)

# Get data to send payment reminders
print 'Remainders (2004-11-30)'
print clients.reminders('2004-11-30')

# Save changes to the clients.csv file
# clients.save()
