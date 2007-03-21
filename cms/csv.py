# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.datatypes import Integer
from itools.csv.csv import CSV as iCSV, Row as iRow
from itools.stl import stl

# Import from ikaaro
from Handler import Node
from text import Text
from registry import register_object_class
import widgets


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
        columns = self.columns
        rows = []

        for i, row in enumerate(self):
            rows.append({
                'column': columns[i] if columns else '',
                'value': row})

        namespace = {}
        namespace['rows'] = rows

        handler = self.get_handler('/ui/CSVRow_view.xml')
        return stl(handler, namespace)


    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Edit'
    def edit_form(self, context):
        columns = self.columns
        rows = []

        for i, row in enumerate(self):
            rows.append({
                'column': columns[i] if columns else '',
                'value': row})

        namespace = {}
        namespace['rows'] = rows

        handler = self.get_handler('/ui/CSVRow_edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        column = context.get_form_values('column')
        self.__init__(column)
        self.parent.set_changed()

        return context.come_back(u'Changes saved.')



class CSV(Text, iCSV):

    class_id = 'text/comma-separated-values'
    class_title = u'Comma Separated Values'
    class_views = [['view'],
                   ['add_row_form'],
                   ['externaledit', 'upload_form'],
                   ['edit_metadata_form'],
                   ['history_form']]


    row_class = Row


    #########################################################################
    # User Interface
    #########################################################################
    edit_form__access__ = False


    #########################################################################
    # View
    def view(self, context):
        namespace = {}

        # The input parameters
        start = context.get_form_value('batchstart', type=Integer, default=0)
        size = 50

        # The batch
        total = len(self.lines)
        namespace['batch'] = widgets.batch(context.uri, start, size, total,
                                           self.gettext)

        # The table
        columns = [ (x, x) for x in self.columns ]
        rows = []
        for row in self.lines[start:start+size]:
            rows.append({})
            for column in self.columns:
                rows[-1][column] = row.get_value(column)
        # TODO Sort
        sortby = None
        sortorder = None
        # TODO Remove
        actions = []
        namespace['table'] = widgets.table(columns, rows, sortby, sortorder,
                                           actions)

        handler = self.get_handler('/ui/CSV_view.xml')
        return stl(handler, namespace)


    #########################################################################
    # Add
    add_row_form__access__ = 'is_allowed_to_edit'
    add_row_form__label__ = u'Add'
    def add_row_form(self, context):
        namespace = {}

        columns = []
        for column_name in self.columns:
            column = {}
            column['title'] = column_name
            # FIXME The widget may be something else than an input field
            # (e.g. a select field)
            column['widget'] = '<input type="text" name="%s" />' % column_name
            columns.append(column)
        namespace['columns'] = columns

        handler = self.get_handler('/ui/CSV_add_row.xml')
        return stl(handler, namespace)


    add_row_action__access__ = 'is_allowed_to_edit'
    def add_row_action(self, context):
        row = []
        for name in self.columns:
            value = context.get_form_value(name)
            datatype = self.schema[name]
            value = datatype.decode(value)
            row.append(value)

        self.add_row(row)

        message = u'New row added.'
        return context.come_back(message)



register_object_class(CSV)
register_object_class(CSV, 'text/x-comma-separated-values')

