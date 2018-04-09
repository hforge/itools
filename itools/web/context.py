# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006, 2008-2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2007, 2009, 2011 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007-2008, 2010 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2009-2011 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
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

# Import from gevent
from gevent.local import local

# Import from itools
from itools.database.fields import get_field_and_datatype
from itools.datatypes import String
from itools.log import Logger
from itools.validators import ValidationError

# Local imports
from exceptions import FormError


###########################################################################
# Keep the context globally
###########################################################################
g = local()


def set_context(ctx):
    g.context = ctx


def get_context():
    return getattr(g, 'context', None)


#######################################################################
# Internationalization
#######################################################################
def select_language(languages):
    accept = get_context().accept_language
    return accept.select_language(languages)


#######################################################################
# Get from the form or query
#######################################################################
def _get_form_value(form, name, type=String, default=None):
    field, datatype = get_field_and_datatype(type)
    # Figure out the default value
    if default is None:
        default = datatype.get_default()

    # Errors
    required_msg = field.get_error_message('required')
    invalid_msg = field.get_error_message('invalid')

    # Missing
    is_mandatory = getattr(datatype, 'mandatory', False)
    is_missing = form.get(name) is None
    if is_missing:
        # Mandatory: raise an error
        if is_mandatory and is_missing:
            raise FormError(required_msg, missing=True)
        # Optional: return the default value
        return default

    # Multiple values
    if datatype.multiple:
        value = form.get(name)
        if not isinstance(value, list):
            value = [value]
        try:
            values = [ datatype.decode(x) for x in value ]
        except Exception:
            raise FormError(invalid_msg, invalid=True)
        # Check the values are valid
        for value in values:
            if not datatype.is_valid(value):
                raise FormError(invalid_msg, invalid=True)
        return values

    # Single value
    value = form.get(name)
    if isinstance(value, list):
        value = value[0]
    try:
        value = datatype.decode(value)
    except Exception:
        raise FormError(invalid_msg, invalid=True)

    # We consider that if the type deserializes the value to None, then we
    # must use the default.
    if value is None:
        if is_mandatory:
            raise FormError(required_msg, missing=True)
        return default

    # We consider a blank string to be a missing value (FIXME not reliable).
    is_blank = isinstance(value, (str, unicode)) and not value.strip()
    if is_blank:
        if is_mandatory:
            raise FormError(required_msg, missing=True)
    elif not datatype.is_valid(value):
        raise FormError(invalid_msg, invalid=True)
    return value


def check_form_value(field, value):
    if value in field.empty_values:
        return
    errors = []
    context = get_context()
    for validator in field.get_validators():
        validator = validator(title=field.title, context=context)
        try:
            validator.check(value)
        except ValidationError, e:
            errors.extend(e.get_messages(field))
    if errors:
        raise FormError(messages=errors, invalid=True)


def get_form_value(form, name, type=String, default=None):
    field, datatype = get_field_and_datatype(type)
    # Not multilingual
    is_multilingual = getattr(type, 'multilingual', False)
    if is_multilingual is False:
        value = _get_form_value(form, name, type, default)
        check_form_value(field, value)
        return value
    # Multilingual
    values = {}
    for key, value in form.iteritems():
        if key.startswith('%s:' % name):
            x, lang = key.split(':', 1)
            value =_get_form_value(form, key, type, default)
            values[lang] = value
    check_form_value(field, values)
    return values



class WebLogger(Logger):

    def get_body(self):
        context = get_context()
        if context is None:
            return Logger.get_body(self)

        # The URI and user
        if context.user:
            lines = ['%s (user: %s)\n\n' % (context.uri, context.user.name)]
        else:
            lines = ['%s\n\n' % context.uri]

        # Request header
        lines.append(context.get_request_line() + '\n')
        headers = context.get_headers()
        for key, value in headers:
            lines.append('%s: %s\n' % (key, value))
        lines.append('\n')

        # Ok
        body = Logger.get_body(self)
        lines.extend(body)
        return lines
