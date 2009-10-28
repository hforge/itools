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

# Import from the Standard Library
from copy import deepcopy

# Import from itools
from itools.core import freeze, thingy_type
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.stl import stl
from itools.uri import decode_query, get_reference, Reference
from exceptions import FormError
from messages import ERROR
from views_fields import ViewField


class view_metaclass(type):

    def __new__(mcs, name, bases, dict):
        # Add the 'field_names' attribute, if not explicitly defined
        if 'field_names' not in dict:
            field_names = set()

            # Inherit from the base classes
            for base in bases:
                base_fields = getattr(base, 'field_names', None)
                if base_fields:
                    field_names.update(base_fields)

            # Add this class fields
            for name, value in dict.iteritems():
                if type(value) is thingy_type and issubclass(value, ViewField):
                    field_names.add(name)

            # Ok
            dict['field_names'] = list(field_names)

        # Add the name to fields that miss them
        for name in dict['field_names']:
            field = dict.get(name)
            if field and field.name is None:
                field.name = name

        # Make and return the class
        return type.__new__(mcs, name, bases, dict)



class BaseView(object):

    __metaclass__ = view_metaclass


    # Access Control
    access = False

    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])


    #######################################################################
    # Schema
    #######################################################################
    def get_field_names(self, resource, context):
        return self.field_names


    def get_field(self, name, resource, context):
        return getattr(self, name)


    def get_fields(self, resource, context):
        for name in self.get_field_names(resource, context):
            field = self.get_field(name, resource, context)
            if field is None:
                continue
            yield field


    def cook(self, resource, context, method):
        form = context.form
        query = context.query
        input = context.input

        error = False
        for field in self.get_fields(resource, context):
            field = field(resource=resource, context=context)
            if field.source == 'query':
                field.cook(query)
            elif method == 'post':
                field.cook(form)
                if field.error:
                    error = True
            else:
                field.cook(query, required=False)
            input[field.name] = field
        if error:
            raise FormError


    #######################################################################
    # Caching
    def get_mtime(self, resource):
        return None


    #######################################################################
    # Request methods
    def http_get(self, resource, context):
        raise NotImplementedError


    def http_post(self, resource, context):
        raise NotImplementedError


    #######################################################################
    # View's metadata
    view_title = None

    def get_view_title(self, context):
        return self.view_title


    #######################################################################
    # Canonical URI for search engines
    # "language" is by default because too widespreaded
    canonical_query_parameters = freeze(['language'])


    def get_canonical_uri(self, context):
        """Return the same URI stripped from redundant view name, if already
        the default, and query parameters not affecting the resource
        representation.
        Search engines will keep this sole URI when crawling different
        combinations of this view.
        """
        uri = get_reference(context.uri)
        query = uri.query
        # Remove the view name if default
        view_name = context.view_name
        if view_name:
            resource = context.resource
            if view_name == resource.get_default_view_name():
                uri = uri.resolve2('..')
        # Remove noise from query parameters
        canonical_query_parameters = self.canonical_query_parameters
        for parameter in query.keys():
            if parameter not in canonical_query_parameters:
                del query[parameter]
        uri.query = query
        return uri



class BaseForm(BaseView):

    def get_field_names(self, resource, context):
        # Check for specific fields
        action = getattr(context, 'form_action', None)
        if action is not None:
            fields = getattr(self, '%s_fields' % action, None)
            if fields is not None:
                return fields

        # Default
        return self.field_names


    def get_value(self, resource, context, name, field):
        return field.datatype.get_default()


    def _get_action(self, resource, context):
        """Default function to retrieve the name of the action from a form
        """
        for name in context.form:
            if name.startswith(';'):
                # Browsers send the mouse coordinates with image submits
                if name.endswith(('.x', '.y')):
                    name = name[:-2]
                action = 'action_%s' % name[1:]
                # Save the query of the action into context.form_query
                if '?' in action:
                    action, query = action.split('?')
                    # Deserialize query using action specific schema
                    schema = getattr(self, '%s_query_schema' % action, None)
                    context.form_query = decode_query(query, schema)
                context.form_action = action
                break
        else:
            context.form_action = 'action'


    def get_action_method(self, resource, context):
        return getattr(self, context.form_action, None)


    def http_post(self, resource, context):
        # Find out which button has been pressed, if more than one
        self._get_action(resource, context)

        # Action
        method = self.get_action_method(resource, context)
        if method is None:
            msg = "the '%s' method is not defined"
            raise NotImplementedError, msg % context.form_action
        return method(resource, context)



class STLView(BaseView):

    template = None


    def get_namespace(self, resource, context, query=None):
        return {}


    def get_template(self, resource, context):
        # Check there is a template defined
        if self.template is None:
            msg = "%s is missing the 'template' variable"
            raise NotImplementedError, msg % repr(self.__class__)
        return context.get_template(self.template)


    def http_get(self, resource, context):
        # Get the namespace
        namespace = self.get_namespace(resource, context)
        if isinstance(namespace, Reference):
            return namespace

        # STL
        template = self.get_template(resource, context)
        body = stl(template, namespace)
        context.ok_wrap('text/html', body)



class STLForm(STLView, BaseForm):

    def get_namespace(self, resource, context, query=None):
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
        fields = self.get_field_names(resource, context)

        # Build the namespace
        namespace = {}
        for name in fields:
            field = context.input[name]
            datatype = field.datatype

            if not field.readonly and name in context.input:
                value = field.value
                if value is None:
                    pass
                elif issubclass(datatype, Enumerate):
                    value = datatype.get_namespace(value)
                elif datatype.multiple:
                    # XXX Done for table multilingual fields (fragile)
                    value = value[0]
                else:
                    value = datatype.encode(value)
            else:
                value = self.get_value(resource, context, name, field)
                if issubclass(datatype, Enumerate):
                    value = datatype.get_namespace(value)
                else:
                    value = datatype.encode(value)
            namespace[name] = {
                'name': name, 'value': value, 'error': field.error}
        return namespace

