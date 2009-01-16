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

# Import from the standard library
from marshal import dumps, loads

# Import from xapian
from xapian import Database, WritableDatabase, DB_CREATE, DB_OPEN
from xapian import Document, Enquire, Query
from xapian import MultiValueSorter, sortable_serialise, sortable_unserialise

# Import from itools
from itools.uri import get_absolute_reference
from base import CatalogAware
from exceptions import XapianIndexError
from fields import get_field
from queries import RangeQuery, PhraseQuery, AndQuery, OrQuery
from queries import AllQuery, NotQuery, StartQuery


# Constants
OP_AND = Query.OP_AND
OP_AND_NOT = Query.OP_AND_NOT
OP_OR = Query.OP_OR
OP_PHRASE= Query.OP_PHRASE
OP_VALUE_RANGE = Query.OP_VALUE_RANGE
OP_VALUE_GE = Query.OP_VALUE_GE
OP_VALUE_LE = Query.OP_VALUE_LE



# We must overload the normal behaviour (range + optimization)
def _encode(field_type, value):
    # integer
    # XXX warning: this doesn't work with the big integers!
    if field_type == 'integer':
        return sortable_serialise(value)
    # A common field or a new field
    field = get_field(field_type)
    return field.encode(value)



def _decode(field_type, data):
    # integer
    if field_type == 'integer':
        if data == '':
            return None
        return int(sortable_unserialise(data))
    # A common field or a new field
    field = get_field(field_type)
    return field.decode(data)



def _index(xdoc, field_type, value, prefix):
    field = get_field(field_type)
    for term in field.split(value):
        xdoc.add_posting(prefix+term[0], term[1])



def _make_PhraseQuery(field_type, value, prefix):
    field = get_field(field_type)
    words = []
    for word in field.split(value):
        words.append(prefix+word[0])
    return Query(OP_PHRASE, words)



def _get_prefix(number):
    """By convention:
    Q is used for the unique Id of a document
    X for a long prefix
    Z for a stemmed word
    """
    # 0 is for the key field, the unique Id of a document
    magic_letters = 'QABCDEFGHIJKLMNOPRSTUVWY'
    size = len(magic_letters)
    result = 'X'*(number/size)
    return result+magic_letters[number%size]



def _get_xquery(catalog, query=None, **kw):
    # Case 1: a query is given
    if query is not None:
        return catalog._query2xquery(query)

    # Case 2: nothing has been specified, return everything
    if not kw:
        return Query('')

    # Case 3: build the query from the keyword parameters
    fields = catalog._fields
    xqueries = []
    for name in kw:
        # 'name' must be indexed
        if name not in fields:
            raise XapianIndexError(name)

        # Ok
        info = fields[name]
        query = _make_PhraseQuery(info['type'], kw[name], info['prefix'])
        xqueries.append(query)

    return Query(OP_AND, xqueries)



class Doc(object):

    def __init__(self, xdoc, fields):
        self._xdoc = xdoc
        self._fields = fields


    def __getattr__(self, name):
        info = self._fields[name]
        data = self._xdoc.get_value(info['value'])
        return _decode(info['type'], data)



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


    # FIXME Obsolete
    get_n_documents = __len__


    def search(self, query=None, **kw):
        catalog = self._catalog

        xquery = _get_xquery(catalog, query, **kw)
        return SearchResults(catalog, Query(OP_AND, [self._xquery, xquery]))


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
        fields = self._catalog._fields

        # sort_by != None
        if sort_by is not None:
            if isinstance(sort_by, list):
                sorter = MultiValueSorter()
                for name in sort_by:
                    # If there is a problem, ...
                    if name not in fields:
                        raise XapianIndexError(name)
                    sorter.add(fields[name]['value'])
                enquire.set_sort_by_key_then_relevance(sorter, reverse)
            else:
                # If there is a problem, ...
                if sort_by not in fields:
                    raise XapianIndexError(name)
                value = fields[sort_by]['value']
                enquire.set_sort_by_value_then_relevance(value, reverse)
        else:
            enquire.set_sort_by_relevance()

        # start/size
        if size == 0:
            size = self._max

        # Construction of the results
        results = []
        for doc in enquire.get_mset(start, size):
            results.append(Doc(doc.get_document(), fields))

        # sort_by=None/reverse=True
        if sort_by is None and reverse:
            results.reverse()

        return results



class Catalog(object):

    def __init__(self, ref, read_only=False):
        # Load the database
        if isinstance(ref, Database) or isinstance(ref, WritableDatabase):
            self._db = ref
        else:
            uri = get_absolute_reference(ref)
            if uri.scheme != 'file':
                raise IOError, ('The file system supported with catalog is '
                                'only "file"')
            path = str(uri.path)

            if read_only:
                self._db = Database(path)
            else:
                self._db = WritableDatabase(path, DB_OPEN)

        db = self._db

        # Asynchronous mode
        if not read_only:
            db.begin_transaction(False)

        # Load the xfields from the database
        self._fields = {}
        self._key_field = None
        self._value_nb = 0
        self._prefix_nb = 0
        self._load_all_internal()


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
        self._load_all_internal()
        db.begin_transaction(False)


    #######################################################################
    # API / Public / (Un)Index
    #######################################################################
    def index_document(self, document):
        """Add a new document.
        """
        db = self._db
        fields = self._fields

        # Check the input
        if not isinstance(document, CatalogAware):
            raise ValueError, 'the document must be a CatalogAware object'

        # Extract the definition and values (do it first, because it may
        # fail).
        doc_fields = document.get_catalog_fields()
        doc_values = document.get_catalog_values()

        # A least one field !
        if len(doc_fields) == 0:
            raise ValueError, 'the document must have at least one field'

        # Make the xapian document
        fields_modified = False
        xdoc = Document()
        for position, field in enumerate(doc_fields):
            name = field.name

            # New field ?
            if name not in fields:
                info = {}
                # Type
                info['type'] = field.type

                # The first, so the key field
                if position == 0:
                    # Key field
                    self._key_field = name
                    info['is_key_field'] = True

                    # The key field must be stored and indexed
                    if not field.is_stored or not field.is_indexed:
                        raise ValueError, ('the first field must be stored '
                                           'and indexed')
                # Stored ?
                if field.is_stored:
                    info['is_stored'] = True
                    info['value'] = self._value_nb
                    self._value_nb += 1
                # Indexed ?
                if field.is_indexed:
                    info['is_indexed'] = True
                    info['prefix'] = _get_prefix(self._prefix_nb)
                    self._prefix_nb += 1
                fields[name] = info
                fields_modified = True
            # Or verifications, ...
            else:
                info = fields[name]
                if ((field.is_stored != ('is_stored' in info)) or
                    (field.is_indexed != ('is_indexed' in info))):
                    msg = (
                        'You have already used the name "%s" for a field, but'
                        ' with an other is_stored/is_indexed combination')
                    raise ValueError, msg % name

            # doc_fields can be greater than doc_values
            if doc_values.get(name) is None:
                if name != self._key_field:
                    continue
                else:
                    raise IndexError, 'the first value is compulsory'


            # Is stored ?
            if field.is_stored:
                xdoc.add_value(info['value'], _encode(field.type,
                                                      doc_values[name]))
            # Is indexed ?
            if field.is_indexed:
                _index(xdoc, field.type, doc_values[name], info['prefix'])

        # Store the first value with the prefix 'Q'
        xdoc.add_term('Q'+_encode(fields[self._key_field]['type'],
                                  doc_values[self._key_field]))

        # TODO: Don't store two documents with the same key field!

        # Save the doc
        db.add_document(xdoc)

        # Store fields ?
        if fields_modified:
            db.set_metadata('fields', dumps(fields))


    def unindex_document(self, value):
        """Remove the document 'value'. Value is the first Field.
           If the document does not exist => no error
        """
        key_field = self._key_field
        if key_field is not None:
            data = _encode(self._fields[key_field]['type'], value)
            self._db.delete_document('Q'+data)


    #######################################################################
    # API / Public / Search
    #######################################################################
    def search(self, query=None, **kw):
        """Launch a search in the catalog.
        """
        xquery = _get_xquery(self, query, **kw)
        return SearchResults(self, xquery)


    def get_unique_values(self, name):
        """Return all the terms of a given indexed field
        """
        fields = self._fields
        if name in fields:
            prefix = fields[name]['prefix']
            return set([t.term[1:] for t in self._db.allterms(prefix)])
        else:
            # If there is a problem => an empty result
            return set()

    #######################################################################
    # API / Private
    #######################################################################
    def _load_all_internal(self):
        """Load the "fields" informations form the database
        """
        fields = self._db.get_metadata('fields')
        self._key_field = None
        self._value_nb = 0
        self._prefix_nb = 0
        if fields == '':
            self._fields = {}
        else:
            self._fields = loads(fields)
            for name, info in self._fields.iteritems():
                if 'is_stored' in info:
                    self._value_nb += 1
                if 'is_indexed' in info:
                    self._prefix_nb += 1
                if 'is_key_field' in info:
                    self._key_field = name


    def _query2xquery(self, query):
        """take a "itools" query and return a "xapian" query
        """
        query_class = query.__class__
        fields = self._fields

        # All Query
        if query_class is AllQuery:
            return Query('')

        # PhraseQuery, the field must be indexed
        if query_class is PhraseQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError, "unexpected '%s'" % type(name)
            # If there is a problem => an empty result
            if name not in fields:
                return Query()
            info = fields[name]
            return _make_PhraseQuery(info['type'], query.value,
                                     info['prefix'])

        # RangeQuery, the field must be stored
        if query_class is RangeQuery:
            name = query.name
            # If there is a problem => an empty result
            if name not in fields:
                return Query()

            info = fields[name]
            field_type = info['type']
            value = info['value']

            left = query.left
            right = query.right

            # Case 1: no limits, return everything
            if left is None and right is None:
                return Query('')

            # Case 2: left limit only
            if right is None:
                return Query(OP_VALUE_GE, value, _encode(field_type, left))

            # Case 3: right limit only
            if left is None:
                return Query(OP_VALUE_LE, value, _encode(field_type, right))

            # Case 4: left and right
            return Query(OP_VALUE_RANGE, value, _encode(field_type, left),
                         _encode(field_type, right))

        # StartQuery, the field must be stored
        if query_class is StartQuery:
            name = query.name
            value = query.value
            # If there is a problem => an empty result
            if name not in fields:
                return Query()

            info = fields[name]
            value_nb = info['value']

            value = _encode(info['type'], value)
            if value:
                # end_value = the word after value: toto => totp
                end_value = value[:-1] + unichr(ord(value[-1]) + 1)

                # good = {x / x >= value}
                good = Query(OP_VALUE_GE, value_nb, value)

                # bad = {x / x >= end_value}
                bad = Query(OP_VALUE_GE, value_nb, end_value)

                # Return {x / x in good but x not in bad}
                return Query(OP_AND_NOT, good, bad)
            else:
                # If value == '', we return everything
                return Query('')

        # And
        i2x = self._query2xquery
        if query_class is AndQuery:
            return Query(OP_AND, [ i2x(q) for q in query.atoms ])

        # Or
        if query_class is OrQuery:
            return Query(OP_OR, [ i2x(q) for q in query.atoms ])

        # Not
        if query_class is NotQuery:
            return Query(OP_AND_NOT, Query(''), i2x(query.query))



def make_catalog(uri):
    """Creates a new and empty catalog in the given uri.
    """
    uri = get_absolute_reference(uri)
    if uri.scheme != 'file':
        raise IOError, 'The file system supported with catalog is only "file"'

    path = str(uri.path)
    db = WritableDatabase(path, DB_CREATE)

    return Catalog(db)

