# Copyright (C) 2005-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 Matthieu France <matthieu@itaapy.com>
# Copyright (C) 2010 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2010-2011 Hervé Cauwelier <herve@oursours.net>
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
from itools.i18n import get_language_name
from itools.i18n.accept import select_language
from itools.fs import lfs
from itools.xml import XMLParser

# Import from here
from .mo import MOFile


xhtml_namespaces = {
    None: 'http://www.w3.org/1999/xhtml'}


# XXX This code does not take into account changes in the filesystem once a
# domain has been registered/loaded.


domains = {}


def register_domain(name, locale_path):
    if name not in domains:
        domains[name] = locale_path


def get_domain(name):
    domain = domains.get(name)
    # Lazy load domain
    if isinstance(domain, str):
        domain = Domain(domain)
        domains[name] = domain

    return domain


class Domain(dict):

    def __init__(self, uri):
        super().__init__()
        for key in lfs.get_names(uri):
            if key[-3:] == '.mo':
                language = key[:-3]
                path = f'{uri}/{key}'
                self[language] = MOFile(path)

    def gettext(self, message, language):
        if language not in self:
            return message
        handler = self[language]
        return handler.gettext(message)

    def get_languages(self):
        return list(self.keys())


class MSGFormatter(Formatter):

    def get_value(self, key, args, kw):
        if type(key) is int:
            return args[key]

        msg, kw = kw
        if key in kw:
            value = kw[key]
        else:
            value = getattr(msg, key)

        if isinstance(value, MSG):
            return value.gettext()

        return value


msg_formatter = MSGFormatter()


class MSG:

    domain = None
    message = None
    format = 'replace'

    def __init__(self, message=None, format=None):
        if self.domain is None:
            domain = _getframe(1).f_globals.get('__name__')
            self.domain = domain.split('.', 1)[0]
        if format:
            self.format = format
        if message:
            self.message = message

    def _format(self, message, **kw):
        if self.format == 'replace':
            return msg_formatter.vformat(message, [], (self, kw))
        elif self.format == 'none':
            return message
        elif self.format == 'html':
            return XMLParser(message, namespaces=xhtml_namespaces)
        elif self.format == 'replace_html':
            message = msg_formatter.vformat(message, [], (self, kw))
            return XMLParser(message, namespaces=xhtml_namespaces)

        raise ValueError(f'unexpected format "{self.format}"')

    def gettext(self, language=None, **kw):
        message = self.message
        domain = get_domain(self.domain)

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
