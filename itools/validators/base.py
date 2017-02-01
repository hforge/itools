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
import re

# Import from itools
from itools.core import prototype, prototype_type
from itools.gettext import MSG

# Import from here
from exceptions import ValidationError
from registry import register_validator


class BaseValidatorMetaclass(prototype_type):

    def __new__(mcs, name, bases, dict):
        cls = prototype_type.__new__(mcs, name, bases, dict)
        if 'validator_id' in dict:
            register_validator(cls)
        return cls


class validator_prototype(prototype):

    __metaclass__ = BaseValidatorMetaclass


class BaseValidator(validator_prototype):

    validator_id = None
    errors = {'invalid': MSG(u'Enter a valid value')}

    def is_valid(self, value):
        try:
            self.check(value)
        except ValidationError:
            return False
        return True


    def check(self, value):
        raise NotImplementedError('Validator is not configured')


    def get_error_msg(self):
        return self.msg


    def raise_default_error(self, kw={}):
        code, msg = self.errors.items()[0]
        raise ValidationError(msg, code, kw)


    def raise_errors(self, errors, kw={}):
        l = []
        for code in errors:
            msg = self.errors[code]
            l.append((msg, code, kw))
        raise ValidationError(l)


    def __call__(self, value):
        return self.check(value)



class EqualsValidator(BaseValidator):

    validator_id = 'equals-to'
    base_value = None
    errors = {'not_equals':  MSG(u'The value should be equals to {base_value}')}

    def check(self, value):
        if value != self.base_value:
            kw = {'base_value': self.base_value}
            self.raise_default_error(kw)



class RegexValidator(BaseValidator):

    regex = None
    inverse_match = False

    def check(self, value):
        value = str(value)
        r = re.compile(self.regex, 0)
        if bool(r.search(value)) != (not self.inverse_match):
            self.raise_default_error()




class HexadecimalValidator(RegexValidator):

    validator_id = 'hexadecimal'
    regex = '^#[A-Fa-f0-9]+$'
    errors = {'invalid': MSG(u'Enter a valid value.')}



class PositiveIntegerValidator(BaseValidator):

    validator_id = 'integer-positive'
    errors = {'integer_positive':  MSG(u'Ensure this value is positive.')}

    def check(self, value):
        if value < 0:
            kw = {'value': value}
            self.raise_default_error(kw)



class PositiveIntegerNotNullValidator(BaseValidator):

    validator_id = 'integer-positive-not-null'
    errors = {'integer_positive_not_null':  MSG(u'Ensure this value is greater than 0.')}

    def check(self, value):
        if value <= 0:
            kw = {'value': value}
            self.raise_default_error(kw)



class MaxValueValidator(BaseValidator):

    validator_id = 'max-value'
    errors = {'max_value':  MSG(u'Ensure this value is less than or equal to {max_value}.')}
    max_value = None

    def check(self, value):
        if value and value > self.max_value:
            kw = {'max_value': self.max_value}
            self.raise_default_error(kw)



class MinValueValidator(BaseValidator):

    validator_id = 'min-value'
    errors = {'min_value':  MSG(u'Ensure this value is greater than or equal to {min_value}.')}
    min_value = None

    def check(self, value):
        if value < self.min_value:
            kw = {'min_value': self.min_value}
            self.raise_default_error(kw)



class MinMaxValueValidator(BaseValidator):

    validator_id = 'min-max-value'
    errors = {'min_max_value': MSG(
        u'Ensure this value is greater than or equal to {min_value} '
        u'and value is less than or equal to {max_value}.')}
    min_value = None
    max_value = None

    def check(self, value):
       if value < self.min_value or value > self.max_value:
            kw = {'max_value': self.max_value,
                  'min_value': self.min_value}
            self.raise_default_error(kw)




class MinLengthValidator(BaseValidator):

    validator_id = 'min-length'
    min_length = 0
    errors = {'min_length': MSG(u'Ensure this value has at least {min_length} characters.')}

    def check(self, value):
        if len(value) < self.min_length:
            kw = {'value': value,
                  'size': len(value),
                  'min_length': self.min_length}
            self.raise_default_error(kw)



class MaxLengthValidator(BaseValidator):

    validator_id = 'max-length'
    max_length = 0
    errors = {'max_length': MSG(u'Ensure this value has at most {max_length} characters.')}

    def check(self, value):
        if len(value) > self.max_length:
            kw = {'value': value,
                  'size': len(value),
                  'max_length': self.max_length}
            self.raise_default_error(kw)
