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


# Import from Python
import datetime

# Import from itools
from itools.resources import memory
from Handler import Handler



class File(Handler):
    """
    This is the base handler class for any file handler. It is also used
    as the default handler class for any file resource that has not a more
    specific handler.
    """

    def __init__(self, resource=None, **kw):
        if resource is None:
            # No resource given, then we create a dummy one
            data = self.get_skeleton(**kw)
            resource = memory.File(data)

        self.resource = resource
        self.load()


    def _load(self, resource):
        self._data = resource.get_data()
        self._mimetype = resource.get_mimetype()


    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self):
        return ''


    #########################################################################
    # API
    #########################################################################
    def to_str(self):
        return self._data


    def save(self):
        self.resource.set_data(self.to_str())
        self.timestamp = datetime.datetime.now()


    #########################################################################
    # Shorthands (there are chances they will be removed some time in the
    # future, use 'to_str' and 'to_unicode' instead!!)
    def __str__(self):
        return self.to_str()


    def __unicode__(self):
        # The method 'to_unicode' is defined by the subclass 'Text',
        # binary files (those that do not inherit from 'Text') will
        # raise an attribute error.
        return self.to_unicode()


