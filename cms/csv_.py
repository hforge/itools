# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from itools.csv.itools_csv import CSV as iCSV, Row as iRow
from itools.stl import stl

# Import from ikaaro
from Handler import Node
from text import Text
from utils import comeback
from registry import register_object_class


class Row(iRow, Node):

    class_title = u'CSV Row'
    class_icon48 = 'images/Text48.png'
    class_views = [['view'],
                   ['edit_form']]


    def get_mtime(self):
        return self.parent.get_mtime()


    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self, context):
        namespace = {}
        namespace['row'] = self

        handler = self.get_handler('/ui/CSVRow_view.xml')
        return stl(handler, namespace)


    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Edit'
    def edit_form(self, context):
        namespace = {}
        namespace['row'] = self

        handler = self.get_handler('/ui/CSVRow_edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        column = context.get_form_value('column')
        self.__init__(column)
        self.parent.set_changed()

        message = self.gettext(u'Changes saved.')
        comeback(message)



class CSV(Text, iCSV):

    class_id = 'text/comma-separated-values'
    class_title = u'Comma Separated Values'
    class_views = [['view'],
                   ['externaledit'],
                   ['edit_metadata_form'],
                   ['history_form']]


    row_class = Row

##    def _load_state(self, resource):
##        data = resource.read()

##        lines = []
##        index = 0
##        for line in parse(data, self.schema):
##            row = Row(line)
##            row.index = index
##            lines.append(row)
##            index = index + 1

##        self.lines = lines
##        self.encoding = self.guess_encoding(data)


    #########################################################################
    # User Interface
    #########################################################################
    edit_form__access__ = False


    def view(self, context):
        namespace = {}
        namespace['rows'] = self.lines
        handler = self.get_handler('/ui/CSV_view.xml')
        return stl(handler, namespace)


register_object_class(CSV)
