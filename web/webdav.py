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
from itools.http import ClientError, BadRequest, Conflict, NotImplemented
from server import RequestMethod, register_method, find_view_by_method


# This module is meant to provide support for the WebDav protocol.  Though so
# far it only does the minimum required for the "external editor" of ikaaro to
# work.



lock_body = """<?xml version="1.0" encoding="utf-8" ?>
<d:prop xmlns:d="DAV:">
 <d:lockdiscovery>
   <d:activelock>
     <d:locktype><d:write/></d:locktype>
     <d:lockscope><d:exclusive/></d:lockscope>
     <d:depth>0</d:depth>
     <d:owner>%(owner)s</d:owner>
     <d:timeout>Second-720</d:timeout>
     <d:locktoken>
       <d:href>opaquelocktoken:%(locktoken)s</d:href>
     </d:locktoken>
   </d:activelock>
 </d:lockdiscovery>
</d:prop>
"""



class Locked(ClientError):
    code = 423
    title = 'Locked'



class LOCK(RequestMethod):

    method_name = 'LOCK'


    @classmethod
    def find_view(cls, server, context):
        find_view_by_method(server, context)


    @classmethod
    def check_conditions(cls, server, context):
        resource = context.resource
        if resource.is_locked():
            raise Locked


    @classmethod
    def check_transaction(cls, server, context):
        return getattr(context, 'commit', True) and context.status < 400



class UNLOCK(RequestMethod):

    method_name = 'UNLOCK'

    @classmethod
    def find_view(cls, server, context):
        find_view_by_method(server, context)


    @classmethod
    def check_conditions(cls, server, context):
        resource = context.resource
        if not resource.is_locked():
            raise Conflict
        # Check wether we have the right key
        request = context.request
        key = request.get_header('Lock-Token')
        if key is None:
            raise BadRequest
        key = key[len('opaquelocktoken:'):]
        lock = resource.get_lock()
        if lock.key != key:
            # FIXME find the good response
            raise BadRequest


    @classmethod
    def check_transaction(cls, server, context):
        return getattr(context, 'commit', True) and context.status < 400



class PUT(RequestMethod):
    """This is the PUT method as defined in WebDAV.
    Resource must be locked before PUTting.
    """

    method_name = 'PUT'


    @classmethod
    def find_view(cls, server, context):
        find_view_by_method(server, context)


    @classmethod
    def check_conditions(cls, server, context):
        request = context.request
        if request.has_header('content-range'):
            raise NotImplemented

        # In WebDAV the resource must be locked
        resource = context.resource
        if not resource.is_locked():
            raise Conflict

        # TODO check the lock matches the "If:" header


    @classmethod
    def check_transaction(cls, server, context):
        return getattr(context, 'commit', True) and context.status < 400



###########################################################################
# Register
###########################################################################

register_method('LOCK', LOCK)
register_method('UNLOCK', UNLOCK)
register_method('PUT', PUT)
