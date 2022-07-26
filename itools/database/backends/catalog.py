# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2011 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2008-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2009 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2010-2011 Hervé Cauwelier <herve@oursours.net>
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
import os
from decimal import Decimal as decimal
from datetime import datetime
from marshal import dumps, loads
from hashlib import sha1

# Import from xapian
from xapian import Database, WritableDatabase, DB_CREATE, DB_OPEN, DB_BACKEND_GLASS
from xapian import Document, Query, QueryParser, Enquire
from xapian import sortable_serialise, sortable_unserialise, TermGenerator

# Import from itools
from itools.core import fixed_offset, lazy, merge_dicts
from itools.datatypes import Decimal, Integer, Unicode, String
from itools.fs import lfs
from itools.i18n import is_punctuation
from logging import getLogger
from itools.database.queries import AllQuery, _AndQuery, NotQuery, _OrQuery, PhraseQuery
from itools.database.queries import RangeQuery, StartQuery, TextQuery, _MultipleQuery

log = getLogger("itools.database")
try:
    from xapian import MultiValueSorter

    XAPIAN_VERSION = '1.2'
except Exception:
    from xapian import MultiValueKeyMaker

    XAPIAN_VERSION = '1.4'

# Constants
OP_AND = Query.OP_AND
OP_AND_NOT = Query.OP_AND_NOT
OP_OR = Query.OP_OR
OP_PHRASE = Query.OP_PHRASE
OP_VALUE_RANGE = Query.OP_VALUE_RANGE
OP_VALUE_GE = Query.OP_VALUE_GE
OP_VALUE_LE = Query.OP_VALUE_LE
TQ_FLAGS = (QueryParser.FLAG_LOVEHATE +
            QueryParser.FLAG_PHRASE +
            QueryParser.FLAG_WILDCARD)
TRANSLATE_MAP = {ord('À'): ord('A'),
                 ord('Â'): ord('A'),
                 ord('â'): ord('a'),
                 ord('à'): ord('a'),
                 ord('Ç'): ord('C'),
                 ord('ç'): ord('c'),
                 ord('É'): ord('E'),
                 ord('Ê'): ord('E'),
                 ord('é'): ord('e'),
                 ord('ê'): ord('e'),
                 ord('è'): ord('e'),
                 ord('ë'): ord('e'),
                 ord('Î'): ord('I'),
                 ord('î'): ord('i'),
                 ord('ï'): ord('i'),
                 ord('ô'): ord('o'),
                 ord('û'): ord('u'),
                 ord('ù'): ord('u'),
                 ord('ü'): ord('u'),
                 ord("'"): ord(' ')}

MSG_NOT_INDEXED = 'the "{name}" field is not indexed'


def bytes_to_str(data):
    for encoding in ["utf-8", "windows-1252", "latin-1"]:
        try:
            if isinstance(data, bytes):
                return data.decode(encoding)
            else:
                return data
        except:
            pass
    raise Exception(f"Type DATA {type(data)} value {data}")


def warn_not_indexed(name):
    log.warning(MSG_NOT_INDEXED.format(name=name))


MSG_NOT_STORED = 'the "{name}" field is not stored'


def warn_not_stored(name):
    log.warning(MSG_NOT_STORED.format(name=name))


MSG_NOT_INDEXED_NOR_STORED = 'the "{name}" field is not indexed nor stored'


def warn_not_indexed_nor_stored(name):
    log.warning(MSG_NOT_INDEXED_NOR_STORED.format(name=name))


class Doc(object):

    def __init__(self, xdoc, fields, metadata):
        self._xdoc = xdoc
        self._fields = fields
        self._metadata = metadata

    def __getattr__(self, name):
        # 1. Get the raw value
        info = self._metadata.get(name)
        if info is None:
            raise AttributeError(MSG_NOT_INDEXED_NOR_STORED.format(name=name))

        stored = info.get('value')
        if stored is None:
            raise AttributeError(MSG_NOT_STORED.format(name=name))
        raw_value = self._xdoc.get_value(stored)

        # 2. Decode
        field_cls = _get_field_cls(name, self._fields, info)
        if raw_value:
            value = _decode(field_cls, raw_value)
            setattr(self, name, value)
            return value

        # 3. Special Case: multilingual field (language negotiation)
        if issubclass(field_cls, Unicode) and 'from' not in info:
            prefix = '%s_' % name
            n = len(prefix)

            languages = []
            values = {}
            for k in self._metadata:
                if k[:n] == prefix:
                    language = k[n:]
                    value = getattr(self, '%s_%s' % (name, language))
                    if not field_cls.is_empty(value):
                        languages.append(language)
                        values[language] = value

            if languages:
                language = select_language(languages)
                if language is None:
                    language = languages[0]
                return values[language]

        # 4. Default
        # FIXME Xapian does not make the difference between the empty string
        # and the absence of value (None).
        value = field_cls.get_default()
        setattr(self, name, value)
        return value

    def get_value(self, name, language=None):
        # Check if stored
        info = self._metadata.get(name)
        if info is None:
            raise AttributeError(MSG_NOT_INDEXED_NOR_STORED.format(name=name))
        stored = info.get('value')
        if stored is None:
            raise AttributeError(MSG_NOT_STORED.format(name=name))
        # Get the raw value
        raw_value = self._xdoc.get_value(stored)
        # Decode
        field_cls = _get_field_cls(name, self._fields, info)
        if raw_value:
            return _decode(field_cls, raw_value)
        # Special Case: multilingual field
        if issubclass(field_cls, Unicode) and 'from' not in info:
            if language:
                name = '%s_%s' % (name, language)
                if self._metadata.get(name):
                    return getattr(self, name)
            else:
                prefix = '%s_' % name
                n = len(prefix)
                # Language negotiation
                languages = []
                values = {}
                for k in self._metadata:
                    if k[:n] == prefix:
                        language = k[n:]
                        value = getattr(self, '%s_%s' % (name, language))
                        if not field_cls.is_empty(value):
                            languages.append(language)
                            values[language] = value
                if languages:
                    language = select_language(languages)
                    if language is None:
                        language = languages[0]
                    return values[language]
        # Default
        return field_cls.get_default()


class SearchResults(object):

    def __init__(self, catalog, xquery):
        self._catalog = catalog
        self._xquery = xquery

    @lazy
    def _enquire(self):
        enquire = Enquire(self._catalog._db)
        enquire.set_query(self._xquery)
        return enquire

    @lazy
    def _max(self):
        enquire = self._enquire
        db = self._catalog._db
        doccount = db.get_doccount()
        return enquire.get_mset(0, doccount).size()

    def __len__(self):
        """Returns the number of documents found."""
        return self._max

    def search(self, query=None, **kw):
        xquery = _get_xquery(self._catalog, query, **kw)
        query = Query(Query.OP_AND, [self._xquery, xquery])
        return self.__class__(self._catalog, query)

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
        # sort_by != None
        metadata = self._catalog._metadata
        if sort_by is not None:
            if isinstance(sort_by, list):
                if XAPIAN_VERSION == '1.4':
                    sorter = MultiValueKeyMaker()
                    for name in sort_by:
                        # If there is a problem, ignore this field
                        if name not in metadata:
                            warn_not_stored(name)
                            continue
                        sorter.add_value(metadata[name]['value'], reverse)
                else:
                    sorter = MultiValueSorter()
                    for name in sort_by:
                        # If there is a problem, ignore this field
                        if name not in metadata:
                            warn_not_stored(name)
                            continue
                        sorter.add(metadata[name]['value'])
                enquire.set_sort_by_key_then_relevance(sorter, reverse)
            else:
                # If there is a problem, ignore the sort
                if sort_by in metadata:
                    value = metadata[sort_by]['value']
                    enquire.set_sort_by_value_then_relevance(value, reverse)
                else:
                    warn_not_stored(sort_by)
        else:
            enquire.set_sort_by_relevance()

        # start/size
        if size == 0:
            size = self._catalog._db.get_doccount()

        # Construction of the results
        fields = self._catalog._fields
        results = [Doc(x.document, fields, metadata)
                   for x in enquire.get_mset(start, size)]

        # sort_by=None/reverse=True
        if sort_by is None and reverse:
            results.reverse()

        return results


class Catalog(object):
    nb_changes = 0
    _db = None
    read_only = False

    def __init__(self, ref, fields, read_only=False, asynchronous_mode=True):
        self.read_only = read_only
        # Load the database
        if isinstance(ref, (Database, WritableDatabase)):
            path = None
            self._db = ref
        else:
            path = lfs.get_absolute_path(ref)
            if read_only:
                self._db = Database(path)
            else:
                self._db = WritableDatabase(path, DB_OPEN)

        db = self._db
        self._asynchronous = asynchronous_mode
        self._fields = fields
        # FIXME: There's a bug in xapian:
        # We cannot get stored values if DB not flushed
        self.commit_each_transaction = True
        # Asynchronous mode
        if not read_only and asynchronous_mode:
            db.begin_transaction(self.commit_each_transaction)
        # Set XAPIAN_FLUSH_THRESHOLD
        os.environ["XAPIAN_FLUSH_THRESHOLD"] = "2000"
        # Load the xfields from the database
        self._metadata = {}
        self._value_nb = 0
        self._prefix_nb = 0
        self._load_all_internal()
        if not read_only:
            self._init_all_metadata()

    def _init_all_metadata(self, has_changes=False):
        """Init new metadata (to avoid 'field is not indexed' warning)
        """
        metadata = self._metadata
        for name, field_cls in self._fields.items():
            if name not in metadata:
                log.debug("[Catalog] New field registered: {0}".format(name))
                has_changes = True
                metadata[name] = self._get_info(field_cls, name)
            else:
                # If the field was in the catalog but is newly stored
                if 'value' not in metadata[name] and getattr(field_cls, 'stored', False):
                    log.debug("[Catalog] Indexed field is now stored: {0}".format(name))
                    has_changes = True
                    metadata[name] = merge_dicts(
                        metadata[name],
                        self._get_info_stored())
                # If the field was stored in the catalog but is newly indexed
                if 'prefix' not in metadata[name] and getattr(field_cls, 'indexed', False):
                    log.debug("[Catalog] Stored field is now indexed: {0}".format(name))
                    has_changes = True
                    metadata[name] = merge_dicts(
                        metadata[name],
                        self._get_info_indexed())
        if has_changes:
            self._db.set_metadata('metadata', dumps(metadata))
            self._db.commit_transaction()
            self._db.begin_transaction(self.commit_each_transaction)

    #######################################################################
    # API / Public / Transactions
    #######################################################################
    def save_changes(self):
        """Save the last changes to disk.
        """
        if not self._asynchronous:
            raise ValueError("The transactions are synchronous")
        db = self._db
        db.commit_transaction()
        if self.commit_each_transaction:
            db.commit()
        else:
            if self.nb_changes > 200:
                db.commit()
                self.nb_changes = 0
        db.begin_transaction(self.commit_each_transaction)

    def abort_changes(self):

        """Abort the last changes made in memory.
        """
        if not self._asynchronous:
            raise ValueError("The transactions are synchronous")
        db = self._db
        if self.commit_each_transaction:
            db.cancel_transaction()
            db.begin_transaction(self.commit_each_transaction)
        else:
            db.cancel_transaction()
            db.begin_transaction(self.commit_each_transaction)
        self._load_all_internal()

    def close(self):
        if self._db is None:
            log.info("Catalog is already closed")
            return
        if self.read_only:
            self._db.close()
            self._db = None
            return
        if self.commit_each_transaction:
            try:
                self._db.cancel_transaction()
            except Exception:
                log.info("Warning: cannot cancel xapian transaction", exc_info=True)
                self._db.close()
                self._db = None
            else:
                self._db.close()
                self._db = None
        else:
            self._db.commit_transaction()
            self._db.commit()
            self._db.close()
            self._db = None

    #######################################################################
    # API / Public / (Un)Index
    #######################################################################
    def index_document(self, document):
        self.nb_changes += 1
        abspath, term, xdoc = self.get_xdoc_from_document(document)
        self._db.replace_document(term, xdoc)
        log.debug("Indexed : {}".format(abspath))

    def unindex_document(self, abspath):
        """Remove the document that has value stored in its abspath.
           If the document does not exist => no error
        """
        self.nb_changes += 1
        data = _reduce_size(_encode(self._fields['abspath'], abspath))
        if type(data) is bytes:
            data = data.decode("utf-8")
        self._db.delete_document('Q' + data)
        log.debug("Unindexed : {}".format(abspath))

    def get_xdoc_from_document(self, doc_values):
        """Return (abspath, term, xdoc) from the document (resource or values as dict)
        """
        term = None
        metadata = self._metadata
        # Check the input
        if type(doc_values) is not dict:
            raise NotImplementedError('Deprecated: doc_values should be a dict')
        fields = self._fields
        abspath = doc_values['abspath']
        # Make the xapian document
        metadata_modified = False
        xdoc = Document()
        for name, value in doc_values.items():
            if name not in fields:
                warn_not_indexed_nor_stored(name)
            field_cls = fields[name]

            # New field ?
            if name not in metadata:
                info = metadata[name] = self._get_info(field_cls, name)
                metadata_modified = True
            else:
                info = metadata[name]

            # XXX This comment is no longer valid, now the key field is
            #     always abspath with field_cls = String
            # Store the key field with the prefix 'Q'
            # Comment: the key field is indexed twice, but we must do it
            #          one => to index (as the others)
            #          two => to index without split
            #          the problem is that "_encode != _index"
            if name == 'abspath':
                key_value = _reduce_size(_encode(field_cls, value))
                key_value = bytes_to_str(key_value)
                term = 'Q' + key_value
                xdoc.add_term(term)

            # A multilingual value?
            if isinstance(value, dict):
                for language, lang_value in value.items():
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
        # Store metadata ?
        if metadata_modified:
            metadata = self._metadata
            self._db.set_metadata('metadata', dumps(metadata))
        # Ok
        return abspath, term, xdoc

    #######################################################################
    # API / Public / Search
    #######################################################################
    def get_unique_values(self, name):
        """Return all the terms of a given indexed field
        """
        metadata = self._metadata
        # If there is a problem => an empty result
        if name not in metadata:
            warn_not_indexed(name)
            return set()

        # Ok
        prefix = metadata[name]['prefix']
        prefix_len = len(prefix)
        return set([t.term[prefix_len:] for t in self._db.allterms(prefix)])

    #######################################################################
    # API / Private
    #######################################################################
    def _get_info(self, field_cls, name):
        # The key field ?
        if name == 'abspath':
            if not (issubclass(field_cls, String) and
                    field_cls.stored and
                    field_cls.indexed):
                raise ValueError(('the abspath field must be declared as '
                                  'String(stored=True, indexed=True)'))
        # Stored ?
        info = {}
        if getattr(field_cls, 'stored', False):
            info = self._get_info_stored()
        # Indexed ?
        if getattr(field_cls, 'indexed', False):
            info = merge_dicts(info, self._get_info_indexed())
        # Ok
        return info

    def _get_info_stored(self):
        value = self._value_nb
        self._value_nb += 1
        return {'value': value}

    def _get_info_indexed(self):
        prefix = _get_prefix(self._prefix_nb)
        self._prefix_nb += 1
        return {'prefix': prefix}

    def _load_all_internal(self):
        """Load the metadata from the database
        """
        self._value_nb = 0
        self._prefix_nb = 0

        metadata = self._db.get_metadata('metadata')

        if metadata == b'':
            self._metadata = {}
        else:
            try:
                self._metadata = loads(metadata)
            except ValueError:
                # Reload metadata if incompatibility between Python 2 and Python 3
                self._init_all_metadata(has_changes=True)
                metadata = self._db.get_metadata('metadata')
                self._metadata = loads(metadata)

            for name, info in self._metadata.items():
                if 'value' in info:
                    self._value_nb += 1
                if 'prefix' in info:
                    self._prefix_nb += 1

    def _query2xquery(self, query):
        """take a "itools" query and return a "xapian" query
        """
        query_class = type(query)
        fields = self._fields
        metadata = self._metadata

        # All Query
        if query_class is AllQuery:
            return Query('')

        # PhraseQuery, the field must be indexed
        if query_class is PhraseQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError("unexpected '%s'" % type(name))
            # If there is a problem => an empty result
            if name not in metadata:
                warn_not_indexed(name)
                return Query()
            info = metadata[name]
            try:
                prefix = info['prefix']
            except KeyError:
                raise ValueError('the field "%s" must be indexed' % name)
            field_cls = _get_field_cls(name, fields, info)
            return _make_PhraseQuery(field_cls, query.value, prefix)

        # RangeQuery, the field must be stored
        if query_class is RangeQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError("unexpected '%s'" % type(name))
            # If there is a problem => an empty result
            if name not in metadata:
                warn_not_indexed(name)
                return Query()

            info = metadata[name]
            value = info.get('value')
            if value is None:
                raise AttributeError(MSG_NOT_STORED.format(name=name))
            field_cls = _get_field_cls(name, fields, info)
            if field_cls.multiple:
                error = 'range-query not supported on multiple fields'
                raise ValueError(error)

            left = query.left
            if left is not None:
                left = _encode_simple_value(field_cls, left)

            right = query.right
            if right is not None:
                right = _encode_simple_value(field_cls, right)

            # Case 1: no limits, return everything
            if left is None and right is None:
                return Query('')

            # Case 2: left limit only
            if right is None:
                return Query(OP_VALUE_GE, value, left)

            # Case 3: right limit only
            if left is None:
                return Query(OP_VALUE_LE, value, right)

            # Case 4: left and right
            return Query(OP_VALUE_RANGE, value, left, right)

        # StartQuery, the field must be stored
        if query_class is StartQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError("unexpected '%s'" % type(name))
            # If there is a problem => an empty result
            if name not in metadata:
                warn_not_indexed(name)
                return Query()

            info = metadata[name]
            value_nb = info.get('value')
            if value_nb is None:
                raise AttributeError(MSG_NOT_STORED.format(name=name))
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

        # TextQuery, the field must be indexed
        if query_class is TextQuery:
            name = query.name
            if type(name) is not str:
                raise TypeError("unexpected %s for 'name'" % type(name))
            # If there is a problem => an empty result
            if name not in metadata:
                warn_not_indexed(name)
                return Query()

            info = metadata[name]
            field_cls = _get_field_cls(name, fields, info)
            try:
                prefix = info['prefix']
            except KeyError:
                raise ValueError('the field "%s" must be indexed' % name)

            # Remove accents from the value
            value = query.value
            if type(value) is not str:
                raise TypeError("unexpected %s for 'value'" % type(value))
            value = value.translate(TRANSLATE_MAP)

            qp = QueryParser()
            qp.set_database(self._db)
            return qp.parse_query(_encode(field_cls, value), TQ_FLAGS, prefix)

        i2x = self._query2xquery
        # Multiple query with single atom
        if isinstance(query, _MultipleQuery) and len(query.atoms) == 1:
            return i2x(query.atoms[0])

        # And
        if query_class is _AndQuery:
            return Query(OP_AND, [i2x(q) for q in query.atoms])

        # Or
        if query_class is _OrQuery:
            return Query(OP_OR, [i2x(q) for q in query.atoms])

        # Not
        if query_class is NotQuery:
            return Query(OP_AND_NOT, Query(''), i2x(query.query))


def make_catalog(uri, fields):
    """Creates a new and empty catalog in the given uri.

    fields must be a dict. It contains some informations about the
    fields in the database. It must contain at least the abspath key field.

    For example:

      fields = {'abspath': String(stored=True, indexed=True),
                'name': Unicode(indexed=True), ...}
    """
    path = lfs.get_absolute_path(uri)
    db = WritableDatabase(path, DB_BACKEND_GLASS)
    return Catalog(db, fields)


#############
# Private API
def _get_prefix(number):
    """By convention:
    Q is used for the unique Id of a document
    X for a long prefix
    Z for a stemmed word
    """
    magic_letters = 'ABCDEFGHIJKLMNOPRSTUVWY'
    size = len(magic_letters)
    result = 'X' * (number // size)
    return result + magic_letters[number % size]


def _decode_simple_value(field_cls, data):
    """Used to decode values in stored fields.
    """
    # Overload the Integer type, cf _encode_simple_value
    if issubclass(field_cls, Integer):
        return int(sortable_unserialise(data))
    elif issubclass(field_cls, Decimal):
        return decimal(sortable_unserialise(data))
    # A common field or a new field
    return field_cls.decode(data)


def _decode(field_cls, data):
    # Singleton
    if not field_cls.multiple:
        return _decode_simple_value(field_cls, data)

    # Multiple
    try:
        value = loads(data)
    except (ValueError, MemoryError):
        return _decode_simple_value(field_cls, data)
    return [_decode_simple_value(field_cls, a_value) for a_value in value]


# We must overload the normal behaviour (range + optimization)
def _encode_simple_value(field_cls, value):
    # Integers (FIXME this doesn't work with the big integers)
    if issubclass(field_cls, Integer):
        return sortable_serialise(value)
    elif issubclass(field_cls, Decimal):
        # FIXME: We convert decimal->float so we lost precision
        return sortable_serialise(float(value))

    # Datetimes: normalize to UTC, so searching works
    if type(value) is datetime:
        value = value.astimezone(fixed_offset(0))

    # A common field or a new field
    return field_cls.encode(value)


def _encode(field_cls, value):
    """Used to encode values in stored fields.
    """
    # Case 1: Single
    if not field_cls.multiple:
        return _encode_simple_value(field_cls, value)

    # Case 2: Multiple
    value = [_encode_simple_value(field_cls, a_value) for a_value in value]
    return dumps(value)


def _get_field_cls(name, fields, info):
    return fields[name] if (name in fields) else fields[info['from']]


def _reduce_size(data):
    # 'data' must be a byte string

    # If the data is too long, we replace it by its sha1
    # FIXME Visibly a bug in xapian counts twice the \x00 character
    # http://bugs.hforge.org/show_bug.cgi?id=940
    if isinstance(data, str):
        data = data.encode("utf-8")
    if len(data) + data.count(b"\x00") > 220:
        return sha1(data).hexdigest()

    # All OK, we simply return the data
    return data


def _index_cjk(xdoc, value, prefix, termpos):
    """
    Returns the next word and its position in the data. The analysis
    is done with the automaton:

    0 -> 1 [letter or number or cjk]
    0 -> 0 [stop word]
    1 -> 0 [stop word]
    1 -> 2 [letter or number or cjk]
    2 -> 2 [letter or number or cjk]
    2 -> 0 [stop word]
    """
    state = 0
    previous_cjk = ''

    for c in value:
        if is_punctuation(c):
            # Stop word
            if previous_cjk and state == 1:  # CJK not yielded yet
                xdoc.add_posting(prefix + previous_cjk, termpos)
                termpos += 1
            # reset state
            previous_cjk = ''
            state = 0
        else:
            c = c.lower()
            if previous_cjk:
                xdoc.add_posting(prefix + ('%s%s' % (previous_cjk, c)),
                                 termpos)
                termpos += 1
                state = 2
            else:
                state = 1
            previous_cjk = c

    # Last word
    if previous_cjk and state == 1:
        xdoc.add_posting(prefix + previous_cjk, termpos)

    return termpos + 1


def _index_unicode(xdoc, value, prefix, language, termpos,
                   TRANSLATE_MAP=TRANSLATE_MAP):

    value = bytes_to_str(value)
    # Check type
    if type(value) is not str:
        msg = 'The value "%s", field "%s", is not a unicode'
        raise TypeError(msg % (value, prefix))

    # Case 1: Japanese or Chinese
    if language in ['ja', 'zh']:
        return _index_cjk(xdoc, value, prefix, termpos)

    # Case 2: Any other language
    tg = TermGenerator()
    tg.set_document(xdoc)
    tg.set_termpos(termpos - 1)
    # Suppress the accents (FIXME This should be done by the stemmer)
    value = value.translate(TRANSLATE_MAP)
    # XXX With the stemmer, the words are saved twice:
    # with prefix and with Zprefix
    #    tg.set_stemmer(stemmer)

    tg.index_text(value, 1, prefix)
    return tg.get_termpos() + 1


def _index(xdoc, field_cls, value, prefix, language):
    """To index a field it must be split in a sequence of words and
    positions:

      [(word, 1), (word, 2), (word, 3), ...]

    Where <word> will be a <str> value.
    """
    value = bytes_to_str(value)
    is_multiple = (field_cls.multiple
                   and isinstance(value, (tuple, list, set, frozenset)))

    # Case 1: Unicode (a complex split)
    if issubclass(field_cls, Unicode) and value is not None:
        if is_multiple:
            termpos = 1
            for x in value:
                termpos = _index_unicode(xdoc, x, prefix, language, termpos)
        else:
            _index_unicode(xdoc, value, prefix, language, 1)
    # Case 2: multiple
    elif is_multiple:
        for position, data in enumerate(value):
            data = _encode_simple_value(field_cls, data)
            data = _reduce_size(data)
            data = bytes_to_str(data)
            xdoc.add_posting(prefix + data, position + 1)
    # Case 3: singleton
    else:
        data = _encode_simple_value(field_cls, value)
        data = _reduce_size(data)
        data = bytes_to_str(data)
        xdoc.add_posting(prefix + data, 1)


def _make_PhraseQuery(field_cls, value, prefix):
    # Get the words
    # XXX It's too complex (slow), we must use xapian
    #     Problem => _index_cjk
    xdoc = Document()
    # XXX Language = 'en' by default
    _index(xdoc, field_cls, value, prefix, 'en')
    words = []
    for term_list_item in xdoc:
        term = term_list_item.term
        for termpos in term_list_item.positer:
            words.append((termpos, term))
    words.sort()
    words = [word[1] for word in words]

    # Make the query
    return Query(OP_PHRASE, words)


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
    for name, value in kw.items():
        # If name is a field not yet indexed, return nothing
        if name not in metadata:
            warn_not_indexed(name)
            return Query()

        # Ok
        info = metadata[name]
        prefix = info['prefix']
        field_cls = _get_field_cls(name, fields, info)
        query = _make_PhraseQuery(field_cls, value, prefix)
        xqueries.append(query)

    return Query(OP_AND, xqueries)
