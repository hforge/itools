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

Every node also contains which documents contain the word and how many
times, for example (if the word 'hello' appears once in the first document
and the word 'here' appears twice in the second document):

  h -- e -- l -- l -- o (0: 1)
         \- r -- e (1: 2)

On the file structure every inverted index (there is one for each field
being indexed) is a folder which contains two files: 'tree' and 'documents'.
The first file (tree) represents on the files the same tree structure, the
second file (documents) records the appearences of each word (document
numbers and frequency).
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


    __version__ = '20040723'


    def get_skeleton(self):
        # The header
        version = IO.encode_version(self.__version__)
        number_of_slots = IO.encode_uint32(0)
        first_slot = IO.encode_link(None)
        first_empty = IO.encode_link(None)
        header = version + number_of_slots + first_slot + first_empty

        return header


    def _load(self, resource):
        # The header
        self.version = IO.decode_version(resource[:4])
        self.number_of_slots = IO.decode_uint32(resource[4:8])
        self.first_slot = IO.decode_link(resource[8:12])
        self.first_empty = IO.decode_link(resource[12:16])


    def _get_free_slot(self):
        """
        Internal method that returns a free slot. If none exists a new one
        is allocated.

        Beware this method leaves the resource in an inconsistent state,
        the method that calls it is responsible to use the slot so the
        resource becomes consistent.
        """
        r = self.resource
        if self.first_empty is None:
            slot_number = self.number_of_slots
            # Number of slots
            self.number_of_slots += 1
            r[4:8] = IO.encode_uint32(self.number_of_slots)
            # Append the new slot to the end of the file
            base = 16 + slot_number * 16
            character = '\x00\x00\x00\x00'
            frequency = IO.encode_link(None)
            first_child = IO.encode_link(None)
            next_sibling = IO.encode_link(None)
            r[base:base+16] = character + frequency + first_child \
                              + next_sibling
        else:
            slot_number = self.first_empty
            # Update first empty
            base = 16 + self.first_empty * 16
            first_empty_link = r[base+12:base+16]
            self.first_empty = IO.decode_link(first_empty_link)
            r[12:16] = first_empty_link

        return slot_number




class IIndexDocuments(File):
    """
    The header format is:

      - version number (4 bytes)
      - number of slots (4 bytes)
      - first empty slot (4 bytes)

    Each slot is made of:

      - document number (4 bytes)
      - frequency (4 bytes)
      - next document (4 bytes)
    """


    __version__ = '20040723'


    def get_skeleton(self):
        version = IO.encode_version(self.__version__)
        number_of_slots = IO.encode_uint32(0)
        first_empty = IO.encode_link(None)
        return version + number_of_slots + first_empty
        

    def _load(self, resource):
        # The header
        self.version = IO.decode_version(resource[:4])
        self.number_of_slots = IO.decode_uint32(resource[4:8])
        self.first_empty = IO.decode_link(resource[8:12])


    def _get_free_slot(self):
        """
        Returns the slot number of a free slot, allocates a new one if
        needed.
        """
        r = self.resource
        if self.first_empty is None:
            slot_number = self.number_of_slots
            # Number of slots
            self.number_of_slots += 1
            r[4:8] = IO.encode_uint32(self.number_of_slots)
            # Append the new slot to the end of the file
            base = 12 + slot_number * 12
            document_number = IO.encode_link(None)
            frequency = IO.encode_uint32(0)
            next = IO.encode_link(None)
            r[base:base+12] = document_number + frequency + next
        else:
            slot_number = self.first_empty
            # Update first empty
            base = 12 + self.first_empty * 12
            first_empty_link = r[base+8:base+12]
            self.first_empty = IO.decode_link(first_empty_link)
            r[8:12] = first_empty_link

        return slot_number


    def _get_document_slot(self, slot_number, document_number):
        """
        Searches and returns the slot number for the given document, starting
        from the given base slot. If it is not found None is returned.
        """
        r = self.resource
        while True:
            base = 12 + slot_number * 12
            x = IO.decode_uint32(r[base:base+4])
            if x == document_number:
                return slot_number
            slot_number = IO.decode_link(r[base+8:base+12])
            if slot_number is None:
                return None
        raise ValueError, 'The database is corrupted!!'



class Tree(object):
    """
    This class represents any node in the search tree (i.e. inverted index).
    """

    def __init__(self, root, slot):
        # The root is also the resource handler.
        self.root = root
        self.slot = slot
        self.documents = {}
        self.children = {}


    def _load(self):
        tree_rsrc = self.root.tree_handler.resource
        slot = 16 + self.slot * 16
        # Documents
        doc_rsrc = self.root.docs_handler.resource
        doc_slot_n = IO.decode_link(tree_rsrc[slot+4:slot+8])
        while doc_slot_n is not None:
            doc_slot = 12 + doc_slot_n * 12
            doc_number = IO.decode_uint32(doc_rsrc[doc_slot:doc_slot+4])
            self.documents[doc_number] = documents = []
            frequency = IO.decode_uint32(doc_rsrc[doc_slot+4:doc_slot+8])
            for i in range(frequency):
                documents.append(None)
            # Next
            doc_slot_n = IO.decode_link(doc_rsrc[doc_slot+8:doc_slot+12])
        # Children
        child_n = IO.decode_link(tree_rsrc[slot+8:slot+12])
        while child_n is not None:
            child = 16 + child_n * 16
            c = IO.decode_character(tree_rsrc[child:child+4])
            tree = Tree(self.root, child_n)
            self.children[c] = tree
            tree._load()
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
                r[free_slot:free_slot+4] = IO.encode_character(prefix)
                r[free_slot+4:free_slot+8] = IO.encode_link(None)
                r[free_slot+8:free_slot+12] = IO.encode_link(None)
                # Prepend the new slot
                this_slot = 16 + self.slot * 16
                r[free_slot+12:free_slot+16] = r[this_slot+8:this_slot+12]
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
            for doc_number, doc_positions in documents.items():
                if doc_number in self.documents:
                    positions = self.documents[doc_number]
                    positions.extend(doc_positions)
                    # Update slot
                    doc_slot_n = docs_handler._get_document_slot(fdoc_slot_n,
                                                                 doc_number)
                    doc_slot = 12 + doc_slot_n * 12
                    # Calculate the frequency
                    frequency = len(positions)
                else:
                    self.documents[doc_number] = doc_positions
                    # Update slot
                    doc_slot_n = docs_handler._get_free_slot()
                    doc_slot = 12 + doc_slot_n * 12
                    docs_rsrc[doc_slot:doc_slot+4] = IO.encode_uint32(doc_number)
                    docs_rsrc[doc_slot+8:doc_slot+12] = fdoc_slot_r
                    tree_rsrc[tree_slot+4:tree_slot+8] = IO.encode_link(doc_slot_n)
                    # Update 'fdoc_slot_*'
                    fdoc_slot_n = doc_slot_n
                    fdoc_slot_r = IO.encode_link(fdoc_slot_n)
                    # Calculate the frequency
                    frequency = len(doc_positions)
                docs_rsrc[doc_slot+4:doc_slot+8] = IO.encode_uint32(frequency)


    def _unindex_term(self, word, doc_number):
        if word:
            prefix, suffix = word[0], word[1:]
            if prefix in self.children:
                subtree = self.children[prefix]
                subtree._unindex_term(suffix, doc_number)
        else:
            del self.documents[doc_number]
            # Update resource
            tree_rsrc = self.root.tree_handler.resource
            docs = self.root.docs_handler
            docs_rsrc = docs.resource
            # Search the document slot
            tree_slot = 16 + self.slot * 16
            docs_slot_r = tree_rsrc[tree_slot+4:tree_slot+8]
            docs_slot_n = IO.decode_link(docs_slot_r)
            # Free slot
            prev_slot_n = prev_slot = None
            while docs_slot_n is not None:
                docs_slot = 12 + docs_slot_n * 12
                x = IO.decode_uint32(docs_rsrc[docs_slot:docs_slot+4])
                next_slot_r = docs_rsrc[docs_slot+8:docs_slot+12]
                next_slot_n = IO.decode_link(next_slot_r)
                if x == doc_number:
                    # Remove from the documents list
                    if prev_slot_n is None:
                        tree_rsrc[tree_slot+4:tree_slot+8] = next_slot_r
                    else:
                        docs_rsrc[prev_slot+8:prev_slot+12] = next_slot_r
                    # Add to the free list
                    old_first_r = docs_rsrc[8:12]
                    docs_rsrc[docs_slot+8:docs_slot+12] = old_first_r
                    docs_rsrc[8:12] = IO.encode_link(docs_slot_n)
                    # Update on memory
                    docs.first_empty = docs_slot_n
                    # Done
                    break
                # Next
                prev_slot_n, prev_slot = docs_slot_n, docs_slot
                docs_slot_n = next_slot_n
            else:
                raise ValueError, 'The database is corrupted!!'


    def search_word(self, word):
        if word:
            prefix, suffix = word[0], word[1:]
            subtree = self.children.get(prefix, None)
            if subtree is None:
                return {}
            else:
                return subtree.search_word(suffix)
        else:
            documents = {}
            for doc_number, positions in self.documents.items():
                weight = len(positions)
                documents[doc_number] = weight
            return documents


    ########################################################################
    # Debugging
    ########################################################################
    def show_for_humans(self, indent=0):
        s = u''
        for key, tree in self.children.items():
            s = s + '%s%s: %s\n' % (' '*indent, key, tree.documents)
            s += tree.show_for_humans(indent + len(key))
        return s



class IIndex(Folder, Tree):
    def get_skeleton(self):
        return [('tree', IIndexTree()),
                ('documents', IIndexDocuments())]


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
    def _load(self, resource):
        self.tree_handler = tree_handler = self.get_handler('tree')
        self.docs_handler = docs_handler = self.get_handler('documents')
        # The tree
        self.documents = {}
        self.children = {}

        tree_rsrc = tree_handler.resource
        child_n = tree_handler.first_slot
        while child_n is not None:
            child = 16 + child_n * 16
            c = IO.decode_character(tree_rsrc[child:child+4])
            tree = Tree(self, child_n)
            self.children[c] = tree
            tree._load()
            # Next
            child_n = IO.decode_link(tree_rsrc[child+12:child+16])
        # The state
        self.added_terms = {}
        self.removed_terms = {}


    def _save(self):
        # Removed terms
        for term, documents in self.removed_terms.items():
            for doc_number in documents:
                self._unindex_term(term, doc_number)
        self.removed_terms = {}
        # Added terms
        for term, documents in self.added_terms.items():
            self._index_term(term, documents)


    ########################################################################
    # Private API
    ########################################################################
    def _index_term(self, term, documents):
        """
        Indexes the given term. The parameter 'documents' is a mapping
        from document number to list of positions:

          {<document number>: [postion, ...],
           ...}
        """
        prefix, suffix = term[0], term[1:]
        if prefix in self.children:
            subtree = self.children[prefix]
        else:
            # Get an empty slot
            slot_number = self.tree_handler._get_free_slot()
            subtree = self.children[prefix] = Tree(self, slot_number)
            # Update resource
            r = self.tree_handler.resource
            # Update data structure on memory
            base = 16 + slot_number * 16
            r[base:base+4] = IO.encode_character(prefix)
            r[base+4:base+8] = IO.encode_link(None)
            r[base+8:base+12] = IO.encode_link(None)
            # Prepend the new slot
            r[base+12:base+16] = r[8:12]
            r[8:12] = IO.encode_link(slot_number)
        subtree._index_term(suffix, documents)


    ########################################################################
    # Public API
    ########################################################################
    def index_term(self, term, doc_number, position):
        # Removed terms
        if term in self.removed_terms:
            if doc_number in self.removed_terms[term]:
                del self.removed_terms[term][doc_number]
        # Added terms
        documents = self.added_terms.setdefault(term, {})
        positions = documents.setdefault(doc_number, [])
        positions.append(position)


    def unindex_term(self, term, doc_number):
        # Added terms
        if term in self.added_terms:
            if doc_number in self.added_terms[term]:
                del self.added_terms[term][doc_number]
        # Removed terms
        documents = self.removed_terms.setdefault(term, Set())
        documents.add(doc_number)


    def search_word(self, word):
        documents = Tree.search_word(self, word)
        # Remove documents
        if word in self.removed_terms:
            for doc_number in self.removed_terms[word]:
                if doc_number in documents:
                    del documents[doc_number]
        # Add documents
        if word in self.added_terms:
            for doc_number, positions in self.added_terms[word].items():
                documents.setdefault(doc_number, 0)
                documents[doc_number] += len(positions)

        return documents
