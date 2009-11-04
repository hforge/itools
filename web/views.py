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
from itools.core import freeze, thingy, thingy_type
from itools.stl import stl
from itools.uri import decode_query, get_reference
from exceptions import FormError
from views_fields import ViewField


class view_metaclass(thingy_type):

    def __new__(mcs, class_name, bases, dict):
        # Add the 'field_names' attribute, if not explicitly defined
        if 'field_names' not in dict:
            field_names = []

            # Inherit from the base classes
            for base in bases:
                for name in getattr(base, 'field_names', []):
                    if name in dict and dict[name] is None:
                        continue
                    if name not in field_names:
                        field_names.append(name)

            # Add this class fields
            for name, value in dict.iteritems():
                if type(value) is thingy_type and issubclass(value, ViewField):
                    if name not in field_names:
                        field_names.append(name)

            # Ok
            dict['field_names'] = field_names

        # Add the name to fields that miss them
        for name in dict['field_names']:
            field = dict.get(name)
            if type(field) is thingy_type and field.name is None:
                field.name = name

        # Make and return the class
        return thingy_type.__new__(mcs, class_name, bases, dict)



class BaseView(thingy):

    __metaclass__ = view_metaclass


    # Access Control
    access = False

    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])


    #######################################################################
    # Schema
    #######################################################################
    def get_field_names(self):
        return self.field_names


    def get_field(self, name):
        return getattr(self, name)


    def get_fields(self):
        for name in self.get_field_names():
            field = getattr(self, name, None)
            if field is None:
                field = self.get_field(name)
            yield field


    def cook(self, method):
        context = self.context
        form = context.form
        query = context.query

        error = False
        for field in self.get_fields():
            # Bind the field to the view
            field = field(view=self)
            # Cook the field
            if field.source == 'query':
                field.cook(query)
            elif method == 'post':
                field.cook(form)
                if field.error:
                    error = True
            else:
                field.cook(query, required=False)
            # Assign the bound & cooked field to the view
            setattr(self, field.name, field)

        if error:
            raise FormError


    #######################################################################
    # Caching
    def get_mtime(self, resource):
        return None


    #######################################################################
    # Request methods
    def http_get(self):
        raise NotImplementedError


    def http_post(self):
        raise NotImplementedError


    #######################################################################
    # View's metadata
    view_title = None


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
            if view_name == resource.default_view_name:
                uri = uri.resolve2('..')
        # Remove noise from query parameters
        canonical_query_parameters = self.canonical_query_parameters
        for parameter in query.keys():
            if parameter not in canonical_query_parameters:
                del query[parameter]
        uri.query = query
        return uri



class BaseForm(BaseView):

    def get_field_names(self):
        # Check for specific fields
        action = getattr(self.context, 'form_action', None)
        if action is not None:
            fields = getattr(self, '%s_fields' % action, None)
            if fields is not None:
                return fields

        # Default
        return self.field_names


    def get_value(self, resource, context, name, field):
        return field.datatype.get_default()


    def _get_action(self):
        """Default function to retrieve the name of the action from a form
        """
        context = self.context
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


    def get_action_method(self):
        return getattr(self, self.context.form_action, None)


    def http_post(self):
        # Find out which button has been pressed, if more than one
        self._get_action()

        # Action
        method = self.get_action_method()
        if method is None:
            msg = "the '%s' method is not defined"
            raise NotImplementedError, msg % self.context.form_action
        return method()



class STLView(BaseView):

    template = None


    def get_template(self):
        # Check there is a template defined
        if self.template is None:
            msg = "%s is missing the 'template' variable"
            raise NotImplementedError, msg % repr(self.__class__)
        return self.context.get_template(self.template)


    def render(self):
        template = self.get_template()
        return stl(template, self)


    def http_get(self):
        context = self.context
        # Get the namespace
        body = self.render()
        context.ok_wrap('text/html', body)



class STLForm(STLView, BaseForm):
    pass

