# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import datetime

# Import from itools
from itools import uri
from itools.resources import base, memory
from Handler import Handler, State



class File(Handler):
    """
    This is the base handler class for any file handler. It is also used
    as the default handler class for any file resource that has not a more
    specific handler.
    """

    class_resource_type = 'file'


    def __init__(self, resource=None, **kw):
        if resource is None:
            # No resource given, then we create a dummy one
            data = self.get_skeleton(**kw)
            resource = memory.File(data)

        self.resource = resource
        self.state = State()
        self.load_state()


    #########################################################################
    # Load / Save
    #########################################################################
    def _load_state(self, resource):
        state = self.state
        state.data = resource.read()


    def _save_state(self, resource):
        resource.truncate()
        resource.write(self.to_str())


    #########################################################################
    # The factory
    #########################################################################
    handler_class_registry = []

    @classmethod
    def register_handler_class(cls, handler_class):
        if 'handler_class_registry' not in cls.__dict__:
            cls.handler_class_registry = []
        cls.handler_class_registry.append(handler_class)


    @classmethod
    def build_handler(cls, resource):
        mimetype = resource.get_mimetype()
        if mimetype is not None:
            registry = cls.__dict__.get('handler_class_registry', [])
            for handler_class in registry:
                if handler_class.is_able_to_handle_mimetype(mimetype):
                    return handler_class.build_handler(resource)
        return cls(resource)


    @classmethod
    def is_able_to_handle_mimetype(cls, mimetype):
        # Check wether this class understands this mimetype
        type, subtype = mimetype.split('/')
        for class_mimetype in cls.class_mimetypes:
            class_type, class_subtype = class_mimetype.split('/')
            if type == class_type:
                if subtype == class_subtype:
                    return True
                if class_subtype == '*':
                    return True
        # Check wether any sub-class is able to handle the mimetype
        for handler_class in cls.__dict__.get('handler_class_registry', []):
            if handler_class.is_able_to_handle_mimetype(mimetype):
                return True
        # Everything failed, we are not able to manage the mimetype
        return False


    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self):
        return ''


    #########################################################################
    # Serialization
    #########################################################################
    def to_str(self):
        return self.state.data


    #########################################################################
    # API
    #########################################################################
    def set_data(self, data):
        self.set_changed()
        self.state.data = data


    def copy_handler(self):
        resource = memory.File(self.to_str())
        return self.__class__(resource)



Handler.register_handler_class(File)
