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
from urllib import urlopen

# Import from itools
import base
from itools import uri



class Resource(base.Resource):
    """ """

    def __init__(self, reference):
        if not isinstance(reference, uri.Reference):
            netpath = uri.Reference(reference)
        self.reference = reference


    def get_uri(self):
        return str(self.reference)


class File(Resource, base.File):
    """ """

    def __str__(self):
        return urlopen(self.get_uri()).read()


    def get_mimetype(self):
        return urlopen(self.get_uri()).info().gettype()



def get_resource(netpath):
    return File(netpath)
