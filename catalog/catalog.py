# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

"""
This module implements an storage for documents, where a document is a
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

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from operator import itemgetter
from subprocess import call

# Import from itools
from itools.uri import get_absolute_reference
from itools import vfs
from index import Index, VERSION, ZERO
import fields
import queries
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
        """
        Returns the documents for the search, sorted by weight.

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
                    return tuple([ doc.fields[x] for x in sort_by ])
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


    def __init__(self, ref):
        self.uri = get_absolute_reference(ref)
        self.has_changed = False
        self.fields = []
        self.field_numbers = {}
        self.indexes = []
        # Load
        base = vfs.open(self.uri)
        with base.open('fields') as file:
            for line in file.readlines():
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
        with base.open('documents_index') as index_file:
            index_file.seek(0, 2)
            self.n_documents = index_file.tell() / 8
        self.added_documents = []
        self.removed_documents = []

        self.timestamp = vfs.get_mtime(self.uri)


    #########################################################################
    # API / Transactions
    #########################################################################
    def save_documents(self):
        base = vfs.open(self.uri)
        index_file = base.open('data/documents_index')
        docs_file = base.open('data/documents')
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
            docs_file.seek(0, 2)
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


    def commit(self):
        # Start
        state = str(self.uri.path.resolve2('state'))
        open(state, 'w').write('START\n')

        # Save
        try:
            for index in self.indexes:
                if index is not None:
                    index.save_state()
            self.save_documents()
        except:
            # Restore from backup
            src = str(self.uri.path.resolve2('data.bak'))
            dst = str(self.uri.path.resolve2('data/'))
            call(['rsync', '-a', '--delete', src, dst])
            # Reload the catalog
            self.__init__(self.uri)
            # We are done
            open(state, 'w').write('OK\n')
            # Forward error
            raise

        # The transaction was successful
        open(state, 'w').write('END\n')

        # Backup
        src = str(self.uri.path.resolve2('data/'))
        dst = str(self.uri.path.resolve2('data.bak'))
        call(['rsync', '-a', '--delete', src, dst])

        # We are done
        open(state, 'w').write('OK\n')

        # Update the timestamp
        self.timestamp = vfs.get_mtime(self.uri)


    def abort(self):
        # Indexes
        for index in self.indexes:
            if index is not None:
                index.abort()

        # Documents
        for doc_n in self.added_documents:
            del self.documents[doc_n]
            self.n_documents -= 1
        self.added_documents = []
        self.removed_documents = []


    #########################################################################
    # API / Index & Search
    #########################################################################
    def get_analyser(self, name):
        field_number = self.field_numbers[name]
        return self.fields[field_number]


    def get_index(self, name):
        field_numbers = self.field_numbers
        # Check the field exists
        if name not in field_numbers:
            raise ValueError, 'the field "%s" is not defined' % name
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
            index_file = base.open('data/documents_index', 'r')
            docs_file = base.open('data/documents', 'r')
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


    def index_document(self, document):
        self.has_changed = True
        # Create the document to index
        doc_number = self.n_documents
        catalog_document = Document(doc_number)

        # Define the function to get values from the document
        if isinstance(document, dict):
            getter = document.get
        else:
            getter = lambda x: getattr(document, x, None)

        # Index
        for field in self.fields:
            # Extract the field value from the document
            value = getter(field.name)

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


    def unindex_document(self, doc_number):
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


    def search(self, query=None, **kw):
        # Build the query if it is passed through keyword parameters
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(queries.Phrase(key, value))

                query = queries.And(*atoms)
            else:
                documents = self.documents
                results = {}
                for doc_n in range(documents.n_documents):
                    try:
                        document = documents.get_document(doc_n)
                    except LookupError:
                        continue
                    results[doc_n] = 1
                return SearchResults(results, documents, self.field_numbers)
        # Search
        results = query.search(self)
        return SearchResults(results, self)



def make_catalog(uri, *fields):
    """
    Creates a new catalog in the given uri.
    """
    uri = get_absolute_reference(uri)
    vfs.make_folder(uri)
    base = vfs.open(uri)

    base.make_folder('data')

    # Create the indexes
    metadata = []
    for i, field in enumerate(fields):
        # The metadata file
        metadata.append('%d#%s#%s#%d#%d\n' % (i, field.name,
                                              field.type,
                                              field.is_indexed,
                                              field.is_stored))
        # Create the index file
        base.make_file('data/%d_docs' % i)
        with base.make_file('data/%d_tree' % i) as file:
            file.write(''.join([VERSION, ZERO, NULL, NULL]))

    # Write the metadata file
    with base.make_file('fields') as file:
        file.write(''.join(metadata))

    # Create the documents
    base.make_file('data/documents')
    base.make_file('data/documents_index')

    # Create the backup data
    base.copy('data', 'data.bak')
    with base.make_file('state') as file:
        file.write('OK\n')

    return Catalog(uri)



def recover(uri):
    raise NotImplementedError
