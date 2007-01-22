# -*- coding: UTF-8 -*-
# Copyright (C) 2001-2007 J. David Ibáñez <jdavid@itaapy.com>
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

"""
This module implements the Accept-Charset and Accept-Language request
headers of the HTTP protocol.

There're six classes: Node, Root, CharsetNode, LanguageNode, AcceptCharset
and AcceptLanguage.

The public interface is provided by the two last classes, AcceptCharset and
AcceptLanguage. The other four shouldn't be used directly.
"""

# Import from the future
from __future__ import absolute_import

# Import from the Standard Library
from locale import getdefaultlocale



class Node(object):
    """
    Base class that represents a node in a tree.
    """

    def __init__(self):
        self.quality = None
        self.children = {}


    # Mapping interface, and other Python standard methods
    def __setitem__(self, key, quality):
        """
        Sets the quality for a language. If the language doesn't exists
        it's added.
        """
        node = self._getnode(key)
        node.quality = quality


    def __delitem__(self, key):
        if isinstance(key, str):
            if key == '*':
                key = []
            else:
                key = key.split('-')

        if len(key) == 0:
            self.quality = None
        else:
            child = self.children[key[0]]
            del child[key[1:]]
            if len(child.children) == 0 and child.quality is None:
                del self.children[key[0]]


    def __str__(self):
        d = {}
        for key, value in self.children.items():
            d[key] = str(value)

        return "%s %s" % (self.get_quality(), d)


    def get_quality(self):
        """
        Returns the quality of this node.
        """
        if self.quality is None:
            return max([ x.get_quality() for x in self.children.values() ])

        return self.quality



class Root(Node):
    """
    Base class that represents the root of a tree.
    """

    # Hack to let access from Zope restricted code (Zope sucks).
    __allow_access_to_unprotected_subobjects__ = 1


    def __init__(self, accept):
        Node.__init__(self)

        self.quality = 0.0

        # Parse the accept string and initialize the tree.
        accept = self.parse(accept)
        for key, quality in accept.items():
            self[key] = quality


    def parse(self, accept):
        """
        From a string formatted as specified in the RFC2616, it builds a data
        structure which provides a high level interface to implement language
        negotiation.
        """
        aux = {}
        for x in accept.split(','):
            x = x.strip()
            x = x.split(';')

            # Get the quality
            if len(x) == 2:
                quality = x[1]            # Get the quality
                quality = quality.strip()
                quality = quality[2:]     # Get the number (remove "q=")
                quality = float(quality)  # Change it to float
            else:
                quality = 1.0

            aux[x[0]] = quality

        return aux


    def __str__(self):
        d = {}
        for key, value in self.children.items():
            d[key] = str(value)

        return "%s %s" % (self.quality, d)


    # Public interface
    def get_quality(self, key):
        """
        Returns the quality of the given node
        """
        try:
            node = self[key]
        except KeyError:
            return self.quality

        return node.get_quality()


    def set(self, key, quality):
        """
        Sets the quality for a language, only if the current quality is
        not bigger. If the language doesn't exists it's added.
        """
        node = self._getnode(key)
        if quality > node.quality:
            node.quality = quality



class CharsetNode(Node):
    """
    Implements the node of a Accept-Charset tree.
    """

    def __getitem__(self, key):
        """
        Traverses the tree to get the object.
        """
        return self.children[key]



class LanguageNode(Node):
    """
    Implements a node of a Accept-Language tree.
    """

    def _getnode(self, key):
        """
        Returns the required node. If it doesn't exists it's created.
        """
        if isinstance(key, str):
            if key == '*':
                key = []
            else:
                key = key.split('-')

        if len(key) == 0:
            return self
        else:
            accept = self.children.setdefault(key[0], LanguageNode())
            return accept._getnode(key[1:])


    def __getitem__(self, key):
        """
        Traverses the tree to get the object.
        """
        key = key.split('-', 1)
        x = key[0]

        try:
            y = key[1]
        except IndexError:
            return self.children[x]
        else:
            return self.children[x][y]



class AcceptCharset(Root, CharsetNode):
    """
    Implements the Accept-Charset tree.
    """

    def parse(self, accept):
        accept = Root.parse(self, accept)
        if not accept.has_key('*') and not accept.has_key('ISO-8859-1'):
            accept['ISO-8859-1'] = 1.0

        return accept


    def _getnode(self, key):
        """
        Behaves like a simple dictionary, only one level.
        """
        if key == '*':
            return self
        return self.children.setdefault(key, CharsetNode())            



class AcceptCharsetType(object):

    @staticmethod
    def decode(data):
        return AcceptCharset(data)


    @staticmethod
    def encode(value):
        return str(value)



class AcceptLanguage(Root, LanguageNode):
    """
    Implements the Accept-Language tree.
    """

    def select_language(self, languages):
        """
        This is the selection language algorithm, it returns the user
        prefered language for the given list of available languages,
        if the intersection is void returns None.
        """
        language, quality = None, 0.0

        for lang in languages:
            q = self.get_quality(lang)
            if q > quality:
                language, quality = lang, q

        return language



class AcceptLanguageType(object):

    @staticmethod
    def decode(data):
        return AcceptLanguage(data)


    @staticmethod
    def encode(value):
        return str(value)



##class AcceptLanguageNode(AcceptNode):
##    """
##    This class is a recursive representation of a tree.

##    To implement the tree behaviour the 'children' attribute is used,
##    it's a mapping object, the value is another AcceptLanguageNode.

##    This class also stores the quality of the node, if its value is None,
##    it means that the quality is the maximum of the qualities of their
##    children.

##    This class provides a subset of a mapping interface.
##    """



def get_accept():
    locale = getdefaultlocale()
    language = locale[0]
    language = language.replace('_', '-')
    return AcceptLanguage(language)


