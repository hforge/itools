# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.handlers.File import File
from itools.handlers.Folder import Folder
import IO


"""
The search data structure is an inverted index. Today we keep how many times
a word appears on each document (the frequency), but not yet the position
within the document of each appearance.

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

Actually, today we do not keep the positions, so the list is filled with
None values:

  h -- e -- l -- l -- o {0: [None]}
         \- r -- e {1: [None, None]}

But this is a temporal situation, in a future version we will keep the
positions.

At the resource level, an inverted index is stored as a folder with two
file resources:

  - 'tree', keeps the tree structure of terms;

  - 'documents', keeps the numbers of the documents where each term has
    been found, and the frequency (number of times the term has been found
    in a document).
"""



class IIndexTree(File):
    """
    The Inverted Index is the data structure used to search. Its format
    consists of a header and a sequence of slots.

    The header format is:

      - version number (4 bytes)
      - number of slots (4 bytes)
      - first full slot (4 bytes)
      - first empty slot (4 bytes)

    Each slot is made of:

      - character (4 bytes)
      - frequency number (4 bytes), pointer to IIndexDocuments
      - first child (4 bytes)
      - next sibling (4 bytes)
    """

    class_version = '20040723'


    def get_skeleton(self):
        # The header
        version = IO.encode_version(self.class_version)
        number_of_slots = IO.encode_uint32(0)
        first_slot = IO.encode_link(None)
        first_empty = IO.encode_link(None)
        header = version + number_of_slots + first_slot + first_empty

        return header


    def _load_state(self, resource):
        state = self.state
        # The header
        state.version = IO.decode_version(resource.read(4))
        state.number_of_slots = IO.decode_uint32(resource.read(4))
        state.first_slot = IO.decode_link(resource.read(4))
        state.first_empty = IO.decode_link(resource.read(4))


    def _get_free_slot(self):
        """
        Internal method that returns a free slot. If none exists a new one
        is allocated.

        Beware this method leaves the resource in an inconsistent state,
        the method that calls it is responsible to use the slot so the
        resource becomes consistent.
        """
        state = self.state
        resource = self.resource
        if state.first_empty is None:
            slot_number = state.number_of_slots
            # Increment number of slots
            state.number_of_slots += 1
            resource[4:8] = IO.encode_uint32(state.number_of_slots)
        else:
            slot_number = state.first_empty
            # Update first empty
            base = 16 + slot_number * 16
            first_empty_link = resource[base+12:base+16]
            state.first_empty = IO.decode_link(first_empty_link)
            resource[12:16] = first_empty_link

        return slot_number



class IIndexDocuments(File):
    """
    The header format is:

    - version number [version]
    - number of slots [uint32]
    - first empty slot [link]

    The rest of the file is split into variable size blocks. A block maybe
    busy or free.

    A busy block format is:

    - document number [uint32]
    - frequency [uint32]
    - next document [link]
    - position (0) [uint32]
    ...
    - position (frequency - 1) [uint32]

    A free block format is:

    - size [uint32]
    - next free block [link]
    - free slot (0)
    ...
    - free slot (size - 2)
    """

    class_version = '20050529'


    def get_skeleton(self):
        version = IO.encode_version(self.class_version)
        number_of_slots = IO.encode_uint32(0)
        first_empty = IO.encode_link(None)
        return version + number_of_slots + first_empty


    def _load_state(self, resource):
        state = self.state
        # The header
        state.version = IO.decode_version(resource.read(4))
        state.number_of_slots = IO.decode_uint32(resource.read(4))
        state.first_empty = IO.decode_link(resource.read(4))



class Tree(object):
    """
    This class represents any node in the search tree (i.e. inverted index).
    """

    def __init__(self, root, slot):
        # The root is also the resource handler.
        self.root = root
        self.slot = slot
        self.documents = None
        self.children = None


    def load_documents(self):
        # Initialize data structure
        self.documents = {}

        # Load document pointer
        tree_rsrc = self.root.tree_handler.resource
        tree_slot = 16 + self.slot * 16
        doc_slot_n = IO.decode_link(tree_rsrc[tree_slot+4:tree_slot+8])

        # Load documents
        doc_rsrc = self.root.docs_handler.resource
        while doc_slot_n is not None:
            doc_slot = 12 + doc_slot_n * 4
            # Load the header
            header = doc_rsrc[doc_slot:doc_slot+12]
            doc_number = IO.decode_uint32(header[0:4])
            frequency = IO.decode_uint32(header[4:8])
            doc_slot_n = IO.decode_link(header[8:12])
            # Load positions
            self.documents[doc_number] = documents = set()
            data = doc_rsrc[doc_slot+12:doc_slot+12+(frequency*4)]
            i = 0
            while i < frequency:
                base = i * 4
                documents.add(IO.decode_uint32(data[base:base+4]))
                i += 1


    def load_children(self):
        self.children = {}

        tree_rsrc = self.root.tree_handler.resource
        slot = 16 + self.slot * 16
        # Children
        child_n = IO.decode_link(tree_rsrc[slot+8:slot+12])
        while child_n is not None:
            child = 16 + child_n * 16
            c = IO.decode_character(tree_rsrc[child:child+4])
            tree = Tree(self.root, child_n)
            self.children[c] = tree
            # Next
            child_n = IO.decode_link(tree_rsrc[child+12:child+16])


    ########################################################################
    # API
    ########################################################################
    def _index_term(self, term, documents):
        """
        Indexes the given term. The parameter 'documents' is a mapping
        from document number to list of positions:

          {<document number>: [postion, ...],
           ...}
        """
        if term:
            if self.children is None:
                self.load_children()

            prefix, suffix = term[0], term[1:]
            if prefix in self.children:
                subtree = self.children[prefix]
            else:
                # Get an empty slot
                free_slot_n = self.root.tree_handler._get_free_slot()
                # Update data structure on memory
                subtree = self.children[prefix] = Tree(self.root, free_slot_n)
                # Update resource
                r = self.root.tree_handler.resource
                # Initialize the empty slot
                free_slot = 16 + free_slot_n * 16
                if self.slot is None:
                    this_slot = 0
                else:
                    this_slot = 16 + self.slot * 16
                r[free_slot:free_slot+16] = IO.encode_character(prefix) \
                                            + IO.encode_link(None) \
                                            + IO.encode_link(None) \
                                            + r[this_slot+8:this_slot+12]
                # Prepend the new slot
                r[this_slot+8:this_slot+12] = IO.encode_link(free_slot_n)
            subtree._index_term(suffix, documents)
        else:
            tree_handler = self.root.tree_handler
            tree_rsrc = tree_handler.resource
            docs_handler = self.root.docs_handler
            docs_rsrc = docs_handler.resource
            # Get the slot in the 'documents' resource
            tree_slot = 16 + self.slot * 16
            fdoc_slot_r = tree_rsrc[tree_slot+4:tree_slot+8]
            fdoc_slot_n = IO.decode_link(fdoc_slot_r)
            if self.documents is None:
                self.load_documents()
            for doc_number, doc_positions in documents.items():
                if doc_number in self.documents:
                    raise ValueError, \
                          'document %s already indexed' % doc_number

                self.documents[doc_number] = doc_positions
                frequency = len(doc_positions)
                # Search a free block
                free_block_n = docs_handler.state.first_empty
                previous_block_n = None
                while free_block_n is not None:
                    free_block = 12 + free_block_n * 4
                    head = docs_rsrc[free_block:free_block+8]
                    size = IO.decode_uint32(head[0:4])
                    next_r = head[4:8]
                    if size >= frequency + 7:
                        # Create new free block
                        new_free_block_n = free_block_n + frequency + 3
                        new_free_block = 12 + new_free_block_n * 4
                        next_free_block_r = docs_rsrc[free_block+4:free_block+8]
                        docs_rsrc[new_free_block:new_free_block+8] = (
                            IO.encode_uint32(size - frequency - 3)
                            + next_free_block_r)
                        # Insert new free block
                        if previous_block_n is None:
                            docs_rsrc[8:12] = IO.encode_link(new_free_block_n)
                            # Update in memory
                            docs_handler.state.first_empty = new_free_block_n
                        else:
                            previous_block = 12 + previous_block_n * 4
                            docs_rsrc[previous_block+4:previous_block+8] = (
                                IO.encode_link(new_free_block_n))
                        break
                    elif frequency + 3 == size:
                        # Pop block
                        if previous_block_n is None:
                            docs_rsrc[8:12] = next_r
                            # Update in memory
                            next_n = IO.decode_link(next_r)
                            docs_handler.state.first_empty = next_n
                        else:
                            previous_block = 12 + previous_block_n * 4
                            docs_rsrc[previous_block+4:previous_block+8] = (
                                next_r)
                        break
                    else:
                        previous_block_n = free_block_n
                        free_block_n = IO.decode_link(head[4:8])

                # Create new block if needed
                if free_block_n is None:
                    free_block_n = docs_handler.state.number_of_slots
                    free_block = 12 + free_block_n * 4
                    number_of_slots = free_block_n + frequency + 3
                    docs_rsrc[4:8] = IO.encode_uint32(number_of_slots)
                    # Update in memory
                    docs_handler.state.number_of_slots = number_of_slots

                # Fill the block
                docs_rsrc[free_block:free_block+12+(frequency*4)] = (
                    IO.encode_uint32(doc_number)
                    + IO.encode_uint32(frequency)
                    + fdoc_slot_r
                    + ''.join([ IO.encode_uint32(x) for x in doc_positions]))
                tree_rsrc[tree_slot+4:tree_slot+8] = IO.encode_link(free_block_n)
                # Update 'fdoc_slot_*'
                fdoc_slot_n = free_block_n
                fdoc_slot_r = IO.encode_link(fdoc_slot_n)


    def _unindex_term(self, word, documents):
        """
        Un-indexes the given term. The parameter 'documents' is a list with
        the numbers of the documents that must be un-indexed.
        """
        if word:
            if self.children is None:
                self.load_children()

            prefix, suffix = word[0], word[1:]
            if prefix in self.children:
                subtree = self.children[prefix]
                subtree._unindex_term(suffix, documents)
        else:
            if self.documents is None:
                self.load_documents()
            for doc_number in documents:
                del self.documents[doc_number]
            # Update resource
            tree_rsrc = self.root.tree_handler.resource
            docs = self.root.docs_handler
            docs_rsrc = docs.resource
            # Search the document block
            tree_slot = 16 + self.slot * 16
            docs_slot_r = tree_rsrc[tree_slot+4:tree_slot+8]
            docs_slot_n = IO.decode_link(docs_slot_r)
            # Free block
            prev_slot_n = prev_slot = None
            while documents and docs_slot_n is not None:
                docs_slot = 12 + docs_slot_n * 4
                header = docs_rsrc[docs_slot:docs_slot+12]
                x = IO.decode_uint32(header[0:4])
                frequency = IO.decode_uint32(header[4:8])
                next_slot_r = header[8:12]
                next_slot_n = IO.decode_link(next_slot_r)
                if x in documents:
                    documents.remove(x)
                    # Remove from the documents list
                    if prev_slot_n is None:
                        tree_rsrc[tree_slot+4:tree_slot+8] = next_slot_r
                    else:
                        docs_rsrc[prev_slot+8:prev_slot+12] = next_slot_r
                    # Add to the free list
                    first_free_block_r = docs_rsrc[8:12]
                    docs_rsrc[docs_slot:docs_slot+8] = (
                        IO.encode_uint32(frequency + 3)
                        + first_free_block_r)
                    docs_rsrc[8:12] = docs_slot_r
                    # Update on memory
                    docs.state.first_empty = docs_slot_n
                else:
                    prev_slot_n, prev_slot = docs_slot_n, docs_slot
                # Next
                docs_slot_n = next_slot_n
                docs_slot_r = next_slot_r


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


    def search_range(self, left, right):
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
                self.load_documents()

            for n in self.documents:
                documents[n] = len(self.documents[n])

        # Children
        if self.children is None:
            self.load_children()

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
            child_documents = self.children[c].search_range(c_left, c_right)
            for n in child_documents:
                if n in documents:
                    documents[n] += child_documents[n]
                else:
                    documents[n] = child_documents[n]
                
        return documents


    ########################################################################
    # Debugging
    ########################################################################
##    def show_for_humans(self, indent=0):
##        s = u''
##        for key, tree in self.children.items():
##            s = s + '%s%s: %s\n' % (' '*indent, key, tree.documents)
##            s += tree.show_for_humans(indent + len(key))
##        return s



class IIndex(Folder):

    def get_skeleton(self):
        return {'tree': IIndexTree(),
                'documents': IIndexDocuments()}


    def _get_handler(self, segment, resource):
        name = segment.name
        if name == 'tree':
            return IIndexTree(resource)
        elif name == 'documents':
            return IIndexDocuments(resource)
        return Folder._get_handler(self, segment, resource)


    ########################################################################
    # Load / Save
    ########################################################################
    def _load_state(self, resource):
        Folder._load_state(self, resource)
        state = self.state

        state.tree_handler = tree_handler = self.get_handler('tree')
        state.docs_handler = docs_handler = self.get_handler('documents')
        # The tree
        state.root = Tree(state, None)
        state.root.documents = {}
        state.root.children = {}

        tree_rsrc = tree_handler.resource
        child_n = tree_handler.state.first_slot
        while child_n is not None:
            child = 16 + child_n * 16
            c = IO.decode_character(tree_rsrc[child:child+4])
            tree = Tree(state, child_n)
            state.root.children[c] = tree
            # Next
            child_n = IO.decode_link(tree_rsrc[child+12:child+16])

        # The state
        state.added_terms = {}
        state.removed_terms = {}


    def _save_state(self, resource):
        # XXX We don't use the given resource!!!

        state = self.state
        # Open resources
        state.tree_handler.resource.open()
        state.docs_handler.resource.open()
        # Removed terms
        for term, documents in state.removed_terms.items():
            state.root._unindex_term(term, documents)
        self.removed_terms = {}
        # Added terms
        _index_term = state.root._index_term
        for term, documents in self.state.added_terms.items():
            _index_term(term, documents)
        state.added_terms = {}
        # Close resources
        state.tree_handler.resource.close()
        state.docs_handler.resource.close()


    ########################################################################
    # Public API
    ########################################################################
    def index_term(self, term, doc_number, position):
        state = self.state
        # Removed terms
        if term in state.removed_terms:
            if doc_number in state.removed_terms[term]:
                del state.removed_terms[term][doc_number]
        # Added terms
        documents = state.added_terms.setdefault(term, {})
        positions = documents.setdefault(doc_number, set())
        positions.add(position)


    def unindex_term(self, term, doc_number):
        state = self.state
        # Added terms
        if term in state.added_terms:
            if doc_number in state.added_terms[term]:
                del state.added_terms[term][doc_number]
                return
        # Removed terms
        documents = state.removed_terms.setdefault(term, set())
        documents.add(doc_number)


    def search_word(self, word):
        state = self.state
        # Open resources
        state.tree_handler.resource.open()
        state.docs_handler.resource.open()

        documents = state.root.search_word(word)
        # Remove documents
        if word in state.removed_terms:
            for doc_number in state.removed_terms[word]:
                if doc_number in documents:
                    del documents[doc_number]
        # Add documents
        if word in state.added_terms:
            for doc_number, positions in state.added_terms[word].items():
                if doc_number in documents:
                    # XXX We ever reach this case?
                    documents[doc_number] |= positions
                else:
                    documents[doc_number] = positions

        # Close resources
        state.tree_handler.resource.close()
        state.docs_handler.resource.close()

        return documents


    def search_range(self, left, right):
        state = self.state
        # Open resources
        state.tree_handler.resource.open()
        state.docs_handler.resource.open()

        documents = state.root.search_range(left, right)
        # XXX We still need to consider removed and added terms, otherwise
        # we may get inaccurate results.

        # Close resources
        state.tree_handler.resource.close()
        state.docs_handler.resource.close()

        return documents
