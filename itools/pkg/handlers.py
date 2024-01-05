# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
# Copyright (C) 2008-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
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

# Import from itools
from itools.datatypes import MultiLinesTokens, String, URI, Email, Tokens
from itools.handlers import ConfigFile


class SetupConf(ConfigFile):

    schema = {
        'name': String,
        'package_name': String,
        'package_root': String(default='.'),
        'title': String,
        'url': String,
        'author_name': String,
        'author_email': Email,
        'license': String,
        'description': String,
        'classifiers': MultiLinesTokens(default=()),
        'packages': Tokens,
        'scripts': Tokens,
        'bin': Tokens,
        'source_language': String,
        'target_languages': Tokens,
        'repository': URI,
        'username': String,
    }
