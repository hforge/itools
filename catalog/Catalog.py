# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from Python
from sets import Set

# Import from itools
from itools.handlers.Folder import Folder
from itools.handlers.Text import Text
import Analysers
from Document import Document, IndexedField, StoredField
from IIndex import IIndex


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


    def _load(self):
        # Keep fields info (each item is an isntance of <Field>)
        self.fields = []
        # Keep the list of indexed fields (only its numbers)
        self.indexed_fields = []
        # Keeps a mapping from field name to field number
        self.field_numbers = {}

        r = self.resource
        data = r.get_data()
        for line in data.split('\n'):
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


    def unicode(self):
        data = u''
        for field in fields:
            data += u'%d#%s#%s#%d#%d\n' % (field.number, field.name,
                                           field.type, field.is_indexed,
                                           field.is_stored)
        return data



class Catalog(Folder):
    def get_skeleton(self, fields=[]):
        skeleton = [('fields', Fields(fields=fields))]
        for number, field in enumerate(fields):
            skeleton.append(('f%d' % number, IIndex()))
        return skeleton


    def _get_handler(self, segment, resource):
        name = segment.name
        if name == 'fields':
            return Fields(resource)
        elif name.startswith('f'):
            return IIndex(resource)
        elif name.startswith('d'):
            return Document(resource)
        return Folder._get_handler(self, segment, resource)


    def _load(self):
        self.documents = [ int(x[1:]) for x in self.get_resources()
                           if x.startswith('d') ]
        self.documents.sort()


    #########################################################################
    # Private API
    #########################################################################
    def get_new_document_number(self):
        if self.documents:
            return self.documents[-1] + 1
        return 0


    #########################################################################
    # Public API
    #########################################################################
    def index_document(self, document):
        # Get the document number, and name
        doc_number = self.get_new_document_number()
        doc_name = 'd%d' % doc_number

        fields = self.get_handler('fields')
        # Documents
        self.documents.append(doc_number)
        self.set_handler(doc_name, Document())
        idoc = self.get_handler(doc_name)
        #
        for field in fields.fields:
            # Extract the field value from the document
            value = None
            if hasattr(document, field.name):
                value = getattr(document, field.name)
            elif isinstance(document, dict):
                if field.name in document:
                    value = document[field.name]
            if callable(value):
                value = value()

            # If value is None, don't go further
            if value is None:
                continue

            # Indexed fields
            if field.is_indexed:
                # Forward index (unindex)
                idoc.set_handler('i%d' % field.number, IndexedField())
                ifield = idoc.get_handler('i%d' % field.number)

                # Choose the right analyser
                if field.type == 'text':
                    analyser = Analysers.Text(value)
                elif field.type == 'bool':
                    analyser = Analysers.Bool(value)
                elif field.type == 'keyword':
                    analyser = Analysers.Keyword(value)
                elif field.type == 'path':
                    analyser = Analysers.Path(value)

                # Inverted index (search)
                ii = self.get_handler('f%d' % field.number)
                terms = Set()
                # Tokenize
                for word, position in analyser:
                    ii.index_word(word, doc_number, position)
                    # Update the un-index data structure
                    if word not in terms:
                        ifield.add_term(word)
                        terms.add(word)

            # Stored fields (hits)
            if field.is_stored:
                idoc.set_handler('s%d' % field.number, StoredField(data=value))

        return doc_number


    def unindex_document(self, doc_number):
        document = self.get_handler('d%d' % doc_number)
        for name in document.get_resources():
            if name.startswith('i'):
                field = document.get_handler(name)
                ii = self.get_handler('f' + name[1:])
                for term in field.terms:
                    ii.unindex_word(term, doc_number)
        # Remove the document
        i = self.documents.index(doc_number)
        del self.documents[i]
        self.del_handler('d%d' % doc_number)


    def search(self, **kw):
        documents = {}

        fields = self.get_handler('fields')
        # Search
        for field_name, value in kw.items():
            field_number = fields.field_numbers[field_name]
            field = fields.fields[field_number]
            if field_number in fields.indexed_fields:
                tree = self.get_handler('f%d' % field_number)
                # XXX Analyse
                if field.type == 'bool':
                    value = str(int(value))
                for doc_number, weight in tree.search_word(value).items():
                    documents.setdefault(doc_number, 0)
                    documents[doc_number] += weight
        # Sort by weight
        documents = [ (weight, doc_number)
                      for doc_number, weight in documents.items() ]
        documents.sort()
        documents.reverse()
        # Build the document objects
        for i, document in enumerate(documents):
            weight, doc_number = document
            document = Document() # XXX
            document.__number__ = doc_number
            # Get the stored fields
            for field in fields.fields:
                if field.is_stored:
                    stored_field = self.get_handler('d%d/s%d' % (doc_number,
                                                                 field.number))
                    setattr(document, field.name, stored_field.value)
            documents[i] = document
        return documents
