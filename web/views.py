# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.stl import stl
from context import FormError
from messages import MSG_MISSING_OR_INVALID


class BaseView(object):

    # Access Control
    access = False

    # Query Schema
    query_schema = {}


    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])


    #######################################################################
    # Query
    def get_query(self, context):
        get_value = context.get_query_value
        schema = self.query_schema

        query = {}
        for name in schema:
            datatype = schema[name]
            query[name] = get_value(name, datatype)

        return query


    #######################################################################
    # Caching
    def get_mtime(self, resource):
        return None


    #######################################################################
    # Request methods
    def GET(self, resource, context):
        raise NotImplementedError


    def POST(self, resource, context):
        raise NotImplementedError



class BaseForm(BaseView):

    schema = {}


    def get_form_title(self):
        return self.form_title


    def get_schema(self, resource, context):
        # Check for specific schema
        action = context.form_action
        schema = getattr(self, '%s_schema' % action, None)
        if schema is not None:
            return schema

        # Default
        return self.schema


    def _get_form(self, resource, context):
        """Form checks the request form and collect inputs consider the
        schema.  This method also checks the request form and raise an
        FormError if there is something wrong (a mandatory field is missing,
        or a value is not valid) or None if everything is ok.

        Its input data is a list (fields) that defines the form variables to
          {'toto': Unicode(mandatory=True, multiple=False, default=u'toto'),
           'tata': Unicode(mandatory=True, multiple=False, default=u'tata')}
        """
        schema = self.get_schema(resource, context)

        values = {}
        invalid = []
        missing = []
        for name in schema:
            datatype = schema[name]
            try:
                value = context.get_form_value(name, type=datatype)
            except FormError, error:
                value = context.get_form_value(name)
                missing.extend(error.missing)
                invalid.extend(error.invalid)
            values[name] = value
        if missing or invalid:
            raise FormError(missing, invalid)
        return values


    def POST(self, resource, context):
        # Load the query
        context.query = self.get_query(context)

        # (1) Find out which button has been pressed, if more than one
        for name in context.get_form_keys():
            if name.startswith(';'):
                context.form_action = 'action_%s' % name[1:]
                break
        else:
            context.form_action = 'action'

        # (2) Automatically validate and get the form input (from the schema).
        try:
            form = self._get_form(resource, context)
        except FormError:
            context.message = MSG_MISSING_OR_INVALID
            return self.GET

        # (3) Action
        method = getattr(self, context.form_action, None)
        if method is None:
            raise NotImplementedError
        goto = method(resource, context, form)

        # (4) Return
        if goto is None:
            return self.GET
        return goto



class STLView(BaseView):

    template = None


    def get_namespace(self, resource, context, query=None):
        return {}


    def GET(self, resource, context):
        # Check there is a template defined
        if self.template is None:
            raise NotImplementedError

        # Load the query
        context.query = self.get_query(context)

        # Get the namespace
        namespace = self.get_namespace(resource, context)

        # Ok
        template = resource.get_object(self.template)
        return stl(template, namespace)



class STLForm(STLView, BaseForm):
    pass
