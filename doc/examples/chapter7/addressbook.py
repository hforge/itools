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
from itools.resources import get_resource
from itools.xml import XML


class Addressbook(XML.Document):
    def _load(self):
        # Load the XML tree
        XML.Document._load(self)
        # Initialize data structure
        self.addresses = []
        # Load addressbook
        addressbook_element = self.get_root_element()
        for address_element in addressbook_element.get_elements():
            # Initialize address record with default values
            address = {'last_name': '',
                       'first_name': '',
                       'telephone': ''}
            # Load values from the XML resource
            for element in address_element.get_elements():
                if element.name == 'lastname':
                    address['last_name'] = unicode(element.children)
                elif element.name == 'firstname':
                    address['first_name'] = unicode(element.children)
                elif element.name == 'telephone':
                    address['telephone'] = unicode(element.children)
            # Add to the list of addresses
            self.addresses.append(address)
        # Clean the unneeded XML tree
        del self.children


    def to_str(self, encoding='UTF-8'):
        # XML declaration
        data = u'<?xml version="1.0" encoding="%s"?>\n' % encoding
        # Open root element
        data += u'<addressbook>\n'
        # Addresses
        for address in self.addresses:
            pattern = u'  <address>\n' \
                      u'    <lastname>%(last_name)s</lastname>\n' \
                      u'    <firstname>%(first_name)s</firstname>\n' \
                      u'    <telephone>%(telephone)s</telephone>\n' \
                      u'  </address>\n'
            data += pattern % address
        # Close root element
        data += u'</addressbook>'
        # Return as a byte string
        return data.encode(encoding)


    def add_address(self, last_name, first_name, telephone):
        address = {'last_name': last_name,
                   'first_name': first_name,
                   'telephone': telephone}
        self.addresses.append(address)


    def view(self):
        # Load the STL template
        resource = get_resource('addressbook.xml')
        template = XML.Document(resource)

        # Build the namespace
        namespace = {'addressbook': self.addresses}

        # Process the template and return the output
        return template.stl(namespace)


if __name__ == '__main__':
    # Load the addressbook
    r = get_resource('addressbook.xml')
    addressbook = Addressbook(r)

    # Output the addressbook content
    print addressbook.view()
