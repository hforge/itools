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
from hashlib import sha1
from marshal import dumps, loads

# Import from xapian
from xapian import sortable_serialise, sortable_unserialise
from xapian import Document, Query, TermGenerator

# Import from itools
from itools.datatypes import Integer, Unicode
from itools.i18n import is_punctuation



# Constants
OP_AND = Query.OP_AND
OP_PHRASE = Query.OP_PHRASE



def _decode_simple_value(field_cls, data):
    """Used to decode values in stored fields.
    """
    # Overload the Integer type, cf _encode_simple_value
    if issubclass(field_cls, Integer):
        if data == '':
            return None
        return int(sortable_unserialise(data))
    # A common field or a new field
    return field_cls.decode(data)



def _decode(field_cls, data):
    if field_cls.multiple:
        try:
            value = loads(data)
        except (ValueError, MemoryError):
            return _decode_simple_value(field_cls, data)
        return [ _decode_simple_value(field_cls, a_value)
                 for a_value in value ]
    else:
        return _decode_simple_value(field_cls, data)



# We must overload the normal behaviour (range + optimization)
def _encode_simple_value(field_cls, value):
    # Overload the Integer type
    # XXX warning: this doesn't work with the big integers!
    if issubclass(field_cls, Integer):
        return sortable_serialise(value)
    # A common field or a new field
    return field_cls.encode(value)



def _encode(field_cls, value):
    """Used to encode values in stored fields.
    """

    is_multiple = (
        field_cls.multiple
        and isinstance(value, (tuple, list, set, frozenset)))

    if is_multiple:
        value = [ _encode_simple_value(field_cls, a_value)
                  for a_value in value ]
        return dumps(value)
    else:
        return _encode_simple_value(field_cls, value)



def _get_field_cls(name, fields, info):
    return fields[name] if (name in fields) else fields[info['from']]



def _reduce_size(data):
    # If the data are too long, we replace it by its sha1
    if len(data) > 240:
        if isinstance(data, unicode):
            data = data.encode('utf-8')
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
    lexeme = previous_cjk = u''

    for c in value:
        if is_punctuation(c):
            # Stop word
            if previous_cjk and state == 1: # CJK not yielded yet
                xdoc.add_posting(prefix + previous_cjk, termpos)
                termpos += 1
            # reset state
            lexeme = u''
            previous_cjk = u''
            state = 0
        else:
            c = c.lower()
            if previous_cjk:
                xdoc.add_posting(prefix + (u'%s%s' % (previous_cjk, c)),
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



def _index_unicode(xdoc, value, prefix, language, termpos):
    # Japanese or Chinese
    if language in ['ja', 'zh']:
        return _index_cjk(xdoc, value, prefix, termpos)

    # Any other language
    tg = TermGenerator()
    tg.set_document(xdoc)
    tg.set_termpos(termpos - 1)
    # XXX The words are saved twice: with prefix and with Zprefix
    #tg.set_stemmer(stemmer)
    tg.index_text(value, 1, prefix)
    return tg.get_termpos() + 1



def _index(xdoc, field_cls, value, prefix, language):
    """To index a field it must be split in a sequence of words and
    positions:

      [(word, 1), (word, 2), (word, 3), ...]

    Where <word> will be a <str> value.
    """
    is_multiple = (
        field_cls.multiple
        and isinstance(value, (tuple, list, set, frozenset)))

    # Unicode: a complex split
    if issubclass(field_cls, Unicode):
        if is_multiple:
            termpos = 1
            for x in value:
                termpos = _index_unicode(xdoc, x, prefix, language, termpos)
        else:
            _index_unicode(xdoc, value, prefix, language, 1)
    # An other type: too easy
    else:
        if is_multiple:
            for position, x in enumerate(value):
                data = _reduce_size(_encode(field_cls, x))
                xdoc.add_posting(prefix + data, position + 1)
        else:
            data = _reduce_size(_encode(field_cls, value))
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
    words = [ word[1] for word in words ]

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
    for name, value in kw.iteritems():
        # If name is a field not yet indexed, return nothing
        if name not in metadata:
            return Query()

        # Ok
        info = metadata[name]
        prefix = info['prefix']
        field_cls = _get_field_cls(name, fields, info)
        query = _make_PhraseQuery(field_cls, value, prefix)
        xqueries.append(query)

    return Query(OP_AND, xqueries)



def split_unicode(text, language='en'):
    xdoc = Document()
    _index_unicode(xdoc, text, '', language, 1)
    words = []
    for term_list_item in xdoc:
        term = unicode(term_list_item.term, 'utf-8')
        for termpos in term_list_item.positer:
            words.append((termpos, term))
    words.sort()
    return [ word[1] for word in words ]

