# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
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
from itools.datatypes import MultiLinesTokens, String, URI, Email, Tokens
from itools.handlers import ConfigFile



class SetupConf(ConfigFile):

    schema = {
        'name': String,
        'title': String,
        'url': URI,
        'author_name': String,
        'author_email': Email,
        'license': String,
        'description': String,
        'classifiers': MultiLinesTokens(default=()),
        'packages': Tokens(default=()),
        'requires': Tokens(default=()),
        'provides': Tokens(default=()),
        'scripts': Tokens(default=()),
        'source_language': String,
        'target_language': String,
        'repository': URI,
        'username': String}


