# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import mimetypes
import os
import tempfile
from string import translate, maketrans

# Import from itools
from __init__ import get_context
from itools import i18n

# Import from Zope
from Acquisition import aq_base, Explicit
from Globals import package_home
from OFS.Folder import Folder



src = ur""" @¹,;:!¡?ª$£¤+&/\"*#()[]{}'ÄÅÁÀÂÃäåáàâãÇçÉÈÊËéèêëæÍÌÎÏíìîïÑñÖÓÒÔÕØöóòôõøßÜÚÙÛüúùûÝ~ýÿ~^°"""
dst = ur"""___________________________AAAAAAaaaaaaCcEEEEeeeeeIIIIiiiiNnOOOOOOooooooSUUUUuuuuY_yy__-"""

transmap = {}
for i in range(len(src)):
    a, b = src[i], dst[i]
    transmap[ord(a)] = ord(b)


def checkid(id):
    """
    Checks wether th id is or not a valid Zope id. If it is the id is
    returned, but stripped. If it is a bad id None is returned to signal
    the error.
    """
    if isinstance(id, str):
        id = unicode(id, 'utf8')
    id = id.strip().translate(transmap).strip('_')

    # Check wether the id is empty
    if len(id) == 0:
        return None

    # Check for unallowed characters
    for c in id:
        if not c.isalnum() and c not in ('.', '-', '_'):
            return None

    # The id is good
    return str(id)



def addfolder(self, name):
    """
    Adds a Zope folder if it does not exist yet. Returns the folder
    with the acquisition wrapper.
    """
    if not hasattr(aq_base(self), name):
        self._setObject(name, Folder())
        getattr(self, name).id = name

    return getattr(self, name)



#############################################################################
# Content Type
#############################################################################
def guess_contenttype(name, data, file=None):
    """
    Guess content type and encoding.

    XXX We don't deal with encoding (compression) yet.
    """
    # Initialize to None
    content_type = None
    encoding = None # compress (.Z) or gzip (.gz) or None
    text_encoding = None # ascii, latin1, utf8, etc..

    # Look at the file headers
    # XXX Zope 2 specific, remove it?
    if file is not None:
        headers = getattr(file, 'headers', None)
        if headers and headers.has_key('content-type'):
            content_type = headers['content-type']

    # Try to guess content type by the file extension
    if content_type in (None, 'application/octet-stream'):
        content_type, encoding = mimetypes.guess_type(name, 0)

    # Guess the content type by the Unix file command
    if content_type in (None, 'application/octet-stream'):
        filename = tempfile.mktemp()
        open(filename, 'w').write(data)
        content_type = os.popen('file -i %s' % filename).read()
        os.unlink(filename)
        content_type = content_type.split(':',1)[1].split(';')[0].split(',')[0].strip()

        # If unknown restore the correct content type
        if content_type == 'data':
            content_type = 'application/octet-stream'

    # Guess the text encoding
    if content_type.startswith('text/'):
        if content_type == 'text/plain/po':
            po = i18n.parsers.PO(data)
            text_encoding = po.encoding

        # Brute force, likely to get the wrong encoding
        if text_encoding is None:
            for text_encoding in ('ascii', 'iso8859', 'utf8'):
                try:
                    unicode(data, text_encoding)
                except UnicodeError:
                    pass
                else:
                    break

        # Default to UTF-8
        if text_encoding is None:
            text_encoding = 'utf8'

    return content_type, text_encoding




##class File(Explicit):
##    """
##    Loads a file from the filesystem and publish it to the web.

##    XXX Do we really need to inherit from Explicit??
##    """

##    def __init__(self, name, globals, content_type=None):
##        # The data
##        home = package_home(globals)
##        data = open('%s/%s' % (home, name)).read()
##        self.data = data

##        # The content type
##        if content_type is None:
##            content_type, encoding = guess_contenttype(name, data)
##        self.content_type = content_type


##    def index_html(self):
##        """ """
##        response = get_context().response
##        response.set_header('Content-type', self.content_type)
##        return self.data


