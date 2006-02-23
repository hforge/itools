# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from analysers import get_analyser


"""
To build a query:

  from itools.catalog import queries
  s1 = queries.Equal('format', 'Actu')
  s2 = queries.Equal('archive', True)
  s3 = queries.Equal('workflow_state', 'public')
  query = queries.And(s1, s2, s3)
"""


class Equal(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def search(self, catalog):
        # A simple query
        index = catalog.get_index(self.name)
        documents = index.search_word(self.value)
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
        index = catalog.get_index(self.name)
        documents = index.search_range(self.left, self.right)
        return documents



class Phrase(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def search(self, catalog):
        # Get the index
        index = catalog.get_index(self.name)
        # Get the analyser
        fields = catalog.get_handler('fields')
        field_number = fields.state.field_numbers[self.name]
        field = fields.state.fields[field_number]
        analyser = get_analyser(field.type)

        documents = {}
        for value, offset in analyser(self.value):
            result = index.search_word(value)
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

    def __init__(self, *args):
        self.atoms = args


    def search(self, catalog):
        documents = self.atoms[0].search(catalog)
        for atom in self.atoms[1:]:
            sub_results = atom.search(catalog)
            for id in documents.keys():
                if id in sub_results:
                    documents[id] += sub_results[id]
                else:
                    del documents[id]

        return documents



class Or(object):

    def __init__(self, *args):
        self.atoms = args


    def search(self, catalog):
        documents = self.atoms[0].search(catalog)
        for atom in self.atoms[1:]:
            sub_results = atom.search(catalog)
            for id in sub_results:
                if id in documents:
                    documents[id] += sub_results[id]
                else:
                    documents[id] = sub_results[id]

        return documents
