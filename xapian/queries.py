# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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

  from itools.xapian import PhraseQuery, AndQuery
  s1 = PhraseQuery('format', 'Actu')
  s2 = PhraseQuery('archive', True)
  s3 = PhraseQuery('workflow_state', 'public')
  query = AndQuery(s1, s2, s3)
"""



class BaseQuery(object):

    def __repr__(self):
        return "<%s.%s(%s)>" % (
            self.__module__,
            self.__class__.__name__,
            self.__repr_parameters__())



class AllQuery(BaseQuery):

    def search(self, catalog):
        return catalog.search()


    def __repr_parameters__(self):
        return ''



class RangeQuery(BaseQuery):

    def __init__(self, name, left, right):
        self.name = name
        self.left = left
        self.right = right


    def search(self, catalog):
        index = catalog.get_index(self.name)
        if index is None:
            return {}

        return index.search_range(self.left, self.right)


    def __repr_parameters__(self):
        return "%r, %r, %r" % (self.name, self.left, self.right)



class PhraseQuery(BaseQuery):

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


    def __repr_parameters__(self):
        return "%r, %r" % (self.name, self.value)


############################################################################
# Boolean or complex searches
############################################################################
class AndQuery(BaseQuery):

    def __init__(self, *args):
        self.atoms = [ x for x in args if not isinstance(x, AllQuery) ]
        if len(self.atoms) == 0 and len(args) > 0:
            self.atoms = [AllQuery()]


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


    def __repr_parameters__(self):
        return ', '.join([ repr(x) for x in self.atoms ])



class OrQuery(BaseQuery):

    def __init__(self, *args):
        for x in args:
            if isinstance(x, AllQuery):
                self.atoms = [x]
                break
        else:
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


    def __repr_parameters__(self):
        return ', '.join([ repr(x) for x in self.atoms ])



class NotQuery(BaseQuery):

    def __init__(self, query):
        self.query = query


    def search(self, catalog):
        all_documents = catalog.search()
        not_documents = self.query.search(catalog)
        sub_results = {}

        for d in all_documents:
            if (d.__number__ in not_documents) is False:
                sub_results[d.__number__] = 1

        return sub_results


    def __repr_parameters__(self):
        return repr(self.query)



class StartQuery(BaseQuery):

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def search(self, catalog):
        # TODO To be implemented for itools.csv and others
        raise NotImplementedError


    def __repr_parameters__(self):
        return "%r, %r" % (self.name, self.value)
