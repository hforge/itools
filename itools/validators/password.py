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

# Import from standard library
from string import ascii_letters, digits

# Import from itools
from itools.gettext import MSG

# Import from here
from base import BaseValidator


class StrongPasswordValidator(BaseValidator):
    """
     at least 5 characters
     at least one character (a,b,c...)
     at least one special character ( *?./+#!,;:=)
     at least a number (1, 2, 3, ...)"
    """

    validator_id = 'strong-password'
    min_length = 5

    errors = {
        'too_short': MSG(u"This password is too short. It must contain at least {min_length} characters."),
        'need_character': MSG(u"This password should contains at least one character."),
        'need_number': MSG(u"This password should contains at least one number."),
        'need_special_character': MSG(u"This password should contains at least one special character."),
      }

    def check(self, value):
        errors = []
        if len(value) < self.min_length:
            errors.append('too_short')
        has_letter = has_digit = has_special = False
        for c in value:
            if c in ascii_letters:
                has_letter = True
            elif c in digits:
                has_digit = True
            else:
                has_special = True
        if not has_letter:
            errors.append('need_character')
        if not has_digit:
            errors.append('need_number')
        if not has_special:
            errors.append('need_special_character')
        if errors:
            kw = {'min_length': self.min_length}
            self.raise_errors(errors, kw)
