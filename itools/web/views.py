# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
# Copyright (C) 2008 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2008, 2011 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2008-2009 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2011 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2012 Sylvain Taverne <taverne.sylvain@gmail.com>
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
from itools.core import freeze, prototype
from itools.database import get_field_and_datatype
from itools.datatypes import Enumerate, String
from itools.gettext import MSG
from itools.handlers import File
from itools.stl import stl
from itools.uri import Reference

# Import from here
from exceptions import FormError, Conflict, MethodNotAllowed
from messages import ERROR



def process_form(get_value, schema, error_msg=None):
    missings = []
    invalids = []
    messages = []
    unknow = []
    values = {}
    for name in schema:
        datatype = schema[name]
        try:
            values[name] = get_value(name, type=datatype)
        except FormError, e:
            if e.missing:
                missings.append(name)
            elif e.invalid:
                invalids.append(name)
            else:
                unknow.append(name)
            messages.extend(e.messages)
    if missings or invalids or unknow:
        error_msg = error_msg or ERROR(u'Form values are invalid')
        raise FormError(
            message=error_msg,
            missing=len(missings)>0,
            invalid=len(invalids)>0,
            messages=messages,
            missings=missings,
            invalids=invalids)
    return values



class ItoolsView(prototype):

    # Access Control
    access = False
    known_methods = []

    def is_access_allowed(self, context):
        return context.is_access_allowed(context.resource, self)


    def get_mtime(self, resource):
        """Caching the view"""
        return None


    def return_json(self, data, context):
        return context.return_json(data)


    def GET(self, resource, context):
        raise MethodNotAllowed


    def PUT(self, resource, context):
        raise MethodNotAllowed


    def HEAD(self, resource, context):
        return self.GET(resource, context)


    def OPTIONS(self, resource, context):
        """Return list of HTTP methods allowed"""
        known_methods = self.known_methods
        context.set_header('Allow', ','.join(known_methods))
        context.entity = None
        context.status = 200


    def DELETE(self, resource, context):
        raise MethodNotAllowed


    def POST(self, resource, context):
        raise MethodNotAllowed


    def PATCH(self, resource, context):
        raise MethodNotAllowed


    def get_canonical_uri(self, context):
        return context.uri


    #######################################################################
    # View's metadata
    title = None

    def get_title(self, context):
        return self.title

    #######################################################################
    # Query
    query_schema = {}


    def get_query_schema(self):
        return self.query_schema


    def get_query(self, context):
        get_value = context.get_query_value
        schema = self.get_query_schema()
        return process_form(get_value, schema)


    #######################################################################
    # Path query
    path_query_schema = {}
    def get_path_query_schema(self):
        return self.path_query_schema


    def get_path_query(self, context):
        get_value = context.get_path_query_value
        schema = self.get_path_query_schema()
        return process_form(get_value, schema)

    #######################################################################
    # POST
    #######################################################################
    schema = {}


    def get_schema(self, resource, context):
        # Check for specific schema
        action = getattr(context, 'form_action', None)
        if action is not None:
            schema = getattr(self, '%s_schema' % action, None)
            if schema is not None:
                return schema
        # Check for method schema
        schema = getattr(self, '%s_schema' % context.method, None)
        if schema is not None:
            return schema
        # Default
        return self.schema


    form_error_message = ERROR(u'There are errors, check below')
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
        return process_form(get_value, schema, self.form_error_message)


    def get_value(self, resource, context, name, datatype):
        return datatype.get_default()



    def on_form_error(self, resource, context):
        content_type, type_parameters = context.get_header('content-type')
        if content_type == 'application/json':
            return self.on_form_error_json(resource, context)
        return self.on_form_error_default(resource, context)


    def on_form_error_default(self, resource, context):
        context.message = context.form_error.get_message()
        # Return to GET view on error
        return self.GET


    def on_form_error_json(self, resource, context):
        error = context.form_error
        error_kw = error.to_dict()
        return self.return_json(error_kw, context)


    def on_query_error(self, resource, context):
        accept = context.get_header('accept')
        if accept == 'application/json':
            return self.on_query_error_json(resource, context)
        return self.on_query_error_default(resource, context)


    def on_query_error_default(self, resource, context):
        message = MSG(u'The query could not be processed.').gettext()
        return message.encode('utf-8')


    def on_query_error_json(self, resource, context):
        error = context.form_error
        error_kw = error.to_dict()
        return self.return_json(error_kw, context)




class BaseView(ItoolsView):

    known_methods = ['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'DELETE']

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
        uri = deepcopy(context.uri)
        query = uri.query

        # Remove the view name if default
        name = uri.path.get_name()
        view_name = name[1:] if name and name[0] == ';' else None
        if view_name:
            resource = context.resource
            if view_name == resource.get_default_view_name():
                uri = uri.resolve2('..')
                view_name = None

        # Be sure the canonical URL either has a view or ends by an slash
        if not view_name and uri.path != '/':
            uri.path.endswith_slash = True

        # Remove noise from query parameters
        canonical_query_parameters = self.canonical_query_parameters
        for parameter in query.keys():
            if parameter not in canonical_query_parameters:
                del query[parameter]
        uri.query = query

        # Ok
        return uri


    def POST(self, resource, context):
        # Get the method
        method = getattr(self, context.form_action, None)
        if method is None:
            msg = "POST method not supported because no '%s' defined"
            raise NotImplementedError(msg % context.form_action)
        # Call method
        goto = method(resource, context, context.form)
        # Return
        if goto is None:
            return self.GET
        return goto


    #######################################################################
    # PUT
    #######################################################################
    access_PUT = False # 'is_allowed_to_put'
    def PUT(self, resource, context):
        # The resource is not locked, the request must have a correct
        #   "If-Unmodified-Since" header.
        if_unmodified_since = context.get_header('If-Unmodified-Since')
        if if_unmodified_since is None:
            raise Conflict
        mtime = resource.get_value('mtime').replace(microsecond=0)
        if mtime > if_unmodified_since:
            raise Conflict
        # Check content-range
        content_range = context.get_header('content-range')
        if content_range:
            raise NotImplemented
        # Check if handler is a File
        handler = resource.get_value('data')
        if not isinstance(handler, File):
            raise ValueError(u"PUT only allowed on files")
        # Save the data
        body = context.get_form_value('body')
        handler.load_state_from_string(body)
        context.database.change_resource(resource)
        # Set the Last-Modified header (if possible)
        mtime = resource.get_value('mtime')
        if mtime is not None:
            mtime = mtime.replace(microsecond=0)
            context.set_header('Last-Modified', mtime)


    access_DELETE = False #'is_allowed_to_remove'
    def DELETE(self, resource, context):
        name = resource.name
        parent = resource.parent
        if parent is None:
            raise MethodNotAllowed
        try:
            parent.del_resource(name)
        except Exception:
            # XXX should be ConsistencyError
            raise Conflict





class STLView(BaseView):

    template = None


    def get_template(self, resource, context):
        # Check there is a template defined
        template = self.template
        if template is None:
            msg = "%s is missing the 'template' variable"
            raise NotImplementedError, msg % repr(self.__class__)

        # Case 1: a path to a file somewhere
        template_type = type(template)
        if template_type is str:
            template = context.get_template(template)
            if template is None:
                msg = 'Template "{0}" was not found'
                raise ValueError(msg.format(self.template))
            return template

        # Case 2: the stream ready to use
        if template_type is list:
            return template

        # Error
        error = 'unexpected type "%s" for the template' % template_type
        raise TypeError, error


    def GET(self, resource, context):
        # Get the namespace
        namespace = self.get_namespace(resource, context)
        if isinstance(namespace, Reference):
            return namespace

        # STL
        template = self.get_template(resource, context)
        if type(template) is list:
            return stl(None, namespace, events=template)

        return stl(template, namespace)


    #######################################################################
    # POST
    #######################################################################
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
        # Figure out whether the form has been submit or not (FIXME This
        # heuristic is not reliable)
        schema = self.get_schema(resource, context)
        submit = (context.method == 'POST')

        # Build the namespace
        namespace = {}
        for name in schema:
            elt = schema[name]
            field, datatype = get_field_and_datatype(elt)
            is_readonly = getattr(datatype, 'readonly', False)
            is_multilingual = getattr(datatype, 'multilingual', False)

            error = None
            if submit and not is_readonly:
                try:
                    value = context.get_form_value(name, type=datatype)
                except FormError, err:
                    error = err.get_message()
                    if issubclass(datatype, Enumerate):
                        value = datatype.get_namespace(None)
                    else:
                        generic_datatype = String(multilingual=is_multilingual)
                        value = context.get_form_value(name,
                                                       type=generic_datatype)
                else:
                    if issubclass(datatype, Enumerate):
                        value = datatype.get_namespace(value)
                    elif is_multilingual:
                        for language in value:
                            value[language] = datatype.encode(value[language])
                    else:
                        value = datatype.encode(value)
            else:
                try:
                    value = self.get_value(resource, context, name, datatype)
                except FormError, err:
                    error = err.get_message()
                    if issubclass(datatype, Enumerate):
                        value = datatype.get_namespace(None)
                    else:
                        value = None
                else:
                    if issubclass(datatype, Enumerate):
                        value = datatype.get_namespace(value)
                    elif is_multilingual:
                        for language in value:
                            value[language] = datatype.encode(value[language])
                    else:
                        value = datatype.encode(value)
            namespace[name] = {'name': name, 'value': value, 'error': error}
        return namespace
