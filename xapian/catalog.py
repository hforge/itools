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
from xapian import Document, Query, inmemory_open

# Import from itools
from itools.uri import get_reference
from itools.vfs import cwd
from base import CatalogAware
from queries import AllQuery, AndQuery, NotQuery, OrQuery, PhraseQuery
from queries import RangeQuery, StartQuery
from results import SearchResults, SearchDocument
from utils import _encode, _get_field_cls, _reduce_size, _make_PhraseQuery
from utils import _index, _get_xquery



# Constants
OP_AND = Query.OP_AND
OP_AND_NOT = Query.OP_AND_NOT
OP_OR = Query.OP_OR
OP_VALUE_RANGE = Query.OP_VALUE_RANGE
OP_VALUE_GE = Query.OP_VALUE_GE
OP_VALUE_LE = Query.OP_VALUE_LE



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



class Catalog(object):

    search_document = SearchDocument


    def __init__(self, ref, fields, read_only=False, asynchronous_mode=True):
        # Load the database
        if isinstance(ref, Database) or isinstance(ref, WritableDatabase):
            self._db = ref
        else:
            uri = cwd.get_uri(ref)
            uri = get_reference(uri)
            if uri.scheme != 'file':
                raise IOError, ('The file system supported with catalog is '
                                'only "file"')
            path = str(uri.path)

            if read_only:
                self._db = Database(path)
            else:
                self._db = WritableDatabase(path, DB_OPEN)

        db = self._db
        self._asynchronous = asynchronous_mode
        self._fields = fields

        # Asynchronous mode
        if not read_only and asynchronous_mode:
            db.begin_transaction(False)

        # Load the xfields from the database
        self._metadata = {}
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
        if not self._asynchronous:
            raise ValueError, "The transactions are synchronous"
        db = self._db
        db.commit_transaction()
        db.flush()
        db.begin_transaction(False)


    def abort_changes(self):
        """Abort the last changes made in memory.
        """
        if not self._asynchronous:
            raise ValueError, "The transactions are synchronous"
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
        metadata = self._metadata
        fields = self._fields

        # Check the input
        if type(document) is dict:
            doc_values = document
        elif isinstance(document, CatalogAware):
            doc_values = document.get_catalog_values()
        else:
            raise ValueError, 'the document must be a CatalogAware object'

        # Make the xapian document
        metadata_modified = False
        xdoc = Document()
        for name, value in doc_values.iteritems():
            field_cls = fields[name]

            # New field ?
            if name not in metadata:
                info = metadata[name] = self._get_info(field_cls, name)
                metadata_modified = True
            else:
                info = metadata[name]

            # A multilingual value ?
            if isinstance(value, dict):
                for language, lang_value in value.iteritems():
                    lang_name = name + '_' + language

                    # New field ?
                    if lang_name not in metadata:
                        lang_info = self._get_info(field_cls, lang_name)
                        lang_info['from'] = name
                        metadata[lang_name] = lang_info
                        metadata_modified = True
                    else:
                        lang_info = metadata[lang_name]

                    # The value can be None
                    if lang_value is not None:
                        # Is stored ?
                        if 'value' in lang_info:
                            xdoc.add_value(lang_info['value'],
                                           _encode(field_cls, lang_value))
                        # Is indexed ?
                        if 'prefix' in lang_info:
                            # Comment: Index twice
                            _index(xdoc, field_cls, lang_value,
                                   info['prefix'], language)
                            _index(xdoc, field_cls, lang_value,
                                   lang_info['prefix'], language)
            # The value can be None
            elif value is not None:
                # Is stored ?
                if 'value' in info:
                    xdoc.add_value(info['value'], _encode(field_cls, value))
                # Is indexed ?
                if 'prefix' in info:
                    # By default language='en'
                    _index(xdoc, field_cls, value, info['prefix'], 'en')

        # Store the key field with the prefix 'Q'
        # Comment: the key field is indexed twice, but we must do it
        #          one => to index (as the others)
        #          two => to index without split
        #          the problem is that "_encode != _index"
        key_field = self._key_field
        if (key_field is None or key_field not in doc_values or
            doc_values[key_field] is None):
            raise ValueError, 'the "key_field" value is compulsory'
        data = _reduce_size(_encode(fields[key_field], doc_values[key_field]))
        xdoc.add_term('Q' + data)

        # TODO: Don't store two documents with the same key field!

        # Save the doc
        db.add_document(xdoc)

        # Store metadata ?
        if metadata_modified:
            db.set_metadata('metadata', dumps(metadata))


    def unindex_document(self, value):
        """Remove the document that has value stored in its key_field.
           If the document does not exist => no error
        """
        key_field = self._key_field
        if key_field is not None:
            data = _reduce_size(_encode(self._fields[key_field], value))
            self._db.delete_document('Q' + data)


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
        metadata = self._metadata
        # If there is a problem => an empty result
        if name not in metadata:
            return set()

        # Ok
        prefix = metadata[name]['prefix']
        prefix_len = len(prefix)
        return set([ t.term[prefix_len:] for t in self._db.allterms(prefix) ])


    #######################################################################
    # API / Private
    #######################################################################
    def _get_info(self, field_cls, name):
        info = {}

        # The key field ?
        if getattr(field_cls, 'is_key_field', False):
            if self._key_field is not None:
                raise ValueError, ('You must have only one key field, '
                                   'not multiple, not multilingual')
            if not (field_cls.is_stored and field_cls.is_indexed):
                raise ValueError, ('the key field must be stored '
                                   'and indexed')
            self._key_field = name
            info['key_field'] = True
        # Stored ?
        if getattr(field_cls, 'is_stored', False):
            info['value'] = self._value_nb
            self._value_nb += 1
        # Indexed ?
        if getattr(field_cls, 'is_indexed', False):
            info['prefix'] = _get_prefix(self._prefix_nb)
            self._prefix_nb += 1

        return info


    def _load_all_internal(self):
        """Load the metadata from the database
        """
        self._key_field = None
        self._value_nb = 0
        self._prefix_nb = 0

        metadata = self._db.get_metadata('metadata')
        if metadata == '':
            self._metadata = {}
        else:
            self._metadata = loads(metadata)
            for name, info in self._metadata.iteritems():
                if 'key_field' in info:
                    self._key_field = name
                if 'value' in info:
                    self._value_nb += 1
                if 'prefix' in info:
                    self._prefix_nb += 1


    def _query2xquery(self, query):
        """take a "itools" query and return a "xapian" query
        """
        query_class = query.__class__
        fields = self._fields
        metadata = self._metadata

        # All Query
        if query_class is AllQuery:
            return Query('')

        # PhraseQuery, the field must be indexed
        if query_class is PhraseQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError, "unexpected '%s'" % type(name)
            # If there is a problem => an empty result
            if name not in metadata:
                return Query()
            info = metadata[name]
            prefix = info['prefix']
            field_cls = _get_field_cls(name, fields, info)
            return _make_PhraseQuery(field_cls, query.value, prefix)

        # RangeQuery, the field must be stored
        if query_class is RangeQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError, "unexpected '%s'" % type(name)
            # If there is a problem => an empty result
            if name not in metadata:
                return Query()

            info = metadata[name]
            value = info['value']
            field_cls = _get_field_cls(name, fields, info)

            left = query.left
            right = query.right

            # Case 1: no limits, return everything
            if left is None and right is None:
                return Query('')

            # Case 2: left limit only
            if right is None:
                return Query(OP_VALUE_GE, value, _encode(field_cls, left))

            # Case 3: right limit only
            if left is None:
                return Query(OP_VALUE_LE, value, _encode(field_cls, right))

            # Case 4: left and right
            return Query(OP_VALUE_RANGE, value, _encode(field_cls, left),
                         _encode(field_cls, right))

        # StartQuery, the field must be stored
        if query_class is StartQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError, "unexpected '%s'" % type(name)
            # If there is a problem => an empty result
            if name not in metadata:
                return Query()

            info = metadata[name]
            value_nb = info['value']
            field_cls = _get_field_cls(name, fields, info)

            value = query.value
            value = _encode(field_cls, value)

            if value:
                # good = {x / x >= value}
                good = Query(OP_VALUE_GE, value_nb, value)

                # Construct the variable end_value:
                # end_value = the word "after" value: toto => totp

                # Delete the '\xff' at the end of value
                end_value = value
                while end_value and ord(end_value[-1]) == 255:
                    end_value = end_value[:-1]

                # Normal case: end_value is not empty
                if end_value:
                    # The world after
                    end_value = end_value[:-1] + chr(ord(end_value[-1]) + 1)

                    # bad = {x / x >= end_value}
                    bad = Query(OP_VALUE_GE, value_nb, end_value)

                    # Return {x / x in good but x not in bad}
                    return Query(OP_AND_NOT, good, bad)
                # If end_value is empty
                else:
                    # Return {x / x in good}
                    return good
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



def make_catalog(uri, fields):
    """Creates a new and empty catalog in the given uri.

       If uri=None the catalog is made "in memory".
       fields must be a dict. It contains some informations about the
       fields in the database.
       By example:
       fields = {'id': Integer(is_key_field=True, is_stored=True,
                               is_indexed=True), ...}
    """
    # In memory
    if uri is None:
        db = inmemory_open()
        return Catalog(db, fields, asynchronous_mode=False)

    # In the local filesystem
    uri = cwd.get_uri(uri)
    uri = get_reference(uri)
    if uri.scheme != 'file':
        raise IOError, 'The file system supported with catalog is only "file"'

    path = str(uri.path)
    db = WritableDatabase(path, DB_CREATE)
    return Catalog(db, fields)

