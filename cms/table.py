# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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

# Import from the Standard Library
from operator import itemgetter

# Import from itools
from itools.datatypes import (DataType, Integer, FileName, is_datatype,
                              Enumerate, Boolean, Date)
from itools.handlers.table import Table as iTable, Record
from itools.i18n import get_language_name
from itools.stl import stl
from itools.rest import checkid
from messages import *
from file import File
from registry import register_object_class
import widgets
from widgets import get_default_widget



class Multiple(DataType):

    def decode(self, data):
        if isinstance(data, list) is True:
            lines = data
        else:
            lines = data.splitlines()

        return [self.type.decode(x)
                for x in lines]



class Table(File, iTable):

    class_id = 'table'
    class_title = u'Table'
    class_views = [['view'],
                   ['add_record_form'],
                   ['edit_metadata_form'],
                   ['history_form']]

    record_class = Record

    @classmethod
    def new_instance_form(cls, context):
        root = context.root

        name = ''
        namespace = {}
        namespace['name'] = name
        # The class id
        namespace['class_id'] = cls.class_id
        # Languages
        languages = []
        website_languages = root.get_property('ikaaro:website_languages')
        default_language = website_languages[0]
        for code in website_languages:
            language_name = get_language_name(code)
            languages.append({'code': code,
                              'name': cls.gettext(language_name),
                              'isdefault': code == default_language})
        namespace['languages'] = languages

        handler = root.get_handler('ui/table/new_instance.xml')
        return stl(handler, namespace)



    @classmethod
    def new_instance(cls, container, context):
        name = context.get_form_value('name')
        title = context.get_form_value('dc:title')
        language = context.get_form_value('dc:language')

        # Check the name
        name = name.strip() or title.strip()
        if not name:
            return context.come_back(MSG_NAME_MISSING)

        name = checkid(name)
        if name is None:
            return context.come_back(MSG_BAD_NAME)

        # Add the language extension to the name
        name = FileName.encode((name, cls.class_extension, language))

        # Check the name is free
        if container.has_handler(name):
            return context.come_back(MSG_NAME_CLASH)

        # Build the object
        handler = cls()
        metadata = handler.build_metadata()
        metadata.set_property('dc:title', title, language=language)
        metadata.set_property('dc:language', language)
        # Add the object
        handler, metadata = container.set_object(name, handler, metadata)

        goto = './%s/;%s' % (name, handler.get_firstview())
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)



    #########################################################################
    # User Interface
    #########################################################################
    def get_fields(self):
        """
        Returns a list of tuples with the name and title of every field.
        """
        fields = []
        for name in self.schema.keys():
            datatype = self.schema[name]
            title = getattr(datatype, 'title', None)
            if title is None:
                title = name
            else:
                title = self.gettext(title)
            fields.append((name, title))

        return fields


    #########################################################################
    # User Interface
    #########################################################################
    edit_form__access__ = False


    #########################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self, context):
        namespace = {}

        # The input parameters
        start = context.get_form_value('batchstart', type=Integer, default=0)
        size = 50

        # The batch
        total = self.get_n_records()
        namespace['batch'] = widgets.batch(context.uri, start, size, total,
                                           self.gettext)

        # The table
        actions = []
        if total:
            ac = self.get_access_control()
            if ac.is_allowed_to_edit(context.user, self):
                actions = [('del_record_action', u'Remove', 'button_delete',None)]

        fields = self.get_fields()
        fields.insert(0, ('index', u'id'))
        records = []

        for record in self.get_records():
            id = record.id
            records.append({})
            records[-1]['id'] = str(id)
            records[-1]['checkbox'] = True
            # Fields
            records[-1]['index'] = id, ';edit_record_form?id=%s' % id
            for field, field_title in fields[1:]:
                value = self.get_value(record, field)
                datatype = self.get_datatype(field)

                multiple = getattr(datatype, 'multiple', False)
                if multiple is True:
                    value.sort()
                    if len(value) > 0:
                        rmultiple = len(value) > 1
                        value = value[0]
                    else:
                        rmultiple = False
                        value = None

                is_enumerate = getattr(datatype, 'is_enumerate', False)
                if is_enumerate:
                    records[-1][field] = datatype.get_value(value)
                else:
                    records[-1][field] = value

                if multiple is True:
                    records[-1][field] = (records[-1][field], rmultiple)
        # Sorting
        sortby = context.get_form_value('sortby')
        sortorder = context.get_form_value('sortorder', 'up')
        if sortby:
            records.sort(key=itemgetter(sortby), reverse=(sortorder=='down'))

        records = records[start:start+size]
        for record in records:
            for field, field_title in fields[1:]:
                if isinstance(record[field], tuple):
                    if record[field][1] is True:
                        record[field] = '%s [...]' % record[field][0]
                    else:
                        record[field] = record[field][0]

        namespace['table'] = widgets.table(fields, records, [sortby], sortorder,
                                           actions)

        handler = self.get_handler('/ui/table/view.xml')
        return stl(handler, namespace)



    del_record_action__access__ = 'is_allowed_to_edit'
    def del_record_action(self, context):
        ids = context.get_form_values('ids', type=Integer)
        for id in ids:
            self.del_record(id)

        message = u'Record deleted.'
        return context.come_back(message)



    #########################################################################
    # Add
    add_record_form__access__ = 'is_allowed_to_edit'
    add_record_form__label__ = u'Add'
    def add_record_form(self, context):
        namespace = {}

        fields = []
        for name, title in self.get_fields():
            # Enumerates, use a selection box
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is False:
                value = context.get_form_value(name) \
                        or getattr(datatype, 'default', None)
            else:
                value = context.get_form_values(name) \
                        or getattr(datatype, 'default', None)

            field = {}
            field['name'] = name
            field['title'] = title
            field['mandatory'] = getattr(datatype, 'mandatory', False)
            field['multiple'] = getattr(datatype, 'multiple', False)
            field['is_date'] = is_datatype(datatype, Date)
            widget = getattr(datatype, 'widget', get_default_widget(datatype))
            field['widget'] = widget.to_html(datatype, name, value)

            # Append
            fields.append(field)
        namespace['fields'] = fields

        handler = self.get_handler('/ui/table/add_record.xml')
        return stl(handler, namespace)



    add_record_action__access__ = 'is_allowed_to_edit'
    def add_record_action(self, context):
        # check form
        check_fields = []
        for name, kk in self.get_fields():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                datatype = Multiple(type=datatype)
            check_fields.append((name, getattr(datatype, 'mandatory', False),
                                 datatype))

        error = context.check_form_input(check_fields)
        if error is not None:
            return context.come_back(error, keep=context.get_form_keys())

        record = {}
        for name, title in self.get_fields():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                if is_datatype(datatype, Enumerate):
                    value = context.get_form_values(name, type=datatype)
                else: # textarea -> string
                    values = context.get_form_value(name)
                    values = values.splitlines()
                    value = []
                    for index in range(len(values)):
                        tmp = values[index].strip()
                        if tmp:
                            value.append(datatype.decode(tmp))
            else:
                value = context.get_form_value(name, type=datatype)
            record[name] = value
        self.add_record(record)

        message = u'New record added.'
        goto = context.uri.resolve2('../;add_record_form')
        return context.come_back(message, goto=goto)



    #########################################################################
    # Edit
    edit_record_form__access__ = 'is_allowed_to_edit'
    def edit_record_form(self, context):
        # Get the record
        id = context.get_form_value('id', type=Integer)
        record = self.get_record(id)

        # Build the namespace
        namespace = {}
        namespace['id'] = id

        fields = []
        for name, title in self.get_fields():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is False:
                value = context.get_form_value(name) \
                        or self.get_value(record, name)
            else:
                value = context.get_form_values(name) \
                        or self.get_value(record, name)

            if is_datatype(datatype, Enumerate) is False \
                    and getattr(datatype, 'multiple', False) is True:
                if isinstance(value, list) is True:
                    if value and isinstance(value[0], str) is False:
                        # get value from the record
                        for index in (range(len(value))):
                            value[index] = datatype.encode(value[index])
                    value = '\n'.join(value)
                else:
                    value = datatype.encode(value)

            field = {}
            field['title'] = title
            field['mandatory'] = getattr(datatype, 'mandatory', False)
            field['multiple'] = getattr(datatype, 'multiple', False)
            field['is_date'] = is_datatype(datatype, Date)
            widget = getattr(datatype, 'widget', get_default_widget(datatype))
            field['widget'] = widget.to_html(datatype, name, value)
            # Append
            fields.append(field)
        namespace['fields'] = fields
        handler = self.get_handler('/ui/table/edit_record.xml')
        return stl(handler, namespace)


    edit_record__access__ = 'is_allowed_to_edit'
    def edit_record(self, context):
        # check form
        check_fields = []
        for name, kk in self.get_fields():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                datatype = Multiple(type=datatype)
            check_fields.append((name, getattr(datatype, 'mandatory', False),
                                 datatype))

        error = context.check_form_input(check_fields)
        if error is not None:
            return context.come_back(error, keep=context.get_form_keys())

        # Get the record
        id = context.get_form_value('id', type=Integer)
        record = {}
        for name, title in self.get_fields():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                if is_datatype(datatype, Enumerate):
                    value = context.get_form_values(name)
                else: # textarea -> string
                    values = context.get_form_value(name)
                    values = values.splitlines()
                    value = []
                    for index in range(len(values)):
                        tmp = values[index].strip()
                        if tmp:
                            value.append(datatype.decode(tmp))
            else:
                value = context.get_form_value(name, type=datatype)
            record[name] = value

        self.update_record(id, **record)
        self.set_changed()
        goto = context.uri.resolve2('../;edit_record_form')
        return context.come_back(MSG_CHANGES_SAVED, goto=goto, keep=['id'])



register_object_class(Table)
