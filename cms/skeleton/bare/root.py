# -*- coding: UTF-8 -*-
# Copyright (C) ${YEAR} ${AUTHOR_NAME} <${AUTHOR_EMAIL}>
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

# Import from itools
from itools.cms.registry import register_object_class
from itools.cms.root import Root as BaseRoot

# Import from here
from base import Handler



class Root(Handler, BaseRoot):

    class_id = '${PACKAGE_NAME}'
    class_title = u'TITLE'



register_object_class(Root)
