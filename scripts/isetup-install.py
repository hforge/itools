#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
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

"""Usage:
isetup-install.py [options] package-spec

If the package is installed in package-spec do nothing.
If the package is not installed, then download if available from index-url to
cache-dir, "python setup.py build install" it, check if built with setuptools
or distutils, if it was with setuptools stop here, else check dependencies and
treat them with something like a "install_package" function.
"""

# Import from the Standard Library
import re
from distutils.version import LooseVersion
from distutils.versionpredicate import VersionPredicate
from optparse import OptionParser
from operator import itemgetter
from os import sep
from os.path import join
from sys import path, exit

# Import from itools
from itools import __version__
import itools.http
from itools.isetup import (parse_package_name, download, list_eggs_info,
                           Repository, EXTENSIONS, Dist, ArchiveNotSupported)
from itools.vfs import exists, open, is_folder, get_names, make_folder


# This is what is called Packages/
TMP_DIR = TMP_DIR_DEFAULT = 'Packages'
PYPI_REPO = 'http://pypi.python.org/simple/'
YES = ('y', 'Y', 'yes', 'YES', 'ok', 'Yes', 'yep')

def find_installed_package(package_version):
    # find the site-packages absolute path
    # The behaviour may change, why not look in every sys.path folder?
    sites = set([])
    for dir in path:
        if is_folder(dir):
            sites.add(dir)
        if 'site-packages' in dir:
            dir = dir.split(sep)
            sites.add(sep.join(dir[:dir.index('site-packages')+1]))

    # yield compatible packages
    for site in sites:
        eggs = list_eggs_info(site, package_version.name)
        for egg in eggs:
            try:
                if package_version.satisfied_by(egg['Version']):
                    yield egg
            # if a package installed gives us an bogus version don't crash
            except ValueError:
                pass


class Enumerate(object):
    """Utility Class
    """
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)


prepare_code = Enumerate('NoAvailableCandidate Ok BadArchive BadName '\
                         'AlreadyInstalled NotFound')
install_code = Enumerate('Ok SetupError UnknownError')

unretrievables = []
packages_to_install = []

def prepare(package_spec):
    """Work with a few globals variables, like repositories, ...
    """
    try:
        package_version = VersionPredicate(package_spec)
    except ValueError:
        unretrievables.append((prepare_code.BadName, package_spec))
        return prepare_code.NoAvailableCandidate

    # Repository listing
    repo_candidates = []

    for repo in repositories:
        # If the repository has the package
        if exists(join(repo, package_version.name)):
            repo = Repository(repo)
            # List versions of this package for this repository
            dists = repo.list_distributions(package_version.name)
            for dist in dists:
                if package_version.satisfied_by(dist['version']):
                    repo_candidates.append(dist)

    # Transform string version of each dists to a LooseVersion
    for candidate in repo_candidates:
        candidate['version'] = LooseVersion(candidate['version'])


    # Cache listing
    cache_candidate = []

    if not exists(CACHE_DIR):
        make_folder(CACHE_DIR)

    cache_candidates = []

    cache_dir = open(CACHE_DIR)
    for filename in cache_dir.get_names('.'):
        dist = parse_package_name(filename)
        if dist['name'] == package_version.name and\
           dist['extension'] in EXTENSIONS:
            try:
                dist['version'] = LooseVersion(dist['version'])
                cache_candidates.append(dist)
            except ValueError:
                continue


    ## Installation listing
    #installed_packages = []
    #for dist in find_installed_package(package_version):
    #    if dist['Name'] == package_version.name:
    #        try:
    #            dist['version'] = LooseVersion(dist['Version'])
    #            cache_candidates.append(dist)
    #        except ValueError:
    #            continue
    #        installed_packages.append(dist)

    candidates  = [(dist['version'], 'cache', dist)\
                   for dist in cache_candidates]
    candidates += [(dist['version'], 'repository', dist)\
                   for dist in repo_candidates]
    #candidates += [(dist['version'], 'installed', dist)\
            #for dist in installed_packages]

    candidates.sort(key=itemgetter(0))
    candidates.reverse()

    if len(candidates) == 0:
        return prepare_code.NoAvailableCandidate

    while candidates:
        bestmatch_version, bestmatch_from, bestmatch = candidates.pop()

        if bestmatch_from == 'installed':
            print '%s %s is already the newest version.' % (bestmatch['Name'],
                                                            bestmatch_version)
            return prepare_code.AlreadyInstalled

        elif bestmatch_from == 'cache':
            dist_loc = join(CACHE_DIR, bestmatch['file'])
        elif bestmatch_from == 'repository':
            try:
                dist_loc = download(bestmatch['url'], CACHE_DIR)
            except LookupError:
                if not candidates:
                    unretrievables.append((prepare_code.NotFound,
                                           bestmatch['name']))
                    return prepare_code.NotFound
                else:
                    continue
        try:
            dist = Dist(str(dist_loc))
        except ArchiveNotSupported:
            if not candidates:
                unretrievables.append((prepare_code.BadArchive, package_spec))
                return prepare_code.BadArchive
            else:
                continue
        if not dist.fromsetuptools and dist.has_metadata('requires'):
            requirements = dist.get_metadata('requires').split(',')
            for requirement in requirements:
                return_code = prepare(requirement)
                if return_code != prepare_code.Ok:
                    unretrievables.append((return_code, requirement))
        packages_to_install.append((bestmatch_from, dist, bestmatch))
        return prepare_code.Ok



def summary(pretend=False, ask=False):
    if pretend:
        print "Would have installed:"
    else:
        print "Will install:"

    for origin, dist, parsed_name in packages_to_install:
        print "%s %s (from %s)" % (parsed_name['name'],
                                   parsed_name['version'],
                                   origin)

    if len(unretrievables) > 0:
        print "But some dependencies have not been found:"

        for error, dep in unretrievables:
            print "%s (error code: %d)" % (dep, error)

        print "Please ensure these packages are correctly installed in your "\
                "system."

    if not pretend:
        if ask and raw_input("Is this ok?(y/N) ") not in YES:
            return
        install()




def install():
    for origin, dist, parsed_name in packages_to_install:
        print "installing %s %s" % (parsed_name['name'],\
                                    parsed_name['version']),
        try:
            ret = dist.install()
        except ArchiveNotSupported:
            print " ... Failed: ",
            print "Unable to extract files from archive"
        if ret == 0:
            print " ... OK"
        else:
            print " ... Failed: ",
            print " error code : %d", ret



if __name__ == '__main__':
    # command line parsing
    usage = '%prog [options] package-spec'
    version = 'itools %s' % __version__
    description = ("Install package from url")
    parser = OptionParser(usage, version=version, description=description)

    parser.add_option("-i", "--index-url",
                  dest="index_url", default="",
                  help="comma separated list of packages index url")

    parser.add_option("-c", "--cache-dir",
                  dest="cache_dir", default=TMP_DIR,
                  help="Cache directory, will download and decompress "\
                     "archives there")

    parser.add_option("-p", "--pretend",
                  dest="pretend", default=False, action="store_true",
                  help="Only print what isetup-install.py will do")

    parser.add_option("-a", "--ask",
                  dest="ask", default=False, action="store_true",
                  help="Ask before installing")


    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error('Please enter a package name')
    elif len(args) > 1:
        parser.error('Please enter only one package name')
    else:
        PACKAGE_SPEC = args[0]


    CACHE_DIR = options.cache_dir

    INDEX_URLS = options.index_url
    repositories = [PYPI_REPO] + INDEX_URLS.split(',')

    return_code = prepare(PACKAGE_SPEC)

    if return_code == prepare_code.NoAvailableCandidate:
        print "%s has not been found" % PACKAGE_SPEC
        exit(1)

    summary(pretend=options.pretend, ask=options.ask)

