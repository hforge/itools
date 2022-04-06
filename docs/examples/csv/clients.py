# -*- coding: UTF-8 -*-
# Copyright (C) 2008, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
from datetime import date

# Import from itools
from itools.csv import CSVFile
from itools.database import RWDatabase
from itools.datatypes import Integer, Unicode, String, Date


class Clients(CSVFile):

    columns = ['client_id', 'name', 'email', 'registration_date']

    schema = {
        'client_id': Integer,
        'name': Unicode,
        'email': String,
        'registration_date': Date}


if __name__ == '__main__':
    rw_database = RWDatabase(path="docs/examples/csv/", size_min=2048, size_max=4096, backend='lfs')
    clients = rw_database.get_handler("clients.csv", Clients)

    # Access a column by its name
    row = clients.get_row(0)

    # Now 'update_row' expects the values to be of the good type
    clients.update_row(0, registration_date=date(2004, 11, 10))

    # So is for the 'add_row' method
    clients.add_row(
        [250, u'J. David Ibanez', 'jdavid@itaapy.com', date(2007, 1, 1)])

    print(clients.to_str())
