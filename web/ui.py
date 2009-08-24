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
from itools.http import StaticMount, get_context
from itools.i18n import has_language
from itools.uri import Path



class UI(StaticMount):

    def __init__(self, prefix, path):
        StaticMount.__init__(self, prefix, path)
        self.registry = {}


    def register(self, name, path):
        self.registry[name] = path


    def get_local_path(self, path):
        if path and path[0] in self.registry:
            root = self.registry[path[0]]
            path = path[1:]
        else:
            root = self.path
        return '%s/%s' % (root, path)


    def get_template(self, path):
        if type(path) is str:
            path = Path(path)

        path = self.get_local_path(path)

        # Case 1. Exact hit
        database = self.database
        try:
            return database.get_handler(path)
        except LookupError:
            pass

        # Try language negotiation
        # Find out the languages available
        path = Path(path)
        parent = str(path[:-1])
        prefix = '%s.' % path[-1]
        n = len(prefix)
        languages = []
        for name in database.get_handler_names(parent):
            if name[:n] == prefix:
                language = name[n:]
                if has_language(language):
                    languages.append(language)

        # Miss
        if not languages:
            raise LookupError, 'template "%s" not found' % path

        # Get the best variant
        context = get_context()
        if context is None:
            language = None
        else:
            accept = context.accept_language
            language = accept.select_language(languages)

        # By default use whatever variant
        # XXX We need a way to define the default
        if language is None:
            language = languages[0]

        # Hit
        return database.get_handler('%s.%s' % (path, language))

