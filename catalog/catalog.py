# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
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
This module implements a storage for documents, where a document is a
set of fields, each field has a value (a unicode string) and is identified
with a number. Documents are also identified with numbers.

So, the data structure is:

  - documents: {<doc number>: Document}
  - n_documents: int

The "n_documents" variable is a counter used to generate unique ids for
the documents.

This data structure is serialized to two files, "documents" and "index".

File format
===========

The index file (index)
----------------------

The index file is made of fixed length blocks of 8 bytes each:

  - pointer to the documents file [link]
  - size of the block in the documents file [uint32]

Each block represents a document: the first block is for the document
number 0, the second block is for the document number 1, and so on.

The documents file (documents)
------------------------------

Within the documents file each document is stored in variable length blocks,
one after another. And a document is made of its fields:

  - field number, is stored [byte]
  - field value

The first byte is split in two parts, the highest weight bit tells whether
the field is stored or not, the lower 7 bits tell are the field number. For
example:

  1 0000010 (field number: 3, is stored: false)

The structure of the field value depends on whether the field is stored or
not. If it is stored it will be an string:

  - field value [string]

If it is not it will be a list of terms:

  - n_terms [vint]
  - term 0 [string]
  ...
  - term n [string]

"""

# Import from the Standard Library
from copy import deepcopy
from operator import itemgetter
from os import listdir, remove
from os.path import exists, getmtime

# Import from itools
from itools.uri import get_absolute_reference
from itools.vfs import vfs, READ_WRITE, APPEND
from base import CatalogAware
from index import Index, VERSION, ZERO
import fields
from queries import EqQuery, AndQuery, PhraseQuery
from io import (decode_byte, encode_byte, decode_link, encode_link,
                decode_string, encode_string, decode_uint32, encode_uint32,
                decode_vint, encode_vint, NULL)



class Field(object):

    __slots__ = ['number', 'name', 'type', 'is_indexed', 'is_stored']


    def __init__(self, number, name, type, is_indexed, is_stored):
        self.number = number
        self.name = name
        self.type = type
        self.is_indexed = is_indexed
        self.is_stored = is_stored



class Document(object):

    __slots__ = ['__number__', 'fields', 'field_numbers']

    def __init__(self, n, *args):
        self.__number__ = n
        self.fields = {}
        for field_number, value in enumerate(args):
            self.fields[field_number] = value
        self.field_numbers = None


    def __getattr__(self, name):
        field_numbers = self.field_numbers
        if field_numbers is None:
            raise AttributeError
        if name not in field_numbers:
            raise AttributeError, "the field '%s' is not defined" % name
        n = field_numbers[name]
        return self.fields.get(n)



class SearchResults(object):

    __slots__ = ['results', 'catalog']


    def __init__(self, results, catalog):
        self.results = results
        self.catalog = catalog


    def get_n_documents(self):
        """Returns the number of documents found."""
        return len(self.results)


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
        # Iterate on sorted by weight in decrease order
        get_document = self.catalog.get_document
        field_numbers = self.catalog.field_numbers

        if sort_by is None:
            # Sort by weight
            doc_numbers = [ x[0] for x in sorted(self.results.iteritems(),
                                                 key=itemgetter(1),
                                                 reverse=True) ]
        else:
            # Just get the document keys unsorted (we will sort later)
            doc_numbers = self.results.keys()

        # Load the documents
        documents = []
        for doc_number in self.results:
            document = get_document(doc_number)
            document.field_numbers = field_numbers
            documents.append(document)

        # Sort by something
        if sort_by is not None:
            if isinstance(sort_by, list):
                sort_by = [ field_numbers[x] for x in sort_by ]
                def key(doc, sort_by=sort_by):
                    return tuple([ doc.fields.get(x) for x in sort_by ])
            else:
                sort_by = field_numbers[sort_by]
                def key(doc, sort_by=sort_by):
                    return doc.fields.get(sort_by)

            documents.sort(key=key, reverse=reverse)

        # Batch
        if size > 0:
            return documents[start:start+size]
        if start > 0:
            return documents[start:]

        return documents



class Catalog(object):

    class_version = '20060708'

    __slots__ = [
        'uri', 'timestamp', 'has_changed',
        'fields', 'field_numbers', 'indexes',
        'documents', 'n_documents', 'added_documents', 'removed_documents']

    #######################################################################
    # API / Public
    #######################################################################

    def __init__(self, ref):
        self.uri = get_absolute_reference(ref)
        self.has_changed = False
        self.fields = []
        self.field_numbers = {}
        self.indexes = []
        # Load
        base = vfs.open(self.uri)
        for line in base.open('data/fields').readlines():
            line = line.strip()
            if not line:
                continue
            number, name, type, is_indexed, is_stored = line.split('#')
            number = int(number)
            is_indexed = bool(int(is_indexed))
            is_stored = bool(int(is_stored))
            cls = fields.get_field(type)
            field = cls(name, is_indexed=is_indexed, is_stored=is_stored)
            field.number = number
            self.fields.append(field)
            self.field_numbers[name] = number
        # Initialize the indexes
        data = self.uri.resolve2('data')
        for field in self.fields:
            if field.is_indexed:
                self.indexes.append(Index(data, field.number))
            else:
                self.indexes.append(None)
        # Initialize the documents
        base = vfs.open(data)
        self.documents = {}
        index_file = base.open('documents_index')
        try:
            index_file.seek(0, 2)
            self.n_documents = index_file.tell() / 8
        finally:
            index_file.close()
        self.added_documents = []
        self.removed_documents = []

        self.timestamp = vfs.get_mtime(self.uri)


    #######################################################################
    # Transactions part
    def save_changes(self):
        """Save the last changes to disk.
        """
        # Start
        path = self.uri.path
        state = str(path.resolve2('state'))
        open(state, 'w').write('START\n')

        # Save
        try:
            for index in self.indexes:
                if index is not None:
                    index.save_state()
            self.save_documents()
        except:
            # Restore from backup
            src = str(path.resolve2('data.bak'))
            dst = str(path.resolve2('data'))
            for name in listdir(src):
                src_file = src + '/' + name
                dst_file = dst + '/' + name
                if getmtime(src_file) < getmtime(dst_file):
                    data = open(src_file).read()
                    open(dst_file, 'w').write(data)
            for name in listdir(dst):
                if not exists(src + '/' + name):
                    remove(dst + '/' + name)
            # Reload the catalog
            self.__init__(self.uri)
            # We are done
            open(state, 'w').write('OK\n')
            # Forward error
            raise

        # The transaction was successful
        open(state, 'w').write('END\n')

        # Backup
        src = str(path.resolve2('data'))
        dst = str(path.resolve2('data.bak'))
        for name in listdir(src):
            src_file = src + '/' + name
            dst_file = dst + '/' + name
            if not exists(dst_file) or getmtime(src_file) > getmtime(dst_file):
                data = open(src_file).read()
                open(dst_file, 'w').write(data)

        # We are done
        open(state, 'w').write('OK\n')

        # Update the timestamp
        self.timestamp = vfs.get_mtime(self.uri)


    def abort_changes(self):
        """Abort the last changes made in memory.
        """
        # Indexes
        for index in self.indexes:
            if index is not None:
                index.abort()


    #######################################################################
    # Documents management
    def index_document(self, document):
        """Add a new document.
        """
        # Check the input
        if not isinstance(document, CatalogAware):
            raise ValueError, 'the document must be a CatalogAware object'

        # Extract the definition and values (do it first, because it may
        # fail).
        fields = document.get_catalog_fields()
        values = document.get_catalog_values()

        # Create new indexes if needed
        new_fields = [ x for x in fields if x.name not in self.field_numbers ]
        if new_fields:
            base = self.uri.resolve2('data')
            folder = vfs.open(base)
            file = folder.open('fields', APPEND)
            try:
                i = len(self.fields)
                for field in new_fields:
                    field = deepcopy(field)
                    field.number = i
                    # Update metadata file
                    file.write('%d#%s#%s#%d#%d\n' % (i, field.name,
                        field.type, field.is_indexed, field.is_stored))
                    # Make index files
                    folder.make_file('%d_docs' % i)
                    tree = folder.make_file('%d_tree' % i)
                    try:
                        tree.write(''.join([VERSION, ZERO, NULL, NULL]))
                    finally:
                        tree.close()
                    # Data Structure
                    self.fields.append(field)
                    self.field_numbers[field.name] = i
                    if field.is_indexed:
                        self.indexes.append((Index(base, i)))
                    else:
                        self.indexes.append(None)
                    # Next
                    i += 1
            finally:
                file.close()

        # Set the catalog as dirty
        self.has_changed = True
        # Create the document to index
        doc_number = self.n_documents
        catalog_document = Document(doc_number)

        # Index
        get = values.get
        for field in fields:
            # Add number attribute
            field.number = self.field_numbers[field.name]

            # Extract the field value from the document
            value = get(field.name)

            # If value is None, don't go further
            if value is None:
                continue

            # Update the Inverted Index
            if field.is_indexed:
                index = self.indexes[field.number]
                # Tokenize
                terms = set()
                for word, position in field.split(value):
                    terms.add(word)
                    # Update the inverted index
                    index.index_term(word, doc_number, position)

            # Update the Document
            if field.is_stored:
                # Stored
                # XXX Coerce
                #if isinstance(value, list):
                #    value = u' '.join(value)
                catalog_document.fields[field.number] = value
            else:
                # Not Stored
                catalog_document.fields[field.number] = list(terms)

        # Add the Document
        # TODO document values must be deserialized
        doc_n = self.n_documents
        self.n_documents += 1
        self.documents[doc_n] = catalog_document
        self.added_documents.append(doc_n)
        return doc_n


    def unindex_document(self, value):
        """Remove the document 'value'. Value is the first Field.
        """
        query = EqQuery(self.fields[0].name, value)
        for document in self.search(query).get_documents():
            self._unindex_document(document.__number__)


    def search(self, query=None, **kw):
        """Launch a search in the catalog.
        """
        # Build the query if it is passed through keyword parameters
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(PhraseQuery(key, value))

                query = AndQuery(*atoms)
            else:
                results = {}
                for doc_n in range(self.n_documents):
                    try:
                        document = self.get_document(doc_n)
                    except LookupError:
                        continue
                    results[doc_n] = 1
                return SearchResults(results, self)
        # Search
        results = query.search(self)
        return SearchResults(results, self)


    #######################################################################
    # API / Private
    #######################################################################
    def save_documents(self):
        base = vfs.open(self.uri)
        index_file = base.open('data/documents_index', READ_WRITE)
        docs_file = base.open('data/documents', APPEND)
        try:
            # Removed documents
            for doc_n in self.removed_documents:
                index_file.seek(doc_n * 8)
                index_file.write(NULL)
                index_file.write(encode_uint32(0))
                # Update data structure
                if doc_n in self.documents:
                    del self.documents[doc_n]
            # Added documents
            index_file.seek(0, 2)
            for doc_n in self.added_documents:
                document = self.documents[doc_n]
                # Append the new document to the documents file
                buffer = []
                append = buffer.append
                keys = document.fields.keys()
                keys.sort()
                for field_number in keys:
                    field = self.fields[field_number]
                    value = document.fields[field_number]
                    # The first byte keeps the field number (0-127) and
                    # a bit that will tell us wether the field is stored
                    # or not.
                    if field.is_stored:
                        # Stored
                        append(encode_byte(field_number | 128))
                        # "value" must be a unicode string
                        value = field.encode(value)
                        append(encode_string(value))
                    else:
                        # Not Stored
                        append(encode_byte(field_number))
                        # "value" must be a list of unicode strings
                        append(encode_vint(len(value)))
                        for x in value:
                            append(encode_string(x))
                position = docs_file.tell()
                data = ''.join(buffer)
                docs_file.write(data)
                # Update the index file
                size = len(data)
                index_file.write(encode_link(position) + encode_uint32(size))
            # Clean the data structure
            self.added_documents = []
            self.removed_documents = []
        finally:
            index_file.close()
            docs_file.close()


    def get_analyser(self, name):
        field_number = self.field_numbers[name]
        return self.fields[field_number]


    def get_index(self, name):
        field_numbers = self.field_numbers
        # The field may be defined by objects not yet indexed
        if name not in field_numbers:
            return None
        # Get the index
        number = field_numbers[name]
        index = self.indexes[number]
        # Check the field is indexed
        if index is None:
            raise ValueError, 'the field "%s" is not indexed' % name

        return index


    def get_document(self, doc_n):
        if doc_n not in self.documents:
            document = Document(doc_n)
            # Load document from the documents file
            base = vfs.open(self.uri)
            index_file = base.open('data/documents_index')
            docs_file = base.open('data/documents')
            try:
                # Read the index entry
                index_file.seek(doc_n * 8)
                data = index_file.read(8)
                pointer = decode_link(data[0:4])
                if pointer is None:
                    raise LookupError, 'document "%d" is not indexed' % doc_n
                size = decode_uint32(data[4:8])
                # Read the document data
                docs_file.seek(pointer)
                data = docs_file.read(size)
                # Load the document data
                while data:
                    first_byte = decode_byte(data[0])
                    field_n = first_byte & 127
                    if first_byte & 128:
                        # Stored
                        value, data = decode_string(data[1:])
                        field = self.fields[field_n]
                        value = field.decode(value)
                    else:
                        # Not Stored
                        n_terms, data = decode_vint(data[1:])
                        value = []
                        while n_terms > 0:
                            x, data = decode_string(data)
                            value.append(x)
                            n_terms -= 1
                    document.fields[field_n] = value
                self.documents[doc_n] = document
            finally:
                index_file.close()
                docs_file.close()

        return self.documents[doc_n]


    def _unindex_document(self, doc_number):
        self.has_changed = True
        # Update the indexes
        document = self.get_document(doc_number)
        for field in self.fields:
            # Check the field is indexed
            if not field.is_indexed:
                continue
            # Check the document is indexed for that field
            value = document.fields.get(field.number)
            if value is None:
                continue
            # If the field is stored, find out the terms to unindex
            if field.is_stored:
                terms = [ term for term, position in field.split(value) ]
                terms = set(terms)
            else:
                terms = value
            # Unindex
            index = self.indexes[field.number]
            for term in terms:
                index.unindex_term(term, doc_number)

        # Update the documents
        if doc_number in self.added_documents:
            self.added_documents.remove(doc_number)
        self.removed_documents.append(doc_number)



def make_catalog(uri):
    """Creates a new and empty catalog in the given uri.
    """
    uri = get_absolute_reference(uri)
    vfs.make_folder(uri)
    base = vfs.open(uri)

    # Write the metadata file
    base.make_folder('data')
    file = base.make_file('data/fields')
    # Create the documents
    base.make_file('data/documents')
    base.make_file('data/documents_index')
    # Create the backup data
    base.copy('data', 'data.bak')
    file = base.make_file('state')
    try:
        file.write('OK\n')
    finally:
        file.close()

    return Catalog(uri)



def recover(uri):
    raise NotImplementedError
