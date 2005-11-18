# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from Analysers import get_analyser


"""
To build a query:

  from itools.catalog import Query
  s1 = Query.Simple('format', 'Actu')
  s2 = Query.Simple('archive', True)
  c1 = Query.Complex(s1, 'and', s2)
  s3 = Query.Simple('workflow_state', 'public')
  query = Query.Complex(c1, 'and', s3)
"""


class Equal(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def search(self, catalog):
        # A simple query
        fields = catalog.get_handler('fields')
        field_number = fields.state.field_numbers[self.name]
        field = fields.state.fields[field_number]
        if field_number in fields.state.indexed_fields:
            tree = catalog.get_handler('f%d' % field_number)
            documents = tree.search_word(self.value)
            # Calculate the weight
            for doc_number in documents:
                documents[doc_number] = len(documents[doc_number])

        return documents



class Range(object):

    def __init__(self, name, left, right):
        self.name = name
        self.left = left
        self.right = right


    def search(self, catalog):
        fields = catalog.get_handler('fields')
        field_number = fields.state.field_numbers[self.name]
        field = fields.state.fields[field_number]
        if field_number in fields.state.indexed_fields:
            tree = catalog.get_handler('f%d' % field_number)
            return tree.search_range(self.left, self.right)
        return {}



class Phrase(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def search(self, catalog):
        # A simple query
        fields = catalog.get_handler('fields')
        field_number = fields.state.field_numbers[self.name]
        field = fields.state.fields[field_number]
        if field_number in fields.state.indexed_fields:
            tree = catalog.get_handler('f%d' % field_number)
            analyser = get_analyser(field.type)
            documents = {}
            for value, offset in analyser(self.value):
                result = tree.search_word(value)
                if offset == 0:
                    documents = result
                else:
                    aux = {}
                    for doc_number in documents:
                        if doc_number in result:
                            pos = [ x for x in documents[doc_number]
                                    if x + offset in result[doc_number] ]
                            if pos:
                                aux[doc_number] = set(pos)
                    documents = aux
            # Calculate the weight
            for doc_number in documents:
                documents[doc_number] = len(documents[doc_number])

        return documents


############################################################################
# Boolean or complex searches
############################################################################
class And(object):

    def __init__(self, left, right):
        self.left = left
        self.right = right


    def search(self, catalog):
        r1 = self.left.search(catalog)
        r2 = self.right.search(catalog)
        documents = {}
        for number in r1:
            if number in r2:
                documents[number] = r1[number] + r2[number]
        return documents



class Or(object):

    def __init__(self, left, right):
        self.left = left
        self.right = right


    def search(self, catalog):
        r1 = self.left.search(catalog)
        r2 = self.right.search(catalog)
        for number in r2:
            if number in r1:
                r1[number] += r2[number]
            else:
                r1[number] = r2[number]
        return r1
