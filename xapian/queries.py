# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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

"""
To build a query:

  from itools.xapian import EqQuery, AndQuery
  s1 = EqQuery('format', 'Actu')
  s2 = EqQuery('archive', True)
  s3 = EqQuery('workflow_state', 'public')
  query = AndQuery(s1, s2, s3)
"""


class EqQuery(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def search(self, catalog):
        index = catalog.get_index(self.name)
        if index is None:
            return {}

        documents = index.search_word(self.value)
        # Calculate the weight
        for doc_number in documents:
            documents[doc_number] = len(documents[doc_number])

        return documents


    def __repr__(self):
        return "<%s.%s(%s=%r)>" % (self.__module__, self.__class__.__name__,
                                   self.name, self.value)



class RangeQuery(object):

    def __init__(self, name, left, right):
        self.name = name
        self.left = left
        self.right = right


    def search(self, catalog):
        index = catalog.get_index(self.name)
        if index is None:
            return {}

        return index.search_range(self.left, self.right)


    def __repr__(self):
        return "<%s.%s(%s=[%r:%r])>" % (self.__module__,
                                        self.__class__.__name__, self.name,
                                        self.left, self.right)



class PhraseQuery(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def search(self, catalog):
        index = catalog.get_index(self.name)
        if index is None:
            return {}

        # Get the analyser
        field = catalog.get_analyser(self.name)

        documents = {}
        for value, offset in field.split(self.value):
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


    def __repr__(self):
        return "<%s.%s(%s=%r)>" % (self.__module__, self.__class__.__name__,
                                   self.name, self.value)


############################################################################
# Boolean or complex searches
############################################################################
class AndQuery(object):

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


    def __repr__(self):
        return "<%s.%s(%s)>" % (self.__module__, self.__class__.__name__,
                                ', '.join([repr(x) for x in self.atoms]))



class OrQuery(object):

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


    def __repr__(self):
        return "<%s.%s(%s)>" % (self.__module__, self.__class__.__name__,
                                ', '.join([repr(x) for x in self.atoms]))



class NotQuery(object):

    def __init__(self, query):
        self.query = query


    def search(self, catalog):
        from itools.catalog import Catalog

        all_documents = catalog.search()
        not_documents = self.query.search(catalog)
        sub_results = {}

        if isinstance(catalog, Catalog):
            for d in all_documents.get_documents():
                if not_documents.has_key(d.__number__) is False:
                    sub_results[d.__number__] = 1
        else:
            for d in all_documents:
                if (d.__number__ in not_documents) is False:
                    sub_results[d.__number__] = 1

        return sub_results
