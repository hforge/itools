# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from distutils.versionpredicate import split_provision
from operator import itemgetter
from os.path import join

# Import from itools
from metadata import get_package_version, parse_setupconf, parse_pkginfo
from itools.vfs import get_names, exists, is_file, is_folder
from itools.vfs import get_ctime


def get_setupconf(dir, package):
    dir = join(dir, package)
    setupconf = join(dir, "setup.conf")
    if is_file(setupconf):
        return parse_setupconf(dir)
    return None


def get_egginfo(dir, file):
    if is_file(join(dir, file)) and file.endswith('.egg-info'):
        attrs = parse_pkginfo(open(join(dir, file)).read())
        attrs['name'] = attrs['Name']
        attrs['version'] = attrs['Version']
        return attrs
    return None


def get_minpackage(dir, package):
    dir = join(dir, package)
    if exists(join(dir, '__init__.py')) and is_file(join(dir, '__init__.py')):
        return {'name': package, 'version': get_package_version(package)}
    return None


def can_import(package):
    if 'Provides' in package:
        try:
            for provided_module in package['Provides'].split(','):
                provided_module = split_provision(provided_module)
                provided_module_name = provided_module[0]
                provided_module_ver = provided_module[1]
                __import__(provided_module_name)
        except:
            return False
        else:
            return True
    else:
        # We can try the name if the project has not filled Provides
        # field
        try:
            __import__(package['name'])
        except:
            return False
        else:
            return True


def get_installed_info(dir, package_name, check_import=False):
    package = {}

    info = get_setupconf(dir, package_name)
    if info:
        if check_import:
            info['is_imported'] = can_import(info)
        return info

    entries = [join(dir, f) for f in get_names(dir) if\
               f.endswith('.egg-info') and package_name.upper() in f.upper()]

    entries.sort(lambda a, b: cmp(get_ctime(a), get_ctime(b)))

    if len(entries) > 0:
        info = get_egginfo(dir, entries.pop())

    if info:
        if check_import:
            info['is_imported'] = can_import(info)
        return info

    info = get_minpackage(dir, package_name)
    if info:
        if check_import:
            info['is_imported'] = can_import(info)
    return info


def list_packages_info(dir, module_name='', check_import=True):
    """For every package in a directory, return its informations and test if
    import is possible.

    Works for::
        * .egg-info
        * package/setup.conf
        * understand if package provides .__version__ or .version
    """
    packages = []
    recorded_packages = []

    setupconf_packages = []
    egginfo_packages = []
    default_package = []
    # XXX todo: understand .egg -maybe by using setuptools-
    #egg_packages = []

    folder_entries = [d for d in get_names(dir) if module_name in d]
    setupconf_packages = [get_setupconf(dir, p) for p in folder_entries]
    egginfo_packages = [get_egginfo(dir, p) for p in folder_entries]
    default_package = [get_minpackage(dir, p) for p in folder_entries]

    for package in setupconf_packages:
        if package != None:
            if check_import:
                package['is_imported'] = can_import(package)
            packages.append((package['name'], package))
            recorded_packages.append(package['name'])

    for package in egginfo_packages:
        if package != None and package['Name'] not in recorded_packages:
            if check_import:
                package['is_imported'] = can_import(package)
            packages.append((package['name'], package))
            recorded_packages.append(package['name'])

    for package in default_package:
        if package != None and package['name'] not in recorded_packages:
            if check_import:
                package['is_imported'] = can_import(package)
            packages.append((package['name'], package))

    packages.sort(cmp=lambda a, b: cmp(a.upper(),b.upper()), key=itemgetter(0))

    return packages

