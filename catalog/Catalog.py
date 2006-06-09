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
from itools.handlers.registry import register_handler_class
from analysers import get_analyser
from IDocument import IndexedFields, StoredFields
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

    __slots__ = ['resource', 'timestamp', 'fields', 'indexed_fields',
                 'field_numbers']


    def new(self, fields=[]):
        self.fields = []
        self.indexed_fields = []
        self.field_numbers = {}

        for number, field in enumerate(fields):
            name, type, is_indexed, is_stored = field
            field = Field(number, name, type, is_indexed, is_stored)
            self.fields.append(field)
            if is_indexed:
                self.indexed_fields.append(number)
            self.field_numbers[name] = number


    def _load_state(self, resource):
        # Keep fields info (each item is an isntance of <Field>)
        self.fields = []
        # Keep the list of indexed fields (only its numbers)
        self.indexed_fields = []
        # Keeps a mapping from field name to field number
        self.field_numbers = {}

        for line in resource.readlines():
            line = line.strip()
            if line:
                number, name, type, is_indexed, is_stored = line.split('#')
                number = int(number)
                is_indexed = bool(int(is_indexed))
                is_stored = bool(int(is_stored))
                field = Field(number, name, type, is_indexed, is_stored)
                self.fields.append(field)
                if is_indexed:
                    self.indexed_fields.append(number)
                self.field_numbers[name] = number


    def to_str(self):
        data = []
        for field in self.fields:
            data.append('%d#%s#%s#%d#%d\n' % (field.number, field.name,
                                              field.type, field.is_indexed,
                                              field.is_stored))
        return ''.join(data)



class Catalog(Folder):

    class_mimetypes = ['application/x-catalog']

    __slots__ = Folder.__slots__ + ['document_number', 'added_documents',
                                    'removed_documents']


    def new(self, fields=[]):
        Folder.new(self)

        # Set initial resources
        cache = self.cache
        for number, field in enumerate(fields):
            cache['f%d' % number] = IIndex()
        fields = Fields(fields=fields)
        cache['fields'] = fields

        # Default state
        self.document_number = 0
        self.added_documents = {}
        self.removed_documents = []


    def get_handler_class(self, segment, resource):
        name = segment.name
        if name == 'fields':
            return Fields
        elif name.startswith('f'):
            return IIndex
        elif name.endswith('i'):
            return IndexedFields
        elif name.endswith('s'):
            return StoredFields
        return Folder.get_handler_class(self, segment, resource)


    #########################################################################
    # Load / Save state
    def _load_state(self, resource):
        Folder._load_state(self, resource)

        # The document number
        document_numbers = [ int(x[:-1]) for x in resource.get_resource_names()
                             if x.endswith('i') ]
        if document_numbers:
            self.document_number = max(document_numbers) + 1
        else:
            self.document_number = 0
        # Added and removed documents
        self.added_documents = {}
        self.removed_documents = []


    def _save_state(self, resource):
        # Remove documents
        for doc_number in self.removed_documents:
            iname = '%07di' % doc_number
            sname = '%07ds' % doc_number
            resource.del_resource(iname)
            resource.del_resource(sname)
            del self.cache[iname]
            del self.cache[sname]
        self.removed_documents = []
        # Add documents
        for doc_number in self.added_documents:
            indexed, stored = self.added_documents[doc_number]
            if indexed.has_changed():
                indexed.save_state()
            if stored.has_changed():
                stored.save_state()
            iname = '%07di' % doc_number
            sname = '%07ds' % doc_number
            resource.set_resource(iname, indexed.resource)
            resource.set_resource(sname, stored.resource)
            self.cache[iname] = None
            self.cache[sname] = None
        self.added_documents = {}


    #########################################################################
    # Private API
    #########################################################################
    def get_new_document_number(self):
        document_number = self.document_number
        self.document_number += 1
        return document_number


    def get_index(self, name):
        fields = self.get_handler('fields')

        field_numbers = fields.field_numbers
        if name not in field_numbers:
            raise ValueError, 'the field "%s" is not defined' % name

        field_number = field_numbers[name]
        if field_number not in fields.indexed_fields:
            raise ValueError, 'the field "%s" is not indexed' % name

        return self.get_handler('f%d' % field_number)


    #########################################################################
    # Public API
    #########################################################################
    def index_document(self, document):
        # Mark as changed
        self.set_changed()

        # Create the document
        doc_number = self.get_new_document_number()
##        idoc = IDocument()
        indexed = IndexedFields()
        stored = StoredFields()
        self.added_documents[doc_number] = (indexed, stored)
        # Index
        fields = self.get_handler('fields')
        for field in fields.fields:
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
                # Get the inverted index (search)
                ii = self.get_handler('f%d' % field.number)
                ii.set_changed()
                # Tokenize
                terms = set()
                analyser = get_analyser(field.type)
                for word, position in analyser(value):
                    terms.add(word)
                    # Update the inverted index
                    ii.index_term(word, doc_number, position)

                # Update the forward index (un-index)
                indexed.add_field(field.number, list(terms))

            # Stored fields (hits)
            if field.is_stored:
                # XXX Coerce lists
                if isinstance(value, list):
                    value = ' '.join(value)
                stored.set_value(field.number, value)

        indexed.save_state()
        stored.save_state()

        return doc_number


    def unindex_document(self, doc_number):
        # Mark as changed
        self.set_changed()

        if doc_number in self.added_documents:
            indexed, stored = self.added_documents.pop(doc_number)
        else:
            indexed = self.get_handler('%07di' % doc_number)
            self.removed_documents.append(doc_number)

        fields = indexed.fields
        for field_number in fields:
            ii = self.get_handler('f%d' % field_number)
            ii.set_changed()
            for term in fields[field_number]:
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
        fields = self.get_handler('fields')
        # iterate on sorted by weight in decrease order
        for document in sorted(documents.iteritems(), key=itemgetter(1),
                               reverse=True):
            doc_number, weight = document
            # Load the IDocument
            if doc_number in self.added_documents:
                indexed, stored = self.added_documents[doc_number]
            else:
                stored = self.get_handler('%07ds' % doc_number)

            # Get the stored fields
            if stored.document is None:
                document = Document(doc_number)
                for field in fields.fields:
                    if field.is_stored:
                        value = stored.get_value(field.number)
                        setattr(document, field.name, value)
                stored.document = document

            yield stored.document


register_handler_class(Catalog)



class Document(object):
    def __init__(self, number):
        self.__number__ = number
