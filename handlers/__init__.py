# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


"""
This package provides and abstraction layer for files, directories and links.
There are two key concepts, resources and handlers.

A resource is anything that behaves like a file (it contains an array of
bytes), as a directory (it contains other resources) or as a link (it
contains a path or an uri to another resource). Doesn't matters wether
a resource lives in the local file system, in a database or is a remote
object accessed with an URI.

A resource handler adds specific semantics to different resources, for
example there is a handler to manage XML files, another to manage PO
files, etc...
"""



# Import from Python
from mimetypes import MimeTypes
from types import StringTypes

# Import from itools
from itools.resources import base, get_resource

# Import from itools.handlers
import CSV
import File
import Folder
import PO
import Text


############################################################################
# The handlers database
############################################################################

class Database(MimeTypes, object):
    """
    This class represents a database that associates resource types to
    resource handlers.

    A resource type is a tuple with two elements. The first one is the
    a number that says wether the resource is a file or a directory,
    the second one is an string that details the file or diretory type.
    For files the mime standard is used.

    For example, the type of an XML file is (0, 'text/xml').
    """

    def __init__(self, filenames=(), strict=True):
        MimeTypes.__init__(self, filenames, strict)

        self.file_handlers = {}
        self.folder_handlers = {}

        # Initialize with the built-in handlers
        self.set_file_handler('', File.File)
        self.set_file_handler('text', Text.Text)
        self.set_file_handler('text/comma-separated-values', CSV.CSV, '.csv')
        self.set_file_handler('text/po', PO.PO, '.po')
        self.set_folder_handler('', Folder.Folder)


    #########################################################################
    # API
    #########################################################################
    def set_file_handler(self, resource_type, handler, extensions=[]):
        """
        Associates a handler class to a resource type (for file resources).
        """
        self.file_handlers[resource_type] = handler

        # Register the extensions
        if isinstance(extensions, StringTypes):
            extensions = [extensions]

        for extension in extensions:
            self.add_type(resource_type, extension)


    def set_folder_handler(self, resource_type, handler):
        """
        Associates a handler class to a resource type (for file resources).
        """
        self.folder_handlers[resource_type] = handler


    def guess_mimetype(self, name, resource):
        """
        Try to guess the mimetype for a resource, given the resource itself
        and its name. To guess from the name we need to extract the type
        extension, we use an heuristic for this task, but it needs to be
        improved because there are many patterns:

        <name>                                 README
        <name>.<type>                          index.html
        <name>.<type>.<language>               index.html.en
        <name>.<type>.<language>.<encoding>    index.html.en.UTF-8
        <name>.<type>.<compression>            itools.tar.gz
        etc...

        And even more complex, the name could contain dots, or the filename
        could start by a dot (a hidden file in Unix systems).

        XXX Use magic numbers too (like file -i).
        """
        # Maybe the resource knows
        mimetype = resource.get_mimetype()

        # If it does not, try guess from the name
        if not mimetype:
            # Get the extension (use an heuristic)
            name = name.split('.')
            if len(name) > 1:
                if len(name) > 2:
                    extension = name[-2]
                else:
                    extension = name[-1]
                mimetype, encoding = database.guess_type('.%s' % extension)

        return mimetype


    def get_handler(self, resource, mimetype):
        if mimetype is None:
            mimetype = ''

        """Receives a resource and a mimetype, returns a handler."""
        # Get the right handlers database
        if isinstance(resource, base.File):
            database = self.file_handlers
        elif isinstance(resource, base.Folder):
            database = self.folder_handlers
        else:
            raise ValueError, 'resource is not a file nor a folder'

        # Get the minimal type there is a handler for
        type = mimetype
        while type not in database:
            type = '/'.join(type.split('/')[:-1])

        # Get the handler class
        handler_class_or_factory = database[type]
        # Build the handler
        handler = handler_class_or_factory(resource)
        # Fix the mimetype if needed
        if not handler.mimetype:
            handler.mimetype = mimetype
        # Return the handler
        return handler


############################################################################
# Default database
database = Database()


############################################################################
# API
############################################################################
def get_handler(uri, database=database):
    """
    Returns a resource handler from a path, where path can be a list of
    strings or an string of the form 'a/b/c'.

    The 'root' parameter is a folder resource (an instance of the class
    'itools.resources.base.Folder'). If the path is relative the requested
    resource will be searched starting from the given root; if none is
    provided the root will be the current filesystem directory.

    The paramater 'database' is an instance of the 'Database' class, which
    keeps the association between resource types and handler classes. By
    default the 'handlers' instance within this module is used.

    The 'accept' parameter is used for language negotiation, it must be an
    instance of the class 'itools.i18n.accept.AcceptLanguage'. If provided,
    when the requested resource does not exists, a variant will be searched
    and returned if found (for example 'index.html.en' is a variant of
    'index.html'), which variant is returned depends on language negotiation.
    By default 'accept' is None, what means that this feature is disabled.
    """
    # XXX A class URI should be developed, and the uri parameter should be
    # an instance of it

    # Get the resource
    resource = get_resource(uri)
    # Get the mimetype
    name = uri.split('/')[-1]
    mimetype = database.guess_mimetype(name, resource)
    # Build the handler
    handler = database.get_handler(resource, mimetype)

    return handler
