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


class ValidationError(Exception):

    errors = []

    def __init__(self, msg=None, code=None, msg_params=None):
        errors = []
        if type(msg) is list:
            errors.extend(msg)
        else:
            errors.append((msg, code, msg_params))
        self.errors = errors


    def get_messages(self, field):
        l = []
        for msg, code, msg_params in self.errors:
            field_msg = field.get_error_message(code) if field else None
            msg = field_msg or msg
            l.append(msg.gettext(**msg_params))
        return l


    def get_message(self, field=None, mode='html'):
        messages = self.get_messages(field)
        if mode == 'html':
            msg = '<br/>'.join(messages)
            return MSG(msg, format='html')
        return '\n'.join(messages)


    def __str__(self):
        return self.get_message()
