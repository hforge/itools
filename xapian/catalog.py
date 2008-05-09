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

# Import from the standard library
from marshal import dumps, loads

# Import from xapian
from xapian import (WritableDatabase, DB_CREATE, DB_OPEN, Document, Enquire,
                    Query, sortable_serialise, sortable_unserialise,
                    MultiValueSorter, TermGenerator, QueryParser, Stem)

# Import from itools
from itools.uri import get_absolute_reference
from itools.catalog import (CatalogAware, get_field, EqQuery, RangeQuery,
                            PhraseQuery, AndQuery, OrQuery, NotQuery)



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
        return int(sortable_unserialise(data))
    # A common field or a new field
    field = get_field(field_type)
    return field.decode(data)



def _index(xdoc, field_type, value, prefix):
    # text
    if field_type == 'text':
        # XXX TEST: we use an english stemmer in all cases
        field = get_field('text')
        stemmer = Stem('en')
        for term in field.split(value):
            xdoc.add_posting(prefix+stemmer(term[0]), term[1])
        #indexer = TermGenerator()
        #indexer.set_document(xdoc)
        #indexer.index_text(value, 1, prefix)
    # A common field or a new field
    else:
        field = get_field(field_type)
        for term in field.split(value):
            xdoc.add_posting(prefix+term[0], term[1])



def _make_PhraseQuery(field_type, value, prefix):
    if field_type == 'text':
        # XXX TEST
        field = get_field('text')
        words = []
        stemmer = Stem('en')
        for word in field.split(value):
            words.append(prefix+stemmer(word[0]))
        return Query(Query.OP_PHRASE, words)

    # A common field or a new field
    field = get_field(field_type)
    words = []
    for word in field.split(value):
        words.append(prefix+word[0])
    return Query(Query.OP_PHRASE, words)



def _get_prefix(number):
    """By convention:
    Q is used for the unique Id of a document
    X for a long prefix
    Z for a stemmed word
    """
    magic_letters = 'ABCDEFGHIJKLMNOPRSTUVWY'
    size = len(magic_letters)
    result = 'X'*(number/size)
    return result+magic_letters[number%size]



class Doc(object):

    def __init__(self, xdoc, fields):
        self._xdoc = xdoc
        self._fields = fields


    def __getattr__(self, name):
        info = self._fields[name]
        data = self._xdoc.get_value(info['value'])
        return _decode(info['type'], data)



class SearchResults(object):

    def __init__(self, query, db, fields):
        self._query = query
        self._db = db
        self._fields = fields

        # Compute max
        enquire = Enquire(db)
        enquire.set_query(query)
        self._max = enquire.get_mset(0,0).get_matches_upper_bound()


    def get_n_documents(self):
        """Returns the number of documents found."""
        enquire = Enquire(self._db)
        enquire.set_query(self._query)
        return enquire.get_mset(0, self._max).size()


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
        enquire = Enquire(self._db)
        enquire.set_query(self._query)
        fields = self._fields

        # sort_by != None
        if sort_by is not None:
            if isinstance(sort_by, list):
                sorter = MultiValueSorter()
                for name in sort_by:
                    sorter.add(fields[name]['value'])
                enquire.set_sort_by_key_then_relevance(sorter, reverse)
            else:
                enquire.set_sort_by_value_then_relevance(
                                            fields[sort_by]['value'], reverse)
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

    def __init__(self, ref):
        # Load the database
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
                # The first, so the key field?
                if position == 0:
                    info['is_key_field'] = True
                    self._key_field = name
                fields[name] = info
                fields_modified = True
            # Verifications
            #else:
            # XXX Question: must we verify if the informations are the same?

            # doc_fields can be greater than doc_values
            if doc_values.get(name) is None:
                if name != self._key_field:
                    continue
                else:
                    raise IndexError, 'the first value is compulsory'

            info = fields[name]

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
        fields = self._fields
        # Build the query if it is passed through keyword parameters
        if query is None:
            if kw:
                xqueries = []
                # name must be indexed
                for name, value in kw.items():
                    info = fields[name]
                    xqueries.append(_make_PhraseQuery(info['type'], value,
                                                      info['prefix']))
                xquery = Query(Query.OP_AND, xqueries)
            else:
                xquery = Query('')
        else:
            xquery = self._query2xquery(query)

        return SearchResults(xquery, self._db, self._fields)


    def get_unique_values(self, name):
        """Return all the terms of a given indexed field
        """
        prefix = self._fields[name]['prefix']
        return set([t.term[1:] for t in self._db.allterms(prefix)])


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
        if query_class is EqQuery or query_class is PhraseQuery:
            # EqQuery = PhraseQuery, the field must be indexed
            info = self._fields[query.name]
            return _make_PhraseQuery(info['type'], query.value, info['prefix'])
        elif query_class is RangeQuery:
            # RangeQuery, the field must be stored
            info = self._fields[query.name]
            field_type = info['type']
            return Query(Query.OP_VALUE_RANGE, info['value'],
                         _encode(field_type, query.left),
                         _encode(field_type, query.right))

        # And, Or, Not
        i2x = self._query2xquery
        if query_class is AndQuery:
            return Query(Query.OP_AND, [i2x(q) for q in query.atoms])
        elif query_class is OrQuery:
            return Query(Query.OP_OR, [i2x(q) for q in query.atoms])
        elif query_class is NotQuery:
            return Query(Query.OP_AND_NOT, Query(''), i2x(query.query))



def make_catalog(uri):
    """Creates a new and empty catalog in the given uri.
    """
    uri = get_absolute_reference(uri)
    if uri.scheme != 'file':
        raise IOError, 'The file system supported with catalog is only "file"'

    path = str(uri.path)
    db = WritableDatabase(path, DB_CREATE)

    return Catalog(db)

