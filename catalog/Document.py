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


# Import from itools
from itools.handlers.File import File
from itools.handlers.Folder import Folder
import IO



class IndexedField(File):
    def get_skeleton(self):
        return IO.encode_uint32(0)


    def _load(self):
        r = self.resource
        self.number_of_terms = IO.decode_uint32(r[:4])
        self.terms = []

        data = r[4:]
        for i in range(self.number_of_terms):
            term, data = IO.decode_string(data)
            self.terms.append(term)


    def add_term(self, term):
        self.number_of_terms += 1
        self.terms.append(term)
        # Update the resource
        self.resource[:4] = IO.encode_uint32(self.number_of_terms)
        self.resource.append(IO.encode_string(term))



class StoredField(File):
    def get_skeleton(self, data=u''):
        return IO.encode_string(data)


    def _load(self):
        data = self.resource.get_data()
        self.value = IO.decode_string(data)[0]



class Document(Folder):
    def _get_handler(self, segment, resource):
        name = segment.name
        if name.startswith('i'):
            return IndexedField(resource)
        elif name.startswith('s'):
            return StoredField(resource)
        return Folder._get_handler(self, segment, resource)
