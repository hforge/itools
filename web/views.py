# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Henry Obein <henry@itaapy.com>
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
from itools.datatypes import Enumerate
from itools.stl import stl
from context import FormError
from messages import MSG_MISSING_OR_INVALID



def process_form(get_value, schema):
    values = {}
    invalid = []
    missing = []
    for name in schema:
        datatype = schema[name]
        try:
            value = get_value(name, type=datatype)
        except FormError, error:
            value = get_value(name)
            missing.extend(error.missing)
            invalid.extend(error.invalid)
        values[name] = value
    if missing or invalid:
        raise FormError(missing, invalid)
    return values



class BaseView(object):

    # Access Control
    access = False

    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])


    #######################################################################
    # Query
    query_schema = {}


    def get_query_schema(self):
        return self.query_schema


    def get_query(self, context):
        get_value = context.get_query_value
        schema = self.get_query_schema()
        return process_form(get_value, schema)


    def on_query_error(self, resource, context):
        return 'The query could not be processed.'


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


    #######################################################################
    # View's metadata
    title = None

    def get_title(self, context):
        return self.title



class BaseForm(BaseView):

    schema = {}


    def get_schema(self, resource, context):
        # Check for specific schema
        action = getattr(context, 'form_action', None)
        if action is not None:
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
        get_value = context.get_form_value
        schema = self.get_schema(resource, context)
        return process_form(get_value, schema)


    def get_value(self, resource, context, name, datatype):
        return datatype.default


    def build_namespace(self, resource, context):
        """This utility method builds a namespace suitable to use to produce
        an HTML form. Its input data is a dictionnary that defines the form
        variables to consider:

          {'toto': Unicode(mandatory=True, multiple=False, default=u'toto'),
           'tata': Unicode(mandatory=True, multiple=False, default=u'tata')}

        Every element specifies the datatype of the field.
        The output is like:

            {<field name>: {'value': <field value>, 'class': <CSS class>}
             ...}
        """
        # Figure out whether the form has been submit or not (FIXME This
        # heuristic is not reliable)
        schema = self.get_schema(resource, context)
        submit = (context.request.method == 'POST')

        # Build the namespace
        namespace = {}
        for name in schema:
            datatype = schema[name]
            cls = []
            if getattr(datatype, 'mandatory', False):
                cls.append('field_is_required')
            readonly = getattr(datatype, 'readonly', False)
            if submit and not readonly:
                try:
                    value = context.get_form_value(name, type=datatype)
                except FormError:
                    value = context.get_form_value(name)
                    cls.append('field_is_missing')
            else:
                value = self.get_value(resource, context, name, datatype)
            if isinstance(datatype, Enumerate):
                value = datatype.get_namespace(value)
            else:
                value = datatype.encode(value)
            cls = ' '.join(cls) or None
            namespace[name] = {'name': name, 'value': value, 'class': cls}
        return namespace


    def _get_action(self, resource, context):
        """ default function to retrieve the name of the action from a form
        """
        for name in context.get_form_keys():
            if name.startswith(';'):
                context.form_action = 'action_%s' % name[1:]
                break
        else:
            context.form_action = 'action'


    def get_action_method(self, resource, context):
        return getattr(self, context.form_action, None)


    def on_form_error(self, resource, context):
        context.message = MSG_MISSING_OR_INVALID
        return self.GET


    def POST(self, resource, context):
        # (1) Find out which button has been pressed, if more than one
        self._get_action(resource, context)

        # (2) Automatically validate and get the form input (from the schema).
        try:
            form = self._get_form(resource, context)
        except FormError, error:
            context.form_error = error
            return self.on_form_error(resource, context)

        # (3) Action
        method = self.get_action_method(resource, context)
        if method is None:
            msg = "the '%s' method is not defined"
            raise NotImplementedError, msg % context.form_action
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
            msg = "%s is missing the 'template' variable"
            raise NotImplementedError, msg % repr(self.__class__)

        # Get the namespace
        namespace = self.get_namespace(resource, context)

        # Ok
        template = resource.get_resource(self.template)
        return stl(template, namespace)



class STLForm(STLView, BaseForm):
    pass
