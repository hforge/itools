# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from response import Response


class BasicAuth(object):

    def get_credentials(self, request):
        authorization = request.get_header('authorization')
        if authorization is None:
            return None

        auth_scheme, credentials = authorization
        if auth_scheme != 'basic':
            return None

        return credentials


    def challenge(self, realm):
        response = Response()
        response.set_status(401)
        response.set_body('401 Unauthorized')
        challenge = 'Basic realm="%s"' % realm
        response.set_header('WWW-Authenticate', challenge)
        return response



class Realm(object):

    realm = 'default'
    auth = BasicAuth() # TODO Support multiple auth schemes in one realm


    def authenticate(self, request):
        credentials = self.auth.get_credentials(request)
        return self._authenticate(credentials)


    def challenge(self, request):
        return self.auth.challenge(self.realm)


    # To override (open by default)
    def _authenticate(self, credentials):
        return True

