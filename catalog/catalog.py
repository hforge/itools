# -*- coding: ISO-8859-1 -*-
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

# Import from the Standard Library
from operator import itemgetter

# Import from itools
from itools import vfs
from itools.handlers.base import Handler
from IO import (encode_byte, encode_character, encode_link, encode_string,
                encode_uint32, encode_version)
from analysers import get_analyser
import queries


class Field(object):

    __slots__ = ['number', 'name', 'type', 'is_indexed', 'is_stored']


    def __init__(self, number, name, type, is_indexed, is_stored):
        self.number = number
        self.name = name
        self.type = type
        self.is_indexed = is_indexed
        self.is_stored = is_stored










class Document(object):
    
    __slots__ = ['fields']


    def __init__(self):
        self.fields = []



class Catalog(Handler):

    class_version = '20060707'

    __slots__ = ['uri', 'timestamp', 'fields', 'field_numbers', 'indexes',
                 'document_number', 'documents', 'added_documents',
                 'removed_documents']


    def new(self, fields=[]):
        self.fields = []
        self.field_numbers = {}
        self.indexes = []
        for number, field in enumerate(fields):
            name, type, is_indexed, is_stored = field
            # Keep field metadata
            field = Field(number, name, type, is_indexed, is_stored)
            self.fields.append(field)
            # Keep a mapping from field name to field number
            self.field_numbers[name] = number
            # Initialize index
            if is_indexed:
                self.indexes.append(Index())
            else:
                self.indexes.append(None)
        # Initialize documents
        self.document_number = 0
        self.documents = []
        self.added_documents = {}
        self.removed_documents = []


    def save_state(self):
        # Define helpful variables
        version = encode_version(self.class_version)
        zero = encode_uint32(0)
        null = encode_link(None)

        # Initialize
        base = self.uri
        if not vfs.exists(base):
            # Make and open the folder
            vfs.make_folder(base)
            base = vfs.open(base)
            # Initialize documents
            base.make_file('documents')
            base.make_file('documents_index')
            with base.open('documents_index') as documents_index:
                documents_index.write(zero)
            # Initialize inverted indexes
            tree = ''.join([version, zero, null, null])
            docs = ''.join([version, zero, null])
            for field in self.fields:
                # The tree
                base.make_file('%d_index_tree' % field.number)
                with base.open('%d_index_tree' % field.number) as file:
                    file.write(tree)
                # The documents
                base.make_file('%d_index_docs' % field.number)
                with base.open('%d_index_docs' % field.number) as file:
                    file.write(docs)
        else:
            base = vfs.open(base)

        # Save changes
        fields = self.fields
        # Documents
        index = base.open('documents_index')
        docs = base.open('documents')
        try:
            # Remove
            for doc_number in self.removed_documents:
                index.seek(4 + doc_number * 4)
                index.write(null)
            # Add
            index.seek(0, 2)
            docs.seek(0, 2)
            for document in self.added_documents.values():
                index.write(encode_link(docs.tell()))
                data = []
                for field in fields:
                    value = document.fields[field.number]
                    if value is None:
                        continue
                    data.append(encode_byte(field.number))
                    if field.is_stored:
                        data.append(encode_string(value))
                    else:
                        analyser = get_analyser(field.type)
                        terms = [ x[0] for x in analyser(value) ]
                        terms = list(set(terms))
                        terms.sort()
                        data.append(encode_string(' '.join(terms)))
                docs.write(''.join(data))
            # Clean data structures
            self.removed_documents = []
            self.added_documents = {}
        finally:
            index.close()
            docs.close()
        # Indexes
        for field in self.fields:
            if not field.is_indexed:
                continue
            index = self.indexes[field.number]
            tree = base.open('%d_index_tree' % field.number)
            docs = base.open('%d_index_docs' % field.number)
            try:
                # Remove
                for term in index.removed_terms:
                    pass
                # Add
                for term in index.added_terms:
                    pass
                # Clean data structures
                # XXX {<term>: set(<doc number>, ..)}
                index.removed_terms = {}
                # XXX {<term>: {<doc number>: [<position>, ..., <position>]}
                index.added_terms = {}
            finally:
                tree.close()
                docs.close()


    #########################################################################
    # Private API
    #########################################################################
    def get_new_document_number(self):
        document_number = self.document_number
        self.document_number += 1
        return document_number


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


    #########################################################################
    # Public API
    #########################################################################
    def index_document(self, document):
        # Create the document
        doc_number = self.get_new_document_number()
        catalog_document = Document()
        self.added_documents[doc_number] = catalog_document

        # Index
        for field in self.fields:
            # Extract the field value from the document
            if isinstance(document, dict):
                value = document.get(field.name)
            else:
                value = getattr(document, field.name, None)

            # If value is None, don't go further
            if value is None:
                catalog_document.fields.append(None)
                continue

            # Update the Inverted Index
            if field.is_indexed:
                index = self.indexes[field.number]
                # Tokenize
                terms = set()
                analyser = get_analyser(field.type)
                for word, position in analyser(value):
                    terms.add(word)
                    # Update the inverted index
                    index.index_term(word, doc_number, position)

            # Update the Document
            if field.is_stored:
                # XXX Coerce lists
                if isinstance(value, list):
                    value = ' '.join(value)
                catalog_document.fields.append(value)
            else:
                # Update the forward index (un-index)
                catalog_document.fields.append(list(terms))

        return doc_number


    def unindex_document(self, doc_number):
        if doc_number in self.added_documents:
            document = self.added_documents.pop(doc_number)
        else:
            document = self.documents[doc_number]
            self.removed_documents.append(doc_number)

        for field in self.fields:
            # Check the field is indexed
            if not field.is_indexed:
                continue
            # Check the document is indexed for that field
            terms = document.fields[field.number]
            if terms is None:
                continue
            # If the field is stored, find out the terms to unindex
            if field.is_stored:
                analyser = get_analyser(field.type)
                terms = [ term for term, position in analyser(terms) ]
                terms = set(terms)
            # Unindex
            index = self.indexes[field.number]
            for term in terms:
                index.unindex_term(term, doc_number)


    def _search(self, query=None, **kw):
        # Build the query if it is passed through keyword parameters
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(queries.Phrase(key, value))

                query = queries.And(*atoms)
            else:
                raise ValueError, "expected a query"
        # Search
        return query.search(self)


    def how_many(self, query=None, **kw):
        """
        Returns the number of documents found.
        """
        return len(self._search(query, **kw))


    def search(self, query=None, **kw):
        # Search
        documents = self._search(query, **kw)
        # Build the document objects
        fields = self.fields
        # iterate on sorted by weight in decrease order
        for document in sorted(documents.iteritems(), key=itemgetter(1),
                               reverse=True):
            doc_number, weight = document
            # Load the IDocument
            if doc_number in self.added_documents:
                yield self.added_documents[doc_number]
            else:
                yield self.documents[doc_number]


