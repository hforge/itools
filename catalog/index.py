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

# Import from itools
from itools import vfs
from itools.handlers.base import Handler
from IO import (decode_character, encode_character, decode_link, encode_link,
                decode_uint32, encode_uint32, encode_version, NULL)



VERSION = encode_version('20060708')
ZERO = encode_uint32(0)

##########################################################################
# Data Structure
##########################################################################
class _Node(object):
    
    __slots__ = ['children', 'documents', 'block']


    def __init__(self, children, documents, block):
        self.children = children
        self.documents = documents
        self.block = block


    #######################################################################
    # Load
    def load_children(self, tree_file):
        children = {}
        # Read the pointer to the first child
        tree_file.seek(self.block * 16 + 8)
        child_n = decode_link(tree_file.read(4))
        # Read the childs
        while child_n is not None:
            # Read the slot
            tree_file.seek(child_n * 16)
            child = tree_file.read(16)
            # Add the child
            c = decode_character(child[:4])
            children[c] = _Node(None, None, child_n)
            # Next
            child_n = decode_link(child[12:])

        self.children = children


    def load_documents(self, tree_file, docs_file):
        documents = {}
        # Read the pointer to the documents
        tree_file.seek(self.block * 16 + 4)
        slot_n = decode_link(tree_file.read(4))
        # Read the documents
        while slot_n is not None:
            # Read the header
            docs_file.seek(slot_n * 4)
            header = docs_file.read(12)
            doc_number = decode_uint32(header[0:4])
            frequency = decode_uint32(header[4:8])
            slot_n = decode_link(header[8:12])
            # Load positions
            data = docs_file.read(frequency*4)
            positions = []
            while data:
                position, data = data[:4], data[4:]
                positions.append(decode_uint32(position))
            documents[doc_number] = positions

        self.documents = documents



class _Index(object):

    __slots__ = ['root', 'tree_n_blocks', 'docs_n_slots']


    def __init__(self):
        self.root = _Node({}, {}, 0)
        self.tree_n_blocks = 1
        self.docs_n_slots = 0


    #######################################################################
    # Init
    def init_tree_file(self, tree_file):
        tree_file.write(''.join([VERSION, ZERO, NULL, NULL]))


    def init_docs_file(self, docs_file):
        docs_file.write(VERSION)


    #######################################################################
    # Index
    def index_term(self, tree_file, docs_file, word, documents):
        """
        Indexes the given documents for the given words.

        Input:

            tree_file: the file object for the tree file (it must be open)
            docs_file: the file object for the docs file (it must be open)
            word     : the word to index (a string)
            documents: the documents to index: {<doc number>: [position, ...]}

        Modifies both the data structure in memory and the given files.
        """
        # Define local variables for speed
        tree_n_blocks = self.tree_n_blocks
        docs_n_slots = self.docs_n_slots

        ###################################################################
        # Get the node for the word to index. Create it if it does not
        # exist.
        node = self.root
        for c in word:
            # Load data if needed
            if node.children is None:
                node.load_children(tree_file)
            # Create the node if needed
            if c not in node.children:
                # Add a new block
                slot_number = tree_n_blocks
                tree_n_blocks += 1
                # Add node
                node.children[c] = _Node({}, {}, slot_number)
                # Write
                # Prepend the new slot
                tree_file.seek(node.block * 16 + 8)
                old_first_child = tree_file.read(4)
                tree_file.seek(-4, 1)
                tree_file.write(encode_link(slot_number))
                # Write the new slot
                tree_file.seek(slot_number * 16)
                tree_file.write(''.join([encode_character(c), NULL, NULL,
                                         old_first_child]))
            # Next
            node = node.children[c]

        # Update the number of blocks
        self.tree_n_blocks = tree_n_blocks

        ###################################################################
        # Update the documents, both the data structure in memory and the
        # file.
        # Get the pointer to the 'documents' file
        tree_file.seek(node.block * 16 + 4)
        first_doc = tree_file.read(4)

        # Load documents if needed
        if node.documents is None:
            node.load_documents(tree_file, docs_file)

        # Build the data to append to the docs file
        buffer = []
        for doc_number in documents:
            if doc_number in node.documents:
                raise ValueError, 'document %s already indexed' % doc_number

            positions = documents[doc_number]
            # Update data structure
            node.documents[doc_number] = positions
            # Calculate the number of slots
            frequency = len(positions)
            # Update the buffer
            buffer.append(encode_uint32(doc_number))
            buffer.append(encode_uint32(frequency))
            buffer.append(first_doc)
            for position in positions:
                buffer.append(encode_uint32(position))
            # Next
            first_doc = encode_link(docs_n_slots)
            docs_n_slots = docs_n_slots + 3 + frequency
        # Append to the docs file
        docs_file.seek(0, 2)
        docs_file.write(''.join(buffer))
        # Prepend the document
        tree_file.seek(node.block * 16 + 4)
        tree_file.write(first_doc)

        self.docs_n_slots = docs_n_slots


    #######################################################################
    # Unindex
    def unindex_term(self, tree_file, docs_file, word, documents):
        """
        Un-indexes the given term. The parameter 'documents' is a list with
        the numbers of the documents that must be un-indexed.
        """
        # Get the node
        node = self.tree
        for c in word:
            if node.children is None:
                node.load_children(tree_file)
            # Next
            node = node.children[c]

        # Load documents
        if node.documents is None:
            node.load_documents()

        # Update data structure
        for doc_number in documents:
            del self.documents[doc_number]

        # Update the docs file
        # Search the document block
        tree_file.seek(node.slot * 16 +  4)
        docs_slot_r = tree_file.read(4)
        docs_slot_n = decode_link(docs_slot_r)
        # Free blocks
        prev_slot_n = prev_slot = None
        while documents and docs_slot_n is not None:
            docs_slot = docs_slot_n * 4
            # Read the header
            docs_file.seek(docs_slot)
            header = docs_file.read(12)
            doc_number = decode_uint32(header[0:4])
            next_slot_r = header[8:12]
            next_slot_n = decode_link(next_slot_r)
            # Hit, remove the block
            if doc_number in documents:
                documents.remove(doc_number)
                # Remove from the documents list
                if prev_slot_n is None:
                    tree_file.seek(-4, 1)
                    tree_file.write(next_slot_r)
                else:
                    docs_file.seek(prev_slot + 8)
                    docs_file.write(next_slot_r)
            else:
                prev_slot_n, prev_slot = docs_slot_n, docs_slot
            # Next
            docs_slot_n = next_slot_n
            docs_slot_r = next_slot_r


    #######################################################################
    # Search
    def search(self, tree_file, docs_file, word):
        node = self.root
        for c in word:
            if node.children is None:
                node.load_children(tree_file)
            # Next
            if c in node.children:
                node = node.children[c]
            else:
                # Miss
                return {}

        if node.documents is None:
            node.load_documents(tree_file, docs_file)

        # XXX Don't copy
        return node.documents.copy()



###########################################################################
# Handler
###########################################################################
class Index(Handler):

    __slots__ = ['uri', 'timestamp', '_index', 'added_terms', 'removed_terms']


    def new(self):
        self._index = _Index()
        # {<term>: {<doc number>: [<position>, ..., <position>]}
        self.added_terms = {}
        # {<term>: set(<doc number>, ..)}
        self.removed_terms = {}


    def _save_state(self, uri):
        base = vfs.open(uri)
        tree_file = base.open('tree')
        docs_file = base.open('docs')
        try:
            # Removed terms
            for term in self.removed_terms:
                # XXX
                pass
            # Added terms
            for term in self.added_terms:
                documents = self.added_terms[term]
                self._index.index_term(tree_file, docs_file, term, documents)
            # Clean the data structure
            self.added_terms = {}
            self.removed_terms = {}
        finally:
            tree_file.close()
            docs_file.close()


    def save_state(self):
        self._save_state(self.uri)


    def save_state_to(self, uri):
        # Create the index folder
        vfs.make_folder(uri) 
        base = vfs.open(uri)
        # Initialize the tree file
        base.make_file('tree')
        with base.open('tree') as file:
            self._index.init_tree_file(file)
        # Initialize the docs file
        base.make_file('docs')
        with base.open('docs') as file:
            self._index.init_docs_file(file)
        # XXX Remains to save the data in "self._index"
        # Save changes
        self._save_state(uri)


    #######################################################################
    # Public API
    #######################################################################
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
        # Search in the data structure
        base = vfs.open(self.uri)
        tree_file = base.open('tree')
        docs_file = base.open('docs')
        try:
            documents = self.index.search(tree_file, docs_file, word)
        finally:
            tree_file.close()
            docs_file.close()

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

        return documents

