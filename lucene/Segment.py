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

# Import from itools.lucene
from Lucene import File



############################################################################
# Analyser
############################################################################

common_words = ['about', 'an', 'and', 'are', 'at', 'as', 'be', 'from', 'for',
                'how', 'in', 'is', 'it', 'of', 'on', 'or',
                'that', 'the', 'this', 'to',
                'was', 'what', 'when', 'where', 'which', 'who', 'why', 'will']

class Analyser(object):
    def __init__(self, data):
        self.data = data
        self.index = 0
        self.position = 0


    def next_word(self):
        """
        Returns the next word and its position in the data. The analysis
        is done with the automaton:

        0 -> 1 [letter or number]
        0 -> 0 [stop word]
        1 -> 2 [letter or number]
        1 -> 0 [stop word]
        2 -> 2 [letter or number]
        2 -> word [stop word]
        """
        state = 0
        lexeme = u''
        while self.index < len(self.data):
            c = self.data[self.index]
            if state == 0:
                if c.isalpha():
                    lexeme += c
                    state = 1
            elif state == 1:
                if c.isalpha():
                    lexeme += c
                    state = 2
                else:
                    lexeme = u''
                    state = 0
            elif state == 2:
                if c.isalpha():
                    lexeme += c
                else:
                    lexeme = lexeme.lower()
                    if lexeme in common_words:
                        lexeme = u''
                        state = 0
                    else:
                        position = self.position
                        self.position += 1
                        return lexeme, position
            self.index += 1
        # Last word
        if state == 2:
            lexeme = lexeme.lower()
            return lexeme, self.position

        return None, None



############################################################################
# Tree
############################################################################

class Tree(object):
    def __init__(self):
        self.documents = {}
        self.children = {}


    def index_word(self, word, doc_number, position):
        if word:
            prefix, suffix = word[0], word[1:]
            subtree = self.children.setdefault(prefix, Tree())
            subtree.index_word(suffix, doc_number, position)
        else:
            positions = self.documents.setdefault(doc_number, [])
            positions.append(position)


    def unindex_word(self, word, doc_number):
        if word:
            prefix, suffix = word[0], word[1:]
            subtree = self.children[prefix]
            subtree.unindex_word(suffix, doc_number)
            if len(subtree.children) == 0 and len(subtree.documents) == 0:
                del self.children[prefix]
        else:
            del self.documents[doc_number]


    def search_word(self, word):
        if word:
            prefix, suffix = word[0], word[1:]
            subtree = self.children.get(prefix, None)
            if subtree is None:
                return []
            else:
                return subtree.search_word(suffix)
        else:
            documents = []
            for doc_number, positions in self.documents.items():
                weight = len(positions)
                documents.append((weight, doc_number))
            documents.sort()
            documents.reverse()
            return [ y for x, y in documents ]


    def to_str(self, indent=0):
        s = u''
        for key, tree in self.children.items():
            s = s + '%s%s: %s\n' % (' '*indent, key, tree.documents)
            s += tree.to_str(indent + len(key))
        return s


    def __str__(self):
        return self.to_str()


    def get_terms(self):
        letters = self.children.keys()
        if letters:
            letters.sort()
            result = []
            for letter in letters:
                subtree = self.children[letter]
                subtree_result = subtree.get_terms()
                if len(subtree_result) == 0:
                    result.append((0, letter, subtree.documents))
                else:
                    # First element, add a letter to the suffix
                    prefix_length, suffix, documents = subtree_result[0]
                    result.append((prefix_length, letter + suffix, documents))
                    # The other elements, increment the prefix length
                    for prefix_length, suffix, documents in subtree_result[1:]:
                        result.append((prefix_length + 1, suffix, documents))
            return result
        else:
            return []



############################################################################
# Segment
############################################################################

class Document(object):
    def __init__(self, number):
        self.__number__ = number



class Segment(object):
    def __init__(self, index_handler, segment_name):
        """
        The expected parameters are the index handler, which must be an
        instance of 'itools.handlers.Index.Index', and the segment name.
        """
        # Load the handlers
        self.fnm = fnm = index_handler.get_handler('%s.fnm' % segment_name)
        self.fdx = fdx = index_handler.get_handler('%s.fdx' % segment_name)
        self.fdt = fdt = index_handler.get_handler('%s.fdt' % segment_name)
        self.tis = tis = index_handler.get_handler('%s.tis' % segment_name)
        self.tii = tii = index_handler.get_handler('%s.tii' % segment_name)
        self.frq = frq = index_handler.get_handler('%s.frq' % segment_name)
        self.prx = prx = index_handler.get_handler('%s.prx' % segment_name)
        self.tvx = tvx = index_handler.get_handler('%s.tvx' % segment_name)
        self.tvd = tvd = index_handler.get_handler('%s.tvd' % segment_name)
        self.tvf = tvf = index_handler.get_handler('%s.tvf' % segment_name)

        # Initialize the data structures
        self.field_names = []
        self.field_numbers = {}
        self.indexed_fields = {}
        self.documents = {}

        # Load the field metadata
        for field_number, field_metadata in enumerate(fnm.fields):
            field_name, is_indexed, is_stored, is_tokenized = field_metadata
            # Keep mapping from field numbers to field names and viceversa
            self.field_names.append(field_name)
            self.field_numbers[field_name] = field_number
            # Initialize the data structure for search
            if is_indexed:
                self.indexed_fields[field_name] = Tree()

        # Load the terms into 'indexed_fields' and 'documents'
        term_text = ''
        freq_index = prox_index = 0
        for terminfo in tis:
            prefix_length, suffix, field_number = terminfo[:3]
            doc_freq, freq_delta, prox_delta, skip_delta = terminfo[3:]
            # Calculate the term text, and the frequency and proximity indices
            term_text = term_text[:prefix_length] + suffix
            freq_index += freq_delta
            prox_index += prox_delta
            # Get the search tree
            field_name = self.field_names[field_number]
            tree = self.indexed_fields[field_name]
            # Load term positions in documents and index them
            frq.index = freq_index
            prx.index = prox_index
            for doc_number, freq in frq.load_termfreqs(doc_freq):
                for position in prx.load_positions(freq):
                    tree.index_word(term_text, doc_number, position)
                # Update 'self.documents'
                fields = self.documents.setdefault(doc_number, {})
                terms = fields.setdefault(field_name, [])
                terms.append(term_text)


    def is_tokenized(self, field_name):
        for field_number, field_metadata in enumerate(self.fnm.fields):
            name, is_indexed, is_stored, is_tokenized = field_metadata
            if name == field_name:
                return is_tokenized
        raise LookupError, 'unknown field name "%s"' % field_name


    def get_new_document_number(self):
        if self.documents:
            document_numbers = self.documents.keys()
            document_numbers.sort()
            return document_numbers[-1] + 1
        return 0


    def index_document(self, document):
        # Get the document number
        doc_number = self.get_new_document_number()
        # Add the document to 'self.documents'
        fields = {}
        # Update the search data structure (term dictionary)
        for field_name in self.indexed_fields:
            if hasattr(document, field_name):
                tree = self.indexed_fields[field_name]
                terms = Set()

                # XXX Check that data is an string
                data = getattr(document, field_name)
                if callable(data):
                    data = data()

                if self.is_tokenized(field_name):
                    analyser = Analyser(data)
                    word, position = analyser.next_word()
                    while word is not None:
                        tree.index_word(word, doc_number, position)
                        # Update the un-index data structure ('self.documents')
                        terms.add(word)
                        # Next word
                        word, position = analyser.next_word()
                else:
                    tree.index_word(data, doc_number, 0)
                    terms.add(data)

                if terms:
                    fields[field_name] = terms

        if fields:
            self.documents[doc_number] = fields
            # Stored fields
            fields = []
            for field_number, field in enumerate(self.fnm.fields):
                field_name, is_indexed, is_stored, is_tokenized = field
                if is_stored and hasattr(document, field_name):
                    data = getattr(document, field_name)
                    if callable(data):
                        data = data()
                    fields.append((field_number, True, data))
            self.fdt.documents.append(fields)

            # Save the data
            self.save()

            # Return the document number
            return doc_number
        else:
            # XXX Output a warning
            return None


    def unindex_document(self, doc_number):
        fields = self.documents[doc_number]
        for field_name, terms in fields.items():
            tree = self.indexed_fields[field_name]
            for term in terms:
                tree.unindex_word(term, doc_number)
        del self.documents[doc_number]
        # Stored fields
        del self.fdt.documents[doc_number] 


    def search(self, **kw):
        documents = []
        for key, value in kw.items():
            if key in self.indexed_fields:
                tree = self.indexed_fields[key]
                for doc_number in tree.search_word(value):
                    # Calculate the document index
                    document_numbers = self.documents.keys()
                    document_numbers.sort()
                    doc_index = document_numbers.index(doc_number)
                    # Get the stored fields
                    stored_fields = self.fdt.documents[doc_index]
                    # Build the document
                    document = Document(doc_number)
                    for field_number, tokenized, value in stored_fields:
                        field_name = self.field_names[field_number]
                        setattr(document, field_name, value)
                    documents.append(document)
        return documents


    def save(self):
        # Get field names sorted
        field_names = [ (name, i) for i, name in enumerate(self.field_names) ]
        field_names.sort()

        # Initialize file data to fill
        tis = File.save_uint32(self.tis.index_interval) \
              + File.save_uint32(self.tis.skip_interval)
##        tii = File.save_uint32(XXX/XXX)
        frq = ''
        prx = ''

        term_count = 0
        freq_delta = 0
        prox_delta = 0
        for field_name, field_number in field_names:
            if field_name in self.indexed_fields:
                tree = self.indexed_fields[field_name]
                for prefix_length, suffix, documents in tree.get_terms():
                    term_count += 1
                    doc_freq = len(documents)
                    tis += File.save_vint(prefix_length)
                    tis += File.save_string(suffix)
                    tis += File.save_vint(field_number)
                    tis += File.save_vint(doc_freq)
                    tis += File.save_vint(freq_delta)
                    tis += File.save_vint(prox_delta)
                    tis += File.save_vint(0) # XXX Dummy SkipDelta
                    # Update frq
                    documents = documents.items()
                    documents.sort()
                    last_document_number = 0
                    term_freqs = ''
                    term_positions = ''
                    for document_number, positions in documents:
                        document_delta = document_number - last_document_number
                        last_document_number = document_number
                        freq = len(positions)
                        if freq == 1:
                            term_freqs += File.save_vint(document_delta*2 + 1)
                        else:
                            term_freqs += File.save_vint(document_delta*2)
                            term_freqs += File.save_vint(freq)
                        # Update prx
                        positions.sort()
                        last_position = 0
                        for position in positions:
                            position_delta = position - last_position
                            last_position = position
                            term_positions += File.save_vint(position_delta)
                    # SkipData
                    skip_data = ''
                    for i in range(doc_freq/self.tis.skip_interval):
                        # XXX Store dummy data
                        skip_data += File.save_vint(0) # DocSkip
                        skip_data += File.save_vint(0) # FreqSkip
                        skip_data += File.save_vint(0) # ProxSkip
                    # Update .frq and .prx files
                    frq = frq + term_freqs + skip_data
                    prx += term_positions
                    # Calculate the frequency and proximity deltas
                    freq_delta = len(term_freqs) + len(skip_data)
                    prox_delta = len(term_positions)

        tis = File.save_int32(self.tis.version) \
              + File.save_uint64(term_count) \
              + tis

        self.tis.resource.set_data(tis)
##        self.tii.resource.set_data(tii)
        self.frq.resource.set_data(frq)
        self.prx.resource.set_data(prx)

        # Save stored fields
        self.fdt.save()

        return term_count
