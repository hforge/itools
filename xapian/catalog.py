# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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



# Import from itools
from itools.uri import get_absolute_reference
from itools.catalog import (CatalogAware, get_field, EqQuery, RangeQuery,
                            PhraseQuery, AndQuery, OrQuery, NotQuery)

# Import from Xapian
from xapian import (WritableDatabase, DB_CREATE, DB_OPEN, Document, Enquire,
                    Query)
# Import from the standard library
from marshal import dumps, loads


class Result(object):
    def __init__(self, xfields, xdoc):
        self._xfields = xfields
        self._data = loads(xdoc.get_data())


    def __getattr__(self, name):
        data = self._data
        if name in data:
            field = get_field(self._xfields[name]['type'])
            return field.decode(data[name])
        else:
            raise AttributeError, "the field '%s' is not defined" % name


class SearchResults(object):
    def __init__(self, xfields, enquire):
        self._xfields = xfields
        self._enquire = enquire
        self._max = enquire.get_mset(0,0).get_matches_upper_bound()

    def get_n_documents(self):
        """Returns the number of documents found."""
        return self._enquire.get_mset(0, self._max).size()


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
        # XXX finish me
        results = []
        for doc in self._enquire.get_mset(0, self._max):
            results.append(Result(self._xfields, doc.get_document()))
        return results



class Catalog(object):
    def __init__(self, ref):
        if isinstance(ref, WritableDatabase):
            self._db = ref
        else:
            uri = get_absolute_reference(ref)
            if uri.scheme != 'file':
                raise IOError, ('The file system supported with catalog is '
                                'only "file"')
            path = str(uri.path)
            self._db = WritableDatabase(path, DB_OPEN)
        db = self._db

        # Asynchronous mode
        db.begin_transaction(False)

        # Load the xfields from the database
        self._xfields = {}
        self._key_field = None
        self._load_xfields()


    #######################################################################
    # API / Public / Transactions
    #######################################################################
    def save_changes(self):
        """Save the last changes to disk.
        """
        db = self._db
        db.commit_transaction()
        db.flush()
        db.begin_transaction(False)


    def abort_changes(self):
        """Abort the last changes made in memory.
        """
        db = self._db
        db.cancel_transaction()
        self._load_xfields()
        db.begin_transaction(False)



    #######################################################################
    # API / Public / (Un)Index
    #######################################################################
    def index_document(self, document):
        """Add a new document.
        """
        db = self._db
        xfields = self._xfields

        # Check the input
        if not isinstance(document, CatalogAware):
            raise ValueError, 'the document must be a CatalogAware object'

        # Extract the definition and values (do it first, because it may
        # fail).
        fields = document.get_catalog_fields()
        values = document.get_catalog_values()

        # A least one field !
        if len(fields) == 0:
            raise ValueError, 'the document must have at least one field'

        # Make the xapian document
        magic_letters = 'ABCDEFGHIJKLMNOPQRSTUWY'
        xfields_modified = False
        xdoc = Document()
        data = {}
        for field in fields:
            name = field.name
            if name not in values:
                continue

            # New field ?
            if name not in xfields:
                if len(xfields) >= len(magic_letters):
                    raise (IndexError, 'You have too many different fields '
                                       'in your database')
                prefix =  magic_letters[len(xfields)]
                xfields[name] = {'prefix':prefix, 'type':field.type}
                xfields_modified = True
                # First field => it's the key!
                if prefix == 'A':
                    self._key_field = name
            # Verification
            else:
                # TODO: 'type' must be the same
                pass

            # Indexed ?
            if field.is_indexed:
                prefix = xfields[name]['prefix']
                for term in field.split(values[name]):
                    xdoc.add_posting(prefix+term[0], term[1])

            # Stored ?
            if field.is_stored:
                data[name] = field.encode(values[name])
            else:
                data[name] = None

        # Store the first value with the prefix 'V'
        # XXX: the first field is stored 2 times!
        xdoc.add_term('V'+fields[0].encode(values[fields[0].name]))

        # TODO: Don't store two documents with the same key field!

        # Save the doc
        xdoc.set_data(dumps(data))
        db.add_document(xdoc)

        # Store xfields ?
        if xfields_modified:
            db.set_metadata('xfields', dumps(xfields))

        # XXX TEST
        #for t in xdoc.termlist():
        #    print t.term
        #print xfields


    def unindex_document(self, value):
        """Remove the document 'value'. Value is the first Field.
           If the document does not exist => no error
        """
        key_field = self._key_field
        if key_field is not None:
            field = self._name2field(key_field)
            self._db.delete_document('V'+field.encode(value))


    #######################################################################
    # API / Public / Search
    #######################################################################
    def search(self, query=None, **kw):
        """Launch a search in the catalog.
        """
        # Build the query if it is passed through keyword parameters
        if query is None:
            if kw:
                xqueries = []
                for key, value in kw.items():
                    prefix = self._xfields[key]['prefix']
                    field = self._name2field(key)
                    words = []
                    for word in field.split(value):
                        words.append(prefix+word[0])
                    xqueries.append(Query(Query.OP_PHRASE, words))
                xquery = Query(Query.OP_AND, xqueries)
            else:
                xquery = Query('')
        else:
            xquery = self._query2xquery(query)

        enquire = Enquire(self._db)
        enquire.set_query(xquery)
        return SearchResults(self._xfields, enquire)


    def get_unique_values(self, name):
        """Return all the terms of a given field ???
        """
        prefix = self._xfields[name]['prefix']
        return set([t.term[1:] for t in self._db.allterms(prefix)])


    #######################################################################
    # API / Private
    #######################################################################
    def _load_xfields(self):
        """Load the "fields" informations form the database
        """
        xfields = self._db.get_metadata('xfields')
        self._key_field = None
        if xfields == '':
            self._xfields = {}
        else:
            self._xfields = loads(xfields)
            for name, info in self._xfields.iteritems():
                if info['prefix'] == 'A':
                    self._key_field = name
                    return


    def _name2field(self, name):
        """Return a field class
        """
        return get_field(self._xfields[name]['type'])


    def _query2xquery(self, iquery):
        """take a "itools" query and return a "xapian" query
        """
        xfields = self._xfields
        i2x = self._query2xquery

        test = lambda c: isinstance(iquery, c)
        # XXX: the difference between EqQuery and PhraseQuery is
        #      that the value is not "splited". Is this the good behaviour?
        if test(EqQuery):
            prefix = xfields[iquery.name]['prefix']
            return Query(prefix+iquery.value)
        elif test(RangeQuery):
            raise NotImplementedError
        elif test(PhraseQuery):
            prefix = xfields[iquery.name]['prefix']
            field = self._name2field(iquery.name)
            words = []
            for word in field.split(iquery.value):
                words.append(prefix+word[0])
            return Query(Query.OP_PHRASE, words)
        elif test(AndQuery):
            return Query(Query.OP_AND, [i2x(q) for q in iquery.atoms])
        elif test(OrQuery):
            return Query(Query.OP_OR, [i2x(q) for q in iquery.atoms])
        elif test(NotQuery):
            return Query(Query.OP_AND_NOT, Query(''), i2x(iquery.query))




def make_catalog(uri):
    """Creates a new and empty catalog in the given uri.
    """
    uri = get_absolute_reference(uri)
    if uri.scheme != 'file':
        raise IOError, 'The file system supported with catalog is only "file"'

    path = str(uri.path)
    db = WritableDatabase(path, DB_CREATE)

    return Catalog(db)

