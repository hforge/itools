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

# Import from the future
from __future__ import with_statement

# Import from itools
from itools import vfs
from io import (decode_character, encode_character, decode_link, encode_link,
                decode_uint32, encode_uint32, encode_uint32_2, encode_version,
                NULL)

NULL2 = NULL + NULL



"""
The search data structure is an inverted index.

On memory the inverted index is a tree where every node represents a letter,
for example, if our index keeps the words 'hello' and 'here' it would look
like:

  h -- e -- l -- l -- o
         \- r -- e

This is a compact representation of the index. And every search takes as
many dictionary lookups as letters has the word being searched, if the
search is succesful (e.g. 'here' takes 4 lookups and 'hello' takes 5).
If the search is not succesful it could take less lookups (4 for 'hell',
but only 2 for 'holidays').

Every node also contains which documents contain the word and the positions
the word appears within the document, for example (if the word 'hello'
appears once in the first document and the word 'here' appears twice in
the second document):

  h -- e -- l -- l -- o {0: [28]}
         \- r -- e {1: [5, 37]}

File format
===========

At the resource level, an inverted index is stored as a folder with two
file resources:

  - 'tree', keeps the tree structure of terms;

  - 'docs', keeps the numbers of the documents where each term has been
    found, and the frequency (number of times the term has been found in
    a document).


The tree file
-------------

The "tree" file is made up of blocks, where each block has 16 bytes. A block
has 4 slots of 4 bytes each.

The first block is special, it represents the root node, the empty string.
Its format is:
    
  - version number [version]
  - <unused> (4 bytes)
  - first child [link]
  - <unused> (4 bytes)

The format for the others blocks is:

  - character [character]
  - pointer to the "docs" file [link]
  - first child [link]
  - next sibling [link]



The docs file
-------------

The "docs" file is made up of blocks of variable length. Each block has a
header of three slots (12 bytes, 3 bytes per slot), followed by n slots,
one for every position the term appears in the document:

  - document number [uint32]
  - frequency [uint32]
  - next document [link]
  - position (0) [uint32]
  ...
  - position (frequency - 1) [uint32]
"""



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
    #######################################################################
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


    def _load_children_deep(self, tree_file):
        # This method is only here to meseaure the memory footprint
        if self.children is None:
            self.load_children(tree_file)
        for child in self.children:
            self.children[child]._load_children_deep(tree_file)


    #######################################################################
    # Search
    #######################################################################
    def search_range(self, tree_file, docs_file, left, right):
        """
        Searches the index from 'left' to 'right', left included and right
        excluded: [left, right[

        Returns a mapping with all the documents found, the values of the
        mapping are the weights.
        """
        documents = {}
        # Here
        if not left:
            if self.documents is None:
                self.load_documents(tree_file, docs_file)

            for n in self.documents:
                documents[n] = len(self.documents[n])

        # Children
        if self.children is None:
            self.load_children(tree_file)

        if left:
            prefix_left, left = left[0], left[1:]
        else:
            prefix_left = None

        if right:
            prefix_right, right = right[0], right[1:]
        else:
            prefix_right = None

        for c in self.children:
            # Skip too small values
            if prefix_left and c < prefix_left:
                continue
            # Skipt too big values
            if prefix_right:
                if c > prefix_right:
                    continue
                if c == prefix_right and not right:
                    continue
            # Build query for the child
            # Left border
            if c == prefix_left:
                c_left = left
            else:
                c_left = None
            # Right border
            if c == prefix_right:
                c_right = right
            else:
                c_right = None
            # Run query
            child_documents = self.children[c].search_range(tree_file,
                                                            docs_file,
                                                            c_left, c_right)
            for n in child_documents:
                if n in documents:
                    documents[n] += child_documents[n]
                else:
                    documents[n] = child_documents[n]
                
        return documents



class _Index(object):

    __slots__ = ['root', 'tree_n_blocks', 'docs_n_slots']


    def __init__(self, tree_file=None, docs_file=None):
        if tree_file is None and docs_file is None:
            self.root = _Node({}, {}, 0)
            self.tree_n_blocks = 1
            self.docs_n_slots = 0
        else:
            self.root = _Node(None, {}, 0)
            # The number of blocks in the tree file
            tree_file.seek(0, 2)
            self.tree_n_blocks = tree_file.tell() / 16
            # The number of slots in the docs file
            docs_file.seek(0, 2)
            self.docs_n_slots = docs_file.tell() / 4


    #######################################################################
    # Init
    def init_tree_file(self, tree_file):
        tree_file.write(''.join([VERSION, ZERO, NULL, NULL]))


    #######################################################################
    # Index
    #######################################################################
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

        seek = tree_file.seek
        read = tree_file.read
        write = tree_file.write

        ###################################################################
        # Get the node for the word to index. Create it if it does not
        # exist.
        node = self.root
        for c in word:
            # Load data if needed
            if node.children is None:
                node.load_children(tree_file)

            # Create the node if needed
            children = node.children
            if c in children:
                # Next
                node = children[c]
            else:
                # Add a new block
                slot_number = tree_n_blocks
                tree_n_blocks += 1
                # Write
                # Prepend the new slot
                seek(node.block * 16 + 8)
                old_first_child = read(4)
                seek(-4, 1)
                write(encode_link(slot_number))
                # Write the new slot
                seek(slot_number * 16)
                write(encode_character(c) + NULL2 + old_first_child)
                # Add node, and continue
                children[c] = node = _Node({}, {}, slot_number)

        # Update the number of blocks
        self.tree_n_blocks = tree_n_blocks

        ###################################################################
        # Update the documents, both the data structure in memory and the
        # file.
        # Get the pointer to the 'documents' file
        seek(node.block * 16 + 4)
        first_doc = read(4)

        # Load documents if needed
        if node.documents is None:
            node.load_documents(tree_file, docs_file)

        # Build the data to append to the docs file
        buffer = []
        append = buffer.append
        node_documents = node.documents
        for doc_number in documents:
            if doc_number in node_documents:
                raise ValueError, 'document %s already indexed' % doc_number

            positions = documents[doc_number]
            # Update data structure
            node_documents[doc_number] = positions
            # Calculate the number of slots
            frequency = len(positions)
            # Update the buffer (uint32, uint32, link, uint32, ...)
            append(encode_uint32_2(doc_number, frequency))
            append(first_doc)
            for position in positions:
                append(encode_uint32(position))
            # Next
            first_doc = encode_link(docs_n_slots)
            docs_n_slots = docs_n_slots + 3 + frequency
        # Append to the docs file
        docs_file.seek(0, 2)
        docs_file.write(''.join(buffer))
        # Prepend the document
        seek(node.block * 16 + 4)
        write(first_doc)

        self.docs_n_slots = docs_n_slots


    #######################################################################
    # Unindex
    #######################################################################
    def unindex_term(self, tree_file, docs_file, word, documents):
        """
        Un-indexes the given term. The parameter 'documents' is a list with
        the numbers of the documents that must be un-indexed.
        """
        # Get the node
        node = self.root
        for c in word:
            if node.children is None:
                node.load_children(tree_file)
            # Next
            node = node.children[c]

        # Load documents
        if node.documents is None:
            node.load_documents(tree_file, docs_file)

        # Update data structure
        for doc_number in documents:
            del node.documents[doc_number]

        # Update the docs file
        # Search the document block
        tree_file.seek(node.block * 16 +  4)
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
    #######################################################################
    def search_word(self, tree_file, docs_file, word):
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


    def search_range(self, tree_file, docs_file, left, right):
        """
        Searches the index from 'left' to 'right', left included and right
        excluded: [left, right[

        Returns a mapping with all the documents found, the values of the
        mapping are the weights.
        """
        # XXX Recursive implementation. Maybe we should try an iterative one
        # for speed.
        return self.root.search_range(tree_file, docs_file, left, right)


###########################################################################
# Handler
###########################################################################
class Index(object):

    __slots__ = ['uri', 'n', '_index', 'added_terms', 'removed_terms']


    def __init__(self, uri, n):
        self.uri = uri
        self.n = n

        base = vfs.open(self.uri)
        tree_file = base.open('%d_tree' % n)
        docs_file = base.open('%d_docs' % n)
        try:
            self._index = _Index(tree_file, docs_file)    
        finally:
            tree_file.close()
            docs_file.close()
        # Nothing changed yet
        self.added_terms = {}
        self.removed_terms = {}


    def save_state(self):
        base = vfs.open(self.uri)
        tree_file = base.open('%d_tree' % self.n)
        docs_file = base.open('%d_docs' % self.n)
        try:
            # Removed terms
            for term in self.removed_terms:
                documents = self.removed_terms[term]
                self._index.unindex_term(tree_file, docs_file, term, documents)
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


    def abort(self):
        self.added_terms = {}
        self.removed_terms = {}


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
        if self.uri is None:
            tree_file = None
            docs_file = None
        else:
            base = vfs.open(self.uri)
            tree_file = base.open('%s_tree' % self.n)
            docs_file = base.open('%s_docs' % self.n)
        try:
            documents = self._index.search_word(tree_file, docs_file, word)
        finally:
            if self.uri is not None:
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


    def search_range(self, left, right):
        if self.uri is None:
            tree_file = None
            docs_file = None
        else:
            base = vfs.open(self.uri)
            tree_file = base.open('tree')
            docs_file = base.open('docs')
        # Search in the data structure
        try:
            documents = self._index.search_range(tree_file, docs_file, left, right)
        finally:
            if self.uri is not None:
                tree_file.close()
                docs_file.close()

        # XXX We still need to consider removed and added terms, otherwise
        # we may get inaccurate results.

        return documents
