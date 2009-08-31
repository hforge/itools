# -*- coding: UTF-8 -*-
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from xapian
from xapian import Enquire, MultiValueSorter, Query

# Import from itools
from itools.datatypes import Unicode
from utils import _decode, _get_field_cls, _get_xquery


class SearchDocument(object):

    def __init__(self, xdoc, fields, metadata):
        self._xdoc = xdoc
        self._fields = fields
        self._metadata = metadata


    def __getattr__(self, name):
        info = self._metadata[name]
        field_cls = _get_field_cls(name, self._fields, info)

        # Get the data
        value = info['value']
        data = self._xdoc.get_value(value)

        # Multilingual field: language negotiation
        if not data and issubclass(field_cls, Unicode) and 'from' not in info:
            prefix = '%s_' % name
            n = len(prefix)
            languages = [ k[n:] for k in self._metadata if k[:n] == prefix ]
            if languages:
                language = select_language(languages)
                if language is None:
                    language = languages[0]
                return getattr(self, '%s_%s' % (name, language))

        # Standard (monolingual)
        return _decode(field_cls, data)



class SearchResults(object):

    def __init__(self, catalog, xquery):
        self._catalog = catalog
        self._xquery = xquery

        # Enquire
        enquire = Enquire(catalog._db)
        enquire.set_query(xquery)
        self._enquire = enquire

        # Max
        max = enquire.get_mset(0,0).get_matches_upper_bound()
        self._max = enquire.get_mset(0, max).size()


    def __len__(self):
        """Returns the number of documents found."""
        return self._max


    def search(self, query=None, **kw):
        catalog = self._catalog

        xquery = _get_xquery(catalog, query, **kw)
        query = Query(Query.OP_AND, [self._xquery, xquery])
        return SearchResults(catalog, query)


    def get_documents(self, sort_by=None, reverse=False, start=0, size=0):
        """Returns the documents for the search, sorted by weight.

        Four optional arguments are accepted, which will modify the documents
        returned.

        First, it is possible to sort by a field, or a list of fields, instead
        of by the weight. The condition is that the field must be stored:

          - "sort_by", if given it must be the name of an stored field, or
            a list of names of stored fields. The results will be sorted by
            this fields, instead of by the weight.

          - "reverse", a boolean value that says whether the results will be
            ordered from smaller to greater (reverse is False, the default),
            or from greater to smaller (reverse is True). This parameter only
            takes effect if the parameter "sort_by" is also given.

        It is also possible to ask for a subset of the documents:

          - "start": returns the documents starting from the given start
            position.

          - "size": returns at most documents as specified by this parameter.

        By default all the documents are returned.
        """
        enquire = self._enquire
        metadata = self._catalog._metadata

        # sort_by != None
        if sort_by is not None:
            if isinstance(sort_by, list):
                sorter = MultiValueSorter()
                for name in sort_by:
                    # If there is a problem, ignore this field
                    if name not in metadata:
                        continue
                    sorter.add(metadata[name]['value'])
                enquire.set_sort_by_key_then_relevance(sorter, reverse)
            else:
                # If there is a problem, ignore the sort
                if sort_by in metadata:
                    value = metadata[sort_by]['value']
                    enquire.set_sort_by_value_then_relevance(value, reverse)
        else:
            enquire.set_sort_by_relevance()

        # start/size
        if size == 0:
            size = self._max

        # Construction of the results
        fields = self._catalog._fields
        cls = self._catalog.search_document
        results = [ cls(x.get_document(), fields, metadata)
                    for x in enquire.get_mset(start, size) ]

        # sort_by=None/reverse=True
        if sort_by is None and reverse:
            results.reverse()

        return results



