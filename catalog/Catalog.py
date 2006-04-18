# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import warnings

# Import from itools
from itools.handlers.Folder import Folder
from itools.handlers.Text import Text
from analysers import get_analyser
from IDocument import IDocument, IndexedField
from IIndex import IIndex
import queries


class Field(object):
    def __init__(self, number, name, type, is_indexed, is_stored):
        self.number = number
        self.name = name
        self.type = type
        self.is_indexed = is_indexed
        self.is_stored = is_stored


class Fields(Text):

    def get_skeleton(self, fields=[]):
        skeleton = ''
        for number, field in enumerate(fields):
            name, type, is_indexed, is_stored = field
            skeleton += '%d#%s#%s#%d#%d\n' % (number, name, type,
                                              is_indexed, is_stored)
        return skeleton


    def _load_state(self, resource):
        state = self.state
        # Keep fields info (each item is an isntance of <Field>)
        state.fields = []
        # Keep the list of indexed fields (only its numbers)
        state.indexed_fields = []
        # Keeps a mapping from field name to field number
        state.field_numbers = {}

        for line in resource.readlines():
            line = line.strip()
            if line:
                number, name, type, is_indexed, is_stored = line.split('#')
                number = int(number)
                is_indexed = bool(int(is_indexed))
                is_stored = bool(int(is_stored))
                field = Field(number, name, type, is_indexed, is_stored)
                state.fields.append(field)
                if is_indexed:
                    state.indexed_fields.append(number)
                state.field_numbers[name] = number


    def to_str(self):
        data = []
        for field in self.state.fields:
            data.append('%d#%s#%s#%d#%d\n' % (field.number, field.name,
                                              field.type, field.is_indexed,
                                              field.is_stored))
        return ''.join(data)



class Catalog(Folder):

    def get_skeleton(self, fields=[]):
        skeleton = {'fields': Fields(fields=fields)}
        for number, field in enumerate(fields):
            skeleton['f%d' % number] = IIndex()
        return skeleton


    def _get_handler(self, segment, resource):
        name = segment.name
        if name == 'fields':
            return Fields(resource)
        elif name.startswith('f'):
            return IIndex(resource)
        elif name.startswith('d'):
            return IDocument(resource)
        return Folder._get_handler(self, segment, resource)


    #########################################################################
    # Load / Save state
    #########################################################################
    def _load_state(self, resource):
        Folder._load_state(self, resource)

        state = self.state
        # The document number
        document_numbers = [ int(x[1:]) for x in resource.get_resource_names()
                             if x.startswith('d') ]
        if document_numbers:
            state.document_number = max(document_numbers) + 1
        else:
            state.document_number = 0
        # Added and removed documents
        state.added_documents = {}
        state.removed_documents = []


    def _save_state(self, resource):
        state = self.state
        # Remove documents
        for doc_number in state.removed_documents:
            name = 'd%07d' % doc_number
            resource.del_resource(name)
            del state.cache[name]
        state.removed_documents = []
        # Add documents
        for doc_number, document in state.added_documents.items():
            if document.has_changed():
                document.save_state()
            name = 'd%07d' % doc_number
            resource.set_resource(name, document.resource)
            state.cache[name] = None
        state.added_documents = {}
        # Save indexes
        fields = self.get_handler('fields')
        for field in fields.state.fields:
            if field.is_indexed:
                iindex = self.get_handler('f%d' % field.number)
                iindex._save_state(iindex.resource)
                iindex.timestamp = iindex.resource.get_mtime()


    #########################################################################
    # Private API
    #########################################################################
    def get_new_document_number(self):
        state = self.state
        document_number = state.document_number
        state.document_number += 1
        return document_number


    def get_index(self, name):
        fields = self.get_handler('fields')

        field_numbers = fields.state.field_numbers
        if name not in field_numbers:
            raise ValueError, 'the field "%s" is not defined' % name

        field_number = field_numbers[name]
        if field_number not in fields.state.indexed_fields:
            raise ValueError, 'the field "%s" is not indexed' % name

        return self.get_handler('f%d' % field_number)


    #########################################################################
    # Public API
    #########################################################################
    def index_document(self, document):
        # Mark as changed
        self.set_changed()

        state = self.state
        # Create the document
        doc_number = self.get_new_document_number()
        idoc = IDocument()
        stored = idoc.get_handler('stored')
        state.added_documents[doc_number] = idoc
        # Index
        fields = self.get_handler('fields')
        for field in fields.state.fields:
            # Extract the field value from the document
            if isinstance(document, dict):
                value = document.get(field.name)
            else:
                value = getattr(document, field.name, None)

            # If value is None, don't go further
            if value is None:
                continue

            # Indexed fields
            if field.is_indexed:
                # Forward index (unindex)
                idoc._set_handler('i%d' % field.number, IndexedField())
                ifield = idoc.get_handler('i%d' % field.number)

                # Inverted index (search)
                ii = self.get_handler('f%d' % field.number)
                terms = set()
                # Tokenize
                analyser = get_analyser(field.type)
                for word, position in analyser(value):
                    ii.index_term(word, doc_number, position)
                    # Update the un-index data structure
                    if word not in terms:
                        ifield.add_term(word)
                        terms.add(word)

            # Stored fields (hits)
            if field.is_stored:
                # XXX Coerce lists
                if isinstance(value, list):
                    value = ' '.join(value)
                stored.set_value(field.number, value)

            stored.save_state()

        return doc_number


    def unindex_document(self, doc_number):
        # Mark as changed
        self.set_changed()

        state = self.state
        if doc_number in state.added_documents:
            document = state.added_documents.pop(doc_number)
        else:
            document = self.get_handler('d%07d' % doc_number)
            state.removed_documents.append(doc_number)

        for name in document.resource.get_resource_names():
            if name.startswith('i'):
                field = document.get_handler(name)
                ii = self.get_handler('f' + name[1:])
                for term in field.state.terms:
                    ii.unindex_term(term, doc_number)


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
        from operator import itemgetter

        # Search
        documents = self._search(query, **kw)
        # Build the document objects
        state = self.state
        fields = self.get_handler('fields')
        # iterate on sorted by weight in decrease order
        for document in sorted(documents.iteritems(), key=itemgetter(1),
                               reverse=True):
            doc_number, weight = document
            # Load the IDocument
            if doc_number in state.added_documents:
                doc_handler = state.added_documents[doc_number]
            else:
                doc_handler = self.get_handler('d%07d' % doc_number)
            # Get the stored fields
            if doc_handler.document is None:
                document = Document(doc_number)
                stored = doc_handler.get_handler('stored')
                for field in fields.state.fields:
                    if field.is_stored:
                        value = stored.get_value(field.number)
                        setattr(document, field.name, value)
                doc_handler.document = document

            yield doc_handler.document



class Document(object):
    def __init__(self, number):
        self.__number__ = number
