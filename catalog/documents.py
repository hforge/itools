# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the future
from __future__ import with_statement

# Import from itools
from itools import vfs
from IO import (decode_byte, encode_byte, decode_link, encode_link,
                decode_string, encode_string, decode_uint32, encode_uint32,
                decode_vint, encode_vint, NULL)

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



class Documents(object):

    __slots__ = ['uri', 'documents', 'n_documents',
                 'added_documents', 'removed_documents']


    def __init__(self, uri):
        self.uri = uri

        base = vfs.open(uri)
        with base.open('documents_index') as index_file:
            self.documents = {}
            index_file.seek(0, 2)
            self.n_documents = index_file.tell() / 8
        # Nothing changed yet
        self.added_documents = []
        self.removed_documents = []


    def save_state(self):
        base = vfs.open(self.uri)
        index_file = base.open('documents_index')
        docs_file = base.open('documents')
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
                    value = document.fields[field_number]
                    # The first byte keeps the field number (0-127) and
                    # a bit that will tell us wether the field is stored
                    # or not. (XXX This information may be passed from
                    # the outside).
                    if isinstance(value, unicode):
                        # Stored
                        append(encode_byte(field_number | 128))
                        # "value" must be a unicode string
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


    ######################################################################
    # API
    ######################################################################
    def index_document(self, document):
        doc_n = self.n_documents
        self.n_documents += 1
        self.documents[doc_n] = document
        self.added_documents.append(doc_n)
        return doc_n


    def unindex_document(self, doc_n):
        if doc_n in self.added_documents:
            self.added_documents.remove(doc_n)
        self.removed_documents.append(doc_n)


    def get_document(self, doc_n):
        if doc_n not in self.documents:
            document = Document(doc_n)
            # Load document from the documents file
            base = vfs.open(self.uri)
            index_file = base.open('index', 'r')
            docs_file = base.open('documents', 'r')
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
                    if first_byte & 128:
                        # Stored
                        value, data = decode_string(data[1:])
                    else:
                        # Not Stored
                        n_terms, data = decode_vint(data[1:])
                        value = []
                        while n_terms > 0:
                            x, data = decode_string(data)
                            value.append(x)
                            n_terms -= 1
                    field_n = first_byte & 127
                    document.fields[field_n] = value
                self.documents[doc_n] = document
            finally:
                index_file.close()
                docs_file.close()

        return self.documents[doc_n]

