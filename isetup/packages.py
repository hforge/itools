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
from os import sep
from os.path import join, split
from sys import path

# Import from itools
from itools.vfs import get_ctime
from itools.vfs import get_names, exists, is_file, is_folder
from metadata import get_package_version, parse_setupconf, parse_pkginfo
from packages_db import PACKAGES_DB


def get_setupconf(package):
    setupconf = join(package, "setup.conf")
    if is_file(setupconf):
        return parse_setupconf(package)
    return None


def get_egginfo(egginfo):
    if is_file(egginfo) and egginfo.endswith('.egg-info'):
        attrs = parse_pkginfo(open(egginfo).read())
        attrs['name'] = attrs['Name']
        attrs['version'] = attrs['Version']
        return attrs
    elif is_folder(egginfo) and egginfo.endswith('.egg-info'):
        attrs = parse_pkginfo(open(join(egginfo, 'PKG-INFO')).read())
        attrs['name'] = attrs['Name']
        attrs['version'] = attrs['Version']
        return attrs
    return None


def get_minpackage(dir):
    package = split(dir)[1]
    if exists(join(dir, '__init__.py')) and is_file(join(dir, '__init__.py')):
        return {'name': package, 'version': get_package_version(package)}
    return None


def can_import(package, origin=None):
    if origin and origin == 'E' and package.has_key('module'):
        test_import = [package['module']]
    elif 'Provides' in package:
        test_import = []
        for provided_module in package['Provides']:
            test_import.append(split_provision(provided_module)[1])
    else:
        # We can try the name if the project has not filled Provides
        # field
        test_import = [package['name']]

    try:
        for module in test_import:
            __import__(module)
    except:
        return False
    else:
        return True


def get_installed_info(dir, package_name, check_import=False):
    package = {}

    info = get_setupconf(join(dir, package_name))
    if info:
        if check_import:
            info['is_imported'] = can_import(info)
        return info

    entries = [join(dir, f) for f in get_names(dir) if\
               f.endswith('.egg-info') and package_name.upper() in f.upper()]

    entries.sort(lambda a, b: cmp(get_ctime(a), get_ctime(b)))

    if len(entries) > 0:
        info = get_egginfo(join(dir, entries.pop()))

    if info:
        if check_import:
            info['is_imported'] = can_import(info)
        return info

    info = get_minpackage(join(dir, package_name))
    if info:
        if check_import:
            info['is_imported'] = can_import(info)
    return info

def packages_infos(check_import, module_name=None):
    # find the site-packages absolute path
    sites = set([])
    for dir in path:
        if 'site-packages' in dir:
            dir = dir.split(sep)
            sites.add(sep.join(dir[:dir.index('site-packages')+1]))

    packages = {}
    recorded_packages = []
    egginfos_mask = []
    modules_mask = []

    def add_package(site, package):
        if packages.has_key(site):
            packages[site].append(package)
        else:
            packages[site] = [package]

    for site in sites:
        for mask, module_mask in PACKAGES_DB:
            egg_found = False
            for egg_info in get_names(site):
                if egg_info.split('-')[0] == mask:
                    data = get_egginfo(join(site,egg_info))
                    if module_name and module_name != data['Name']:
                        continue
                    data['module'] = module_mask
                    add_package(site, (data['Name'], data, 'E'))
                    recorded_packages.append(data['Name'])
                    egginfos_mask.append(mask)
                    modules_mask.append(module_mask)
                    egg_found = True
            if egg_found:
                continue

            if module_name and module_name != module_mask:
                continue

            data = get_setupconf(join(site, module_mask))
            if data:
                add_package(site, (module_mask, data, 'S'))
                recorded_packages.append(module_mask)
                modules_mask.append(module_mask)
                continue

            data = get_minpackage(join(site, module_mask))
            if data:
                add_package(site, (module_mask, data, 'M'))
                recorded_packages.append(module_mask)
                modules_mask.append(module_mask)

    setupconf_packages = []
    egginfo_packages = []
    default_package = []
    # XXX todo: understand .egg -maybe by using setuptools-
    #egg_packages = []

    for site in sites:
        for package in get_names(site):
            if package in modules_mask:
                continue

            if (package.endswith('.egg-info')):
                name = package.split('-')[0]
                if name in egginfos_mask:
                    continue
                # Why the first?
                data = get_egginfo(join(site, package))
                if (data['Name'] in recorded_packages or
                   (module_name and data['Name'] != module_name)):
                    continue
                del data['Name']
                del data['Version']
                add_package(site, (data['name'], data, 'E'))
                recorded_packages.append(data['name'])
                continue
            elif module_name and module_name != package:
                continue

            data = get_setupconf(join(site, package))
            if data and data['name'] not in recorded_packages:
                add_package(site, (data['name'], data, 'S'))
                recorded_packages.append(data['name'])
                continue

            data = get_minpackage(join(site, package))
            if data and data['name'] not in recorded_packages:
                add_package(site, (data['name'], data, 'M'))
                recorded_packages.append(data['name'])
                continue


    for site in packages:
        packages[site].sort(cmp=lambda a, b: cmp(a.upper(),b.upper()),
                      key=itemgetter(0))
        if check_import:
            for name, package, origin in packages[site]:
                package['is_imported'] = can_import(package, origin)
        yield (site, packages[site])

