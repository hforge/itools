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

# Import from the Standard Library
from mimetypes import add_type

# Import from isetup
from commands import DEFAULT_REPOSITORY, iregister, iupload
from distribution import Dist, ArchiveNotSupported
from handlers import SetupConf
from metadata import get_package_version, SetupFile, RFC822File, PKGINFOFile
from packages import get_installed_info, packages_infos
from packages_db import PACKAGES_DB
from repository import parse_package_name, download, EXTENSIONS


__all__ = [
    'SetupConf',
    'DEFAULT_REPOSITORY',
    'iregister',
    'iupload',
    # Metadata functions
    'parse_pkginfo',
    'get_package_version',
    'SetupFile',
    'RFC822File',
    'PKGINFOFile',
    # Packages infos functions
    'get_installed_info',
    'packages_infos',
    # Repositories functions and classses
    'parse_package_name',
    'download',
    # Distribution class
    'Dist',
    # Exceptions
    'ArchiveNotSupported',
    # List of supported extensions
    'EXTENSIONS',
    # Dict of known packages
    'PACKAGES_DB'
    ]

add_type('text/x-egg-info', '.egg-info')
