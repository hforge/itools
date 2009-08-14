# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007-2008 Sylvain Taverne <sylvain@itaapy.com>
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
from datetime import datetime
from thread import get_ident, allocate_lock
from time import strptime

# Import from itools
from itools.core import freeze
from itools.datatypes import String
from itools.gettext import MSG
from itools.http import HTTPContext
from itools.i18n import AcceptLanguageType
from itools.uri import get_reference
from messages import ERROR



class FormError(StandardError):
    """Raised when a form is invalid (missing or invalid fields).
    """

    def __init__(self, message=None, missing=freeze([]), invalid=freeze([])):
        self.msg = message
        self.missing = missing
        self.invalid = invalid


    def get_message(self):
        # Custom message
        if self.msg is not None:
            if isinstance(self.msg, MSG):
                return self.msg
            return ERROR(self.msg)
        # Default message
        missing = len(self.missing)
        invalid = len(self.invalid)
        if missing and invalid:
            msg = u"There are {miss} field(s) missing and {inv} invalid."
        elif missing:
            msg = u"There are {miss} field(s) missing."
        elif invalid:
            msg = u"There are {inv} field(s) invalid."
        else:
            # We should never be here
            msg = u"Everything looks fine (strange)."

        # Ok
        return ERROR(msg, miss=missing, inv=invalid)


    def __str__(self):
        return self.get_message().gettext()



class Context(HTTPContext):

    user = None
    resource = None
    status = None


    def __init__(self, soup_message, path):
        HTTPContext.__init__(self, soup_message, path)

        # accept_language
        accept_language = self.get_header('Accept-Language') or ''
        self.accept_language = AcceptLanguageType.decode(accept_language)


    def get_link(self, resource):
        """Return a link to the given resource, from the given context.
        """
        # FIXME This method should give an error if the given resource is
        # not within the site root.
        site_root = self.site_root
        return '/%s' % site_root.get_pathto(resource)


    #######################################################################
    # API / Redirect
    #######################################################################
    def come_back(self, message, goto=None, keep=freeze([]), **kw):
        """This is a handy method that builds a resource URI from some
        parameters.  It exists to make short some common patterns.
        """
        # By default we come back to the referrer
        if goto is None:
            goto = self.get_referrer()
            # Replace goto if no referrer
            if goto is None:
                uri = str(self.uri)
                if '/;' in uri:
                    goto = uri.split('/;')[0]

        if type(goto) is str:
            goto = get_reference(goto)

        # Preserve some form values
        form = {}
        for key, value in self.request.get_form().items():
            # Be robust
            if not key:
                continue
            # Omit methods
            if key[0] == ';':
                continue
            # Omit files
            if isinstance(value, tuple) and len(value) == 3:
                continue
            # Keep form field
            if (keep is True) or (key in keep):
                form[key] = value
        if form:
            goto = goto.replace(**form)
        # Translate the source message
        if message:
            text = message.gettext(**kw)
            if isinstance(message, ERROR):
                return goto.replace(error=text)
            else:
                return goto.replace(info=text)
        return goto


    #######################################################################
    # API / Forms
    #######################################################################
    def get_query_value(self, name, type=String, default=None):
        """Returns the value for the given name from the query.  Useful for
        POST requests.
        """
        form = self.uri.query
        return get_form_value(form, name, type, default)


    def get_form_value(self, name, type=String, default=None):
        form = self.request.get_form()
        return get_form_value(form, name, type, default)


    def get_form_keys(self):
        return self.request.get_form().keys()


    # FIXME Obsolete since 0.20.4, to be removed by the next major release
    def get_form_values(self, name, default=freeze([]), type=None):
        request = self.request
        if request.has_parameter(name):
            value = request.get_parameter(name)
            if not isinstance(value, list):
                value = [value]

            if type is None:
                return value
            return [ type.decode(x) for x in value ]

        return default


    def has_form_value(self, name):
        return self.request.has_parameter(name)


    #######################################################################
    # API / Utilities
    #######################################################################
    def agent_is_a_robot(self):
        footprints = [
            'Ask Jeeves/Teoma', 'Bot/', 'crawler', 'Crawler',
            'freshmeat.net URI validator', 'Gigabot', 'Google',
            'LinkChecker', 'msnbot', 'Python-urllib', 'Yahoo', 'Wget',
            'Zope External Editor']

        user_agent = self.get_header('User-Agent')
        for footprint in footprints:
            if footprint in user_agent:
                return True
        return False


#######################################################################
# Get from the form or query
#######################################################################
def get_form_value(form, name, type=String, default=None):
    # Figure out the default value
    if default is None:
        default = type.get_default()

    # Missing
    is_mandatory = getattr(type, 'mandatory', False)
    is_missing = form.get(name) is None
    if is_missing:
        # Mandatory: raise an error
        if is_mandatory and is_missing:
            raise FormError(missing=[name])
        # Optional: return the default value
        return default

    # Multiple values
    if type.multiple:
        value = form.get(name)
        if not isinstance(value, list):
            value = [value]
        try:
            values = [ type.decode(x) for x in value ]
        except:
            raise FormError(invalid=[name])
        # Check the values are valid
        for value in values:
            if not type.is_valid(value):
                raise FormError(invalid=[name])
        return values

    # Single value
    value = form.get(name)
    if isinstance(value, list):
        value = value[0]
    try:
        value = type.decode(value)
    except:
        raise FormError(invalid=[name])

    # We consider that if the type deserializes the value to None, then we
    # must use the default.
    if value is None:
        if is_mandatory:
            raise FormError(missing=[name])
        return default

    # We consider a blank string to be a missing value (FIXME not reliable).
    is_blank = isinstance(value, (str, unicode)) and not value.strip()
    if is_blank:
        if is_mandatory:
            raise FormError(missing=[name])
    elif not type.is_valid(value):
        raise FormError(invalid=[name])
    return value
