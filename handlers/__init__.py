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
import mimetypes

# Import from itools
from itools.resources import base, get_resource

# Import from itools.handlers
import Handler
import CSV
import File
import Folder
import PO
import Text



mimetypes.add_type('text/po', '.po')
mimetypes.add_type('text/comma-separated-values', '.csv')
mimetypes.add_type('application/xhtml+xml', '.xhtml')


def guess_mimetype(name, resource):
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
            mimetype, encoding = mimetypes.guess_type('.%s' % extension)

    return mimetype



def get_handler(uri):
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
    mimetype = guess_mimetype(name, resource)
    # Build the handler
    return Handler.Handler.build_handler(resource, mimetype)



# Initialize with the built-in handlers
for handler_class in File.File, Text.Text, CSV.CSV, PO.PO, Folder.Folder:
    Handler.Handler.register_handler_class(handler_class)
