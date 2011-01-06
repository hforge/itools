# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Matthieu France <matthieu@itaapy.com>
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
from string import Formatter
from sys import _getframe

# Import from itools
from itools.core import thingy, is_thingy
from itools.handlers import RODatabase
from itools.i18n import get_language_name
from itools.xml import XMLParser


xhtml_namespaces = {
    None: 'http://www.w3.org/1999/xhtml'}


# XXX This code does not take into account changes in the filesystem once a
# domain has been registered/loaded.


domains = {}

def register_domain(name, locale_path):
    if name not in domains:
        domains[name] = Domain(locale_path)


def get_domain(name):
    return domains[name]



database = RODatabase()

class Domain(dict):

    def __init__(self, uri):
        folder = database.get_handler(uri)
        for key in folder.get_handler_names():
            if key[-3:] == '.mo':
                language = key[:-3]
                self[language] = folder.get_handler(key)


    def gettext(self, message, language):
        if language not in self:
            return message
        handler = self[language]
        return handler.gettext(message)


    def get_languages(self):
        return self.keys()



class MSGFormatter(Formatter):

    def get_value(self, key, args, kw):
        if type(key) is int:
            return args[key]

        msg, kw = kw
        if key in kw:
            value = kw[key]
        else:
            value = getattr(msg, key)

        if is_thingy(value, MSG):
            return value.gettext()

        return value


msg_formatter = MSGFormatter()


class MSG(thingy):

    domain = None
    format = 'replace'

    def __init__(self, message=None, **kw):
        if self.domain is None:
            domain = _getframe(2).f_globals.get('__name__')
            self.domain = domain.split('.', 1)[0]

        if message:
            self.message = message


    def _format(self, message, **kw):
        if self.format == 'replace':
            return msg_formatter.vformat(message, [], (self, kw))
        elif self.format == 'none':
            return message
        elif self.format == 'html':
            data = message.encode('utf_8')
            return XMLParser(data, namespaces=xhtml_namespaces)
        elif self.format == 'replace_html':
            message = msg_formatter.vformat(message, [], (self, kw))
            data = message.encode('utf_8')
            return XMLParser(data, namespaces=xhtml_namespaces)

        raise ValueError, 'unexpected format "{0}"'.format(self.format)


    def gettext(self, language=None, **kw):
        message = self.message
        domain = domains.get(self.domain)

        if domain is not None:
            # Find out the language
            if language is None:
                languages = domain.get_languages()
                # The 'select_language' function must be built-in
                language = select_language(languages)

            # Look-up
            if language is not None:
                message = domain.gettext(message, language)

        return self._format(message, **kw)



def get_language_msg(code):
    language = get_language_name(code)
    return MSG(language)
