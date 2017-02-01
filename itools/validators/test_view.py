# -*- coding: UTF-8 -*-
# Copyright (C) 2016 Sylvain Taverne <sylvain@agicia.com>
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
from itools.gettext import MSG
from itools.validators import validator

# Import from ikaaro
from ikaaro.autoedit import AutoEdit
from ikaaro.fields import Char_Field, Integer_Field, Email_Field, File_Field


class TestValidators(AutoEdit):

    access = True
    title = MSG(u"Test validators")

    fields = ['field_1', 'field_2', 'field_3', 'field_4', 'field_5', 'field_6',
              'field_7', 'field_8', 'field_9', 'field_10', 'field_11', 'field_12',
              'field_13', 'field_14', 'field_15']

    field_1 = Integer_Field(
        title=MSG(u'5+5 equals to ?'),
        validators=[validator('equals-to', base_value=10)],
        error_messages={'not_equals': MSG(u'Give me a 10 ;)')}
        )
    field_2 = Char_Field(
        title=MSG(u'Hexadecimal color'),
        validators=[validator('hexadecimal')])
    field_3 = Integer_Field(
        title=MSG(u'Give a positive number'),
        validators=[validator('integer-positive')])
    field_4 = Integer_Field(
        title=MSG(u'Give a strict positive number'),
        validators=[validator('integer-positive-not-null')])
    field_5 = Integer_Field(
        title=MSG(u'Give a number (max value 10)'),
        validators=[validator('max-value', max_value=10)])
    field_6 = Integer_Field(
        title=MSG(u'Give a number (min value 10)'),
        validators=[validator('min-value', min_value=10)])
    field_7 = Integer_Field(
        title=MSG(u'Give a number (>=10 and <=20)'),
        validators=[validator('min-max-value', min_value=10, max_value=20)])
    field_8 = Char_Field(
        title=MSG(u'Give text (min length: 3 characters)'),
        validators=[validator('min-length', min_length=3)])
    field_9 = Char_Field(
        title=MSG(u'Give text (max length: 5 characters)'),
        validators=[validator('max-length', max_length=5)])
    field_10 = Email_Field(
        title=MSG(u'Give an email (unique in DB)'),
        validators=[validator('unique', field_name='email')],
        error_messages={'invalid': MSG(u'Give be an email address !!!'),
                        'unique': MSG(u'This address is already used')})
    field_11 = File_Field(
        title=MSG(u'File extension (png)'),
        validators=[validator('file-extension', allowed_extensions=['png'])])
    field_12 = File_Field(
        title=MSG(u'File mimetypes (image/png)'),
        validators=[validator('file-mimetypes', allowed_mimetypes=['image/png'])])
    field_13 = File_Field(
        title=MSG(u'Image max pixels'),
        validators=[validator('image-pixels', max_pixels=10*10)])
    field_14 = Char_Field(
        title=MSG(u'Strong password'),
        validators=[validator('strong-password')])
    field_15 = Integer_Field(
        title=MSG(u'Number >=5 and equals to 10'),
        validators=[
          validator('min-value', min_value=5),
          validator('equals-to', base_value=10),
        ])


    def _get_datatype(self, resource, context, name):
          field = self.get_field(resource, name)
          return field(resource=resource)

    def action(self, resource, context, form):
        print form
