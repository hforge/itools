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

# Import from the Standard Library
from operator import itemgetter

# Import from itools
from itools.handlers.Handler import Handler
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



class Tree(object):

    __slots__ = ['children', 'documents']


    def __init__(self):
        # {<key>: Tree}
        self.children = {}
        # {<doc number>: [<position>, ..., <position>]}
        self.documents = {}


    def search_word(self, word):
        if word:
            if self.children is None:
                self.load_children()

            prefix, suffix = word[0], word[1:]
            subtree = self.children.get(prefix, None)
            if subtree is None:
                return {}
            else:
                return subtree.search_word(suffix)
        else:
            if self.documents is None:
                self.load_documents()

            return self.documents.copy()



class Index(object):
    
    __slots__ = ['root', 'added_terms', 'removed_terms']


    def __init__(self):
        self.root = Tree()
        # {<term>: {<doc number>: [<position>, ..., <position>]}
        self.added_terms = {}
        # {<term>: set(<doc number>, ..)}
        self.removed_terms = {}


    def index_term(self, term, doc_number, position):
        # Removed terms
        if term in self.removed_terms:
            if doc_number in self.removed_terms[term]:
                del self.removed_terms[term][doc_number]
        # Added terms
        documents = self.added_terms.setdefault(term, {})
        positions = documents.setdefault(doc_number, set())
        positions.add(position)


    def unindex_term(self, term, doc_number):
        # Added terms
        added_terms = self.added_terms
        if term in added_terms and doc_number in added_terms[term]:
            del self.added_terms[term][doc_number]
            return

        # Removed terms
        documents = self.removed_terms.setdefault(term, set())
        documents.add(doc_number)


    def search_word(self, word):
        # Open resources
##        self.tree_handler.resource.open()
##        self.docs_handler.resource.open()

        documents = self.root.search_word(word)
        # Remove documents
        if word in self.removed_terms:
            for doc_number in self.removed_terms[word]:
                if doc_number in documents:
                    del documents[doc_number]
        # Add documents
        if word in self.added_terms:
            for doc_number, positions in self.added_terms[word].items():
                if doc_number in documents:
                    # XXX We ever reach this case?
                    documents[doc_number] |= positions
                else:
                    documents[doc_number] = positions

        # Close resources
##        self.tree_handler.resource.close()
##        self.docs_handler.resource.close()

        return documents





class Document(object):
    
    __slots__ = ['fields']


    def __init__(self):
        self.fields = []



class Catalog(Handler):

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


