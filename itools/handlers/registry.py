# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007, 2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2011 Hervé Cauwelier <herve@oursours.net>
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


handler_classes = {}


def register_handler_class(handler_class):
    for mimetype in handler_class.class_mimetypes:
        handler_classes[mimetype] = handler_class


def get_handler_class_by_mimetype(mimetype, soft=False):
    if mimetype is not None:
        if mimetype in handler_classes:
            return handler_classes[mimetype]

        main_type = mimetype.split('/')[0]
        if main_type in handler_classes:
            return handler_classes[main_type]

    if soft:
        return None

    raise ValueError(mimetype)
