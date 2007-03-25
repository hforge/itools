# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA



objects_registry = {}

def register_object_class(object, format=None):
    if format is None:
        format = object.class_id
    objects_registry[format] = object


def get_object_class(class_id):
    if class_id in objects_registry:
        return objects_registry[class_id]

    if '/' in class_id:
        class_id = class_id.split('/')[0]
        if class_id in objects_registry:
            return objects_registry[class_id]

    # Default to file
    return objects_registry["application/octet-stream"]


##def build_handler(resource, format=None):
##    from file import File
##    from folder import Folder

##    if format in registry:
##        handler_class = registry[format]
##    else:
##        format = format.split('/')
##        if format[0] in registry:
##            handler_class = registry[format[0]]
##        else:
##            # XXX Show a warning message here
##            if isinstance(resource, base.File):
##                handler_class = registry[File.class_id]
##            elif isinstance(resource, base.Folder):
##                handler_class = registry[Folder.class_id]
##            else:
##                raise ValueError, \
##                      'Unknown resource type "%s"' % repr(resource)
####    # Check wether the resource is a file and the handler class is a
####    # folder, or viceversa.
####    if isinstance(resource, base.File):
####        if not issubclass(handler_class, File):
####            handler_class = File
####    elif isinstance(resource, base.Folder):
####        if not issubclass(handler_class, Folder):
####            handler_class = Folder

##    return handler_class(resource)


