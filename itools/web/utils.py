# Copyright (C) 2009-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
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

# Import from standard library
from datetime import datetime, date, time
from decimal import Decimal
from json import JSONEncoder
import types

# Import from itools
from itools.gettext import MSG
from itools.html import stream_to_str_as_html, XHTMLFile
from itools.uri import Reference
from itools.xml import XMLParser


reason_phrases = {
    # Informational (HTTP 1.1)
    100: 'Continue',
    101: 'Switching Protocols',
    # Success (HTTP 1.0)
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    204: 'No Content',
    # Success (HTTP 1.1)
    203: 'Non-Authoritative Information',
    205: 'Reset Content',
    206: 'Partial Content',
    # Redirection (HTTP 1.0)
    301: 'Moved Permanently',
    302: 'Found',
    304: 'Not Modified',
    # Redirection (HTTP 1.1)
    300: 'Multiple Choices',
    303: 'See Other',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    # Client error (HTTP 1.0)
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    # Client error (HTTP 1.1)
    402: 'Payment Required',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    # Client error (WebDAV),
    423: 'Locked',
    # Server error (HTTP 1.0)
    500: 'Internal error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    # Server error (HTTP 1.1)
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    }


def fix_json(obj):
    """Utility function, given a json object as returned by json.loads
    transform the unicode strings to strings.

    TODO Use a custom JSONDecoder instead.
    """
    obj_type = type(obj)
    if obj_type is str:
        return obj.encode('utf-8')
    if obj_type is list:
        return [ fix_json(x) for x in obj ]
    if obj_type is dict:
        aux = {}
        for x, y in obj.items():
            aux[fix_json(x)] = fix_json(y)
        return aux
    return obj



class NewJSONEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, date):
            return o.isoformat()
        elif isinstance(o, time):
            return o.isoformat()
        elif isinstance(o, bytes):
            return o.decode()
        elif isinstance(o, MSG):
            return o.gettext()
        elif isinstance(o, XMLParser):
            return stream_to_str_as_html(o)
        elif isinstance(o, XHTMLFile):
            return stream_to_str_as_html(o.events)
        elif isinstance(o, types.GeneratorType):
            return list(o)
        elif isinstance(o, set):
            return list(o)
        elif isinstance(o, Reference):
            return str(o)
        return JSONEncoder.default(self, o)
