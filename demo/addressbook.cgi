#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from itools
from itools import get_abspath
from itools.handlers import get_handler

class Address(object):
    def __init__(self, lastname, firstname, telephone):
        self.lastname = lastname
        self.firstname = firstname
        self.telephone = telephone


class Addressbook(object):
    def __init__(self):
        self.addressbook = []

    def add_address(self, lastname, firstname, telephone):
        address = Address(lastname, firstname, telephone)
        self.addressbook.append(address)

    def view(self):
        # Load the STL template
        path = get_abspath(globals(), 'addressbook.xml')
        template = get_handler(path)

        # Build the namespace
        namespace = {'addressbook': self.addressbook}

        # Process the template and return the output
        return template.stl(namespace)


if __name__ == '__main__':
    # Create the addressbook
    addressbook = Addressbook()
    addressbook.add_address('Jordan', 'Robert', '0606060606')
    addressbook.add_address('Buendia', 'Aureliano', '0612345678')

    # Output the HTTP headers
    print "Content-Type: text/html"
    print

    # Output the addressbook content
    print addressbook.view()
