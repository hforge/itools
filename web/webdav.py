# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from server import RequestMethod, register_method



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



class LOCK(RequestMethod):

    @classmethod
    def handle_request(cls, server, context):
        response = context.response

        # (1) The requested resource
        cls.find_resource(server, context)
        resource = context.object

        # (2) Access Control
        ac = resource.get_access_control()
        if not ac.is_allowed_to_lock(context.user, resource):
            # XXX Should it be Unauthorized (401) or Forbidden (403) ?
            response.set_status(401)
            response.set_header('content-length', 0)
            response.set_body(None)
            return response

        # (3) Check whether the resource is already locked
        if resource.is_locked():
            response.set_status(423)
            response.set_header('content-length', 0)
            response.set_body(None)
            return response

        # (4) Lock the resource
        try:
            lock = resource.lock()
        except:
            server.log_error(context)
            server.abort_transaction(context)
            response.set_status(423)
            response.set_header('content-length', 0)
            response.set_body(None)
            return response

        # (5) Commit transaction
        cls.commit_transaction(server, context)

        # (6) Ok
        response.set_status(200)
        response.set_header('Content-Type', 'text/xml; charset="utf-8"')
        response.set_header('Lock-Token', 'opaquelocktoken:%s' % lock)
        entity = lock_body % {'owner': context.user.name, 'locktoken': lock}
        response.set_header('content-length', len(entity))
        response.set_body(entity)
        return response



class UNLOCK(RequestMethod):

    @classmethod
    def handle_request(cls, server, context):
        response = context.response

        # (1) The requested resource
        cls.find_resource(server, context)
        resource = context.object

        # (2) Access Control
        ac = resource.get_access_control()
        if not ac.is_allowed_to_lock(context.user, resource):
            # XXX Should it be Unauthorized (401) or Forbidden (403) ?
            response.set_status(401)
            response.set_header('content-length', 0)
            response.set_body(None)
            return response

        # (3) Check whether the resource is already locked
        if not resource.is_locked():
            # FIXME This probably not the good response
            response.set_status(423)
            response.set_header('content-length', 0)
            response.set_body(None)
            return response

        # (4) Unlock
        # Check wether we have the right key
        key = context.request.get_header('Lock-Token')
        key = key[len('opaquelocktoken:'):]
        lock = resource.get_lock()
        if lock.key != key:
            # FIXME Send some nice response to the client
            raise ValueError, 'can not unlock resource, wrong key'

        resource.unlock()

        # (5) Commit transaction
        cls.commit_transaction(server, context)

        # (6) Ok
        response.set_status(200)
        response.set_header('Content-Type', 'text/xml; charset="utf-8"')
        response.set_header('Lock-Token', 'opaquelocktoken:%s' % lock)
        response.set_body(None)
        return response



###########################################################################
# Register
###########################################################################

register_method('LOCK', LOCK)
register_method('UNLOCK', UNLOCK)
