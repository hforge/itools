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
from xapian import Document, Enquire, Query, TermGenerator
# XXX from xapian import Stem
from xapian import MultiValueSorter, sortable_serialise, sortable_unserialise
from xapian import inmemory_open

# Import from itools
from itools.datatypes import Integer, Unicode
from itools.i18n import is_asian_character, is_punctuation
from itools.uri import get_absolute_reference
from base import CatalogAware
from exceptions import XapianIndexError
from queries import RangeQuery, PhraseQuery, AndQuery, OrQuery
from queries import AllQuery, NotQuery, StartQuery

# Constants
# XXX stemmer = Stem('en')
OP_AND = Query.OP_AND
OP_AND_NOT = Query.OP_AND_NOT
OP_OR = Query.OP_OR
OP_PHRASE= Query.OP_PHRASE
OP_VALUE_RANGE = Query.OP_VALUE_RANGE
OP_VALUE_GE = Query.OP_VALUE_GE
OP_VALUE_LE = Query.OP_VALUE_LE



# We must overload the normal behaviour (range + optimization)
def _encode(field_cls, value):
    # Overload the Integer type
    # XXX warning: this doesn't work with the big integers!
    if issubclass(field_cls, Integer):
        return sortable_serialise(value)
    # A common field or a new field
    return field_cls.encode(value)



def _decode(field_cls, data):
    # Overload the Integer type, cf _encode
    if issubclass(field_cls, Integer):
        if data == '':
            return None
        return int(sortable_unserialise(data))
    # A common field or a new field
    return field_cls.decode(data)



def _index_cjk(xdoc, value, prefix, termpos):
    """
    Returns the next word and its position in the data. The analysis
    is done with the automaton:

    0 -> 1 [letter or number]
    0 -> 0 [stop word]
    1 -> 1 [letter or number or cjk]
    1 -> 0 [stop word]
    0 -> 2 [cjk]
    2 -> 0 [stop word]
    2 -> 3 [letter or number or cjk]
    3 -> 3 [letter or number or cjk]
    3 -> 0 [stop word]
    """
    state = 0
    lexeme = previous_cjk = u''
    mode_cjk = None

    for c in value:
        if mode_cjk is None:
            mode_cjk = is_asian_character(c)

        if is_punctuation(c):
            # Stop word
            if mode_cjk: # CJK
                if previous_cjk and state == 2: # CJK not yielded yet
                    xdoc.add_posting(prefix + previous_cjk, termpos)
                    termpos += 1
            else: # ASCII
                if state == 1:
                    lexeme = lexeme.lower()
                    xdoc.add_posting(prefix + lexeme, termpos)
                    termpos += 1

            # reset state
            lexeme = u''
            previous_cjk = u''
            state = 0
            mode_cjk = None
        else:
            if mode_cjk is False: # ASCII
                if state == 1:
                    lexeme += c
                else: # state == 0
                    lexeme += c
                    state = 1

            else: # CJK
                c = c.lower()
                if previous_cjk:
                    xdoc.add_posting(prefix + (u'%s%s' % (previous_cjk, c)),
                                     termpos)
                    termpos += 1
                    state = 3
                else:
                    state = 2
                previous_cjk = c

    # Last word
    if state == 1:
        lexeme = lexeme.lower()
        xdoc.add_posting(prefix + lexeme, termpos)
    elif previous_cjk and state == 2:
        xdoc.add_posting(prefix + previous_cjk, termpos)

    return termpos + 1



def _index_unicode_value(xdoc, value, prefix, language, termpos):
    if language in ['ko', 'ja', 'zh']:
        return _index_cjk(xdoc, value, prefix, termpos)
    else:
        tg = TermGenerator()
        tg.set_document(xdoc)
        tg.set_termpos(termpos - 1)
        # XXX The words are saved twice: with prefix and with Zprefix
        #tg.set_stemmer(stemmer)
        tg.index_text(value, 1, prefix)
        return tg.get_termpos() + 1



def _index_unicode(xdoc, field_cls, value, prefix, language):
    if (field_cls.multiple and
        isinstance(value, (tuple, list, set, frozenset))):
        termpos = 1
        for x in value:
            termpos = _index_unicode_value(xdoc, x, prefix, language, termpos)
    else:
        _index_unicode_value(xdoc, value, prefix, language, 1)



def _index(xdoc, field_cls, value, prefix):
    """To index a field it must be split in a sequence of words and
    positions:

      [(word, 1), (word, 2), (word, 3), ...]

    Where <word> will be a <str> value.
    """

    # Unicode: a complex split
    if issubclass(field_cls, Unicode):
        # A multilingual value ?
        # XXX Make it compulsory
        if isinstance(value, dict):
            for language, a_value in value.iteritems():
                _index_unicode(xdoc, field_cls, a_value, prefix, language)
        else:
            _index_unicode(xdoc, field_cls, value, prefix, 'en')
    # An other type: too easy
    else:
        if (field_cls.multiple and
            isinstance(value, (tuple, list, set, frozenset))):
            for position, x in enumerate(value):
                xdoc.add_posting(prefix + field_cls.encode(x), position + 1)
        else:
            xdoc.add_posting(prefix + field_cls.encode(value), 1)



def _make_PhraseQuery(field_cls, value, prefix):
    # Get the words
    # XXX It's too complex (slow), we must use xapian
    #     Problem => _index_cjk
    xdoc = Document()
    _index(xdoc, field_cls, value, prefix)
    words = []
    for term_list_item in xdoc:
        term = term_list_item.term
        for termpos in term_list_item.positer:
            words.append((termpos, term))
    words.sort()
    words = [ word[1] for word in words ]

    # Make the query
    return Query(OP_PHRASE, words)



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



def _get_xquery(catalog, query=None, **kw):
    # Case 1: a query is given
    if query is not None:
        return catalog._query2xquery(query)

    # Case 2: nothing has been specified, return everything
    if not kw:
        return Query('')

    # Case 3: build the query from the keyword parameters
    metadata = catalog._metadata
    fields = catalog._fields
    xqueries = []
    for name, value in kw.iteritems():
        # If name is a field not yet indexed, return nothing
        if name not in metadata:
            return Query()

        # Ok
        prefix = metadata[name]['prefix']
        query = _make_PhraseQuery(fields[name], value, prefix)
        xqueries.append(query)

    return Query(OP_AND, xqueries)



def split_unicode(text, language='en'):
    xdoc = Document()
    _index_unicode_value(xdoc, text, '', language, 1)
    words = []
    for term_list_item in xdoc:
        term = unicode(term_list_item.term, 'utf-8')
        for termpos in term_list_item.positer:
            words.append((termpos, term))
    words.sort()
    return [ word[1] for word in words ]



class Doc(object):

    def __init__(self, xdoc, fields, metadata):
        self._xdoc = xdoc
        self._fields = fields
        self._metadata = metadata


    def __getattr__(self, name):
        value = self._metadata[name]['value']
        data = self._xdoc.get_value(value)
        return _decode(self._fields[name], data)



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
        results = []
        for doc in enquire.get_mset(start, size):
            results.append(Doc(doc.get_document(), fields, metadata))

        # sort_by=None/reverse=True
        if sort_by is None and reverse:
            results.reverse()

        return results



class Catalog(object):

    def __init__(self, ref, fields, read_only=False,
                 asynchronous_mode=True):

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
        if not isinstance(document, CatalogAware):
            raise ValueError, 'the document must be a CatalogAware object'

        # Extract the values (do it first, because it may fail).
        doc_values = document.get_catalog_values()

        # Make the xapian document
        metadata_modified = False
        xdoc = Document()
        for name, value in doc_values.iteritems():
            field_cls = fields[name]

            # New field ?
            if name not in metadata:
                info = {}

                # The key field ?
                if getattr(field_cls, 'is_key_field', False):
                    if self._key_field is not None:
                        raise ValueError, 'You must have only one key field'
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
                # XXX the key field is indexed twice
                if getattr(field_cls, 'is_indexed', False):
                    info['prefix'] = _get_prefix(self._prefix_nb)
                    self._prefix_nb += 1

                # Save info
                # XXX info can be "{}"
                metadata[name] = info
                metadata_modified = True
            else:
                info = metadata[name]

            # The value can be None
            if value is not None:
                # Is stored ?
                if getattr(field_cls, 'is_stored', False):
                    xdoc.add_value(info['value'], _encode(field_cls, value))

                # Is indexed ?
                if getattr(field_cls, 'is_indexed', False):
                    _index(xdoc, field_cls, value, info['prefix'])

        # Store the first value with the prefix 'Q'
        key_field = self._key_field
        if key_field is None or key_field not in doc_values:
            raise ValueError, 'the "key_field" value is compulsory'
        xdoc.add_term('Q'+_encode(fields[key_field], doc_values[key_field]))

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
            data = _encode(self._fields[key_field], value)
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
        metadata = self._metadata
        if name in metadata:
            prefix = metadata[name]['prefix']
            prefix_size = len(prefix)
            return set([ t.term[prefix_size:]
                         for t in self._db.allterms(prefix) ])
        else:
            # If there is a problem => an empty result
            return set()

    #######################################################################
    # API / Private
    #######################################################################
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
            prefix = metadata[name]['prefix']
            return _make_PhraseQuery(fields[name], query.value, prefix)

        # RangeQuery, the field must be stored
        if query_class is RangeQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError, "unexpected '%s'" % type(name)
            # If there is a problem => an empty result
            if name not in metadata:
                return Query()

            value = metadata[name]['value']
            field_cls = fields[name]

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

            value_nb = metadata[name]['value']

            value = query.value
            value = _encode(fields[name], value)

            if value:
                # end_value = the word after value: toto => totp
                # XXX This code is bogus if the value = '\xff'
                # XXX We must fix it!!
                end_value = value[:-1] + chr(ord(value[-1]) + 1)

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



def make_catalog(uri, fields):
    """Creates a new and empty catalog in the given uri.

       If uri=None the catalog is made "in memory".
       fields must be a dict. It contains some informations about the
       fields in the database.
       By example:
       fields = {'id': Integer(is_key_field=True, is_stored=True,
                               is_indexed=True), ...}
    """
    if uri is None:
        db = inmemory_open()
        return Catalog(db, fields, asynchronous_mode=False)
    else:
        uri = get_absolute_reference(uri)
        if uri.scheme != 'file':
            raise IOError, ('The file system supported with catalog is only '
                            '"file"')
        path = str(uri.path)
        db = WritableDatabase(path, DB_CREATE)
        return Catalog(db, fields)


