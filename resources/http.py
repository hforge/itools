# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ib��ez Palomar <jdavid@itaapy.com>
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
    pass



class File(Resource, base.File):

    def get_data(self):
        return urlopen(str(self.uri)).read()


    def get_mimetype(self):
        return urlopen(str(uri)).info().gettype()



def get_resource(netpath):
    return File(netpath)
