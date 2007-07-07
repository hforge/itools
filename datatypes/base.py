# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class DataType(object):

    default = None


    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])


    @staticmethod
    def decode(data):
        raise NotImplementedError


    @staticmethod
    def encode(value):
        raise NotImplementedError


    @staticmethod
    def is_valid(value):
        return True
