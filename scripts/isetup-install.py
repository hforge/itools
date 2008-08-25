#!/usr/bin/env python
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

"""Usage:
isetup-install.py [options] package-spec

If the package is installed in package-spec do nothing.
If the package is not installed, then download if available from index-url to
cache-dir, "python setup.py build install" it, check if built with setuptools
or distutils, if it was with setuptools stop here, else check dependencies and
treat them with something like a "install_package" function.
"""

# Import from the Standard Library
from distutils.version import LooseVersion
from distutils.versionpredicate import VersionPredicate
from optparse import OptionParser
from operator import itemgetter
from os import sep
from os.path import join
import re
from sys import path, exit

# Import from itools
from itools import __version__
import itools.http
from itools.isetup import parse_package_name, download, get_installed_info
from itools.isetup import get_repository, EXTENSIONS, Dist
from itools.vfs import exists, is_folder, get_names, make_folder
from itools import vfs


# See --cache-dir option description
TMP_DIR = '/tmp/Packages'
PYPI_REPO = 'http://pypi.python.org/simple/'
YES = ('y', 'Y', 'yes', 'YES', 'ok', 'Yes', 'yep')

class Enumerate(object):
    """Utility Class
    """
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)


prepare_code = Enumerate('NoAvailableCandidate Ok BadArchive BadName '
                         'NotFound')
install_code = Enumerate('Ok SetupError UnknownError')

# List of unretrievables packages
unretrievables = []
# List of packages to install
packages_to_install = []



def find_installed_package(package_version):
    """Returns informations from package installed in the closest site
    directory possible, (eg. the package in use in this python).
    """
    # find the site-packages absolute path
    sites = set([])
    for dir in path:
        if 'site-packages' in dir:
            dir = dir.split(sep)
            sites.add(sep.join(dir[:dir.index('site-packages')+1]))

    # yield compatible packages
    for site in sites:
        infos = get_installed_info(site, package_version.name)
        if infos == None:
            continue
        try:
            new_version = LooseVersion(infos['version'])
        except ValueError:
            # if a package installed gives us an bogus version don't crash
            new_version = '?'
        infos['version'] = new_version
        return infos
    return None


def prepare(package_spec):
    """Work with a few globals variables, like repositories, ...
    """
    # Parse the version specifications
    try:
        package_version = VersionPredicate(package_spec)
    except ValueError:
        unretrievables.append((prepare_code.BadName, package_spec))
        return prepare_code.NoAvailableCandidate

    # Repository listing
    repo_candidates = []
    for repo_str in repositories:
        # If the repository has the package
        if exists(join(repo_str, package_version.name)):
            repo = get_repository(repo_str)
            # List versions of this package for this repository
            dists = repo.list_distributions(package_version.name)
            for dist in dists:
                if package_version.satisfied_by(dist['version']):
                    dist['version'] = LooseVersion(dist['version'])
                    repo_candidates.append(dist)

    # Cache listing
    if not exists(CACHE_DIR):
        make_folder(CACHE_DIR)

    cache_candidates = []
    cache_dir = vfs.open(CACHE_DIR)
    for filename in cache_dir.get_names('.'):
        dist = parse_package_name(filename)
        if dist['name'] == package_version.name and\
           dist['extension'] in EXTENSIONS:
            try:
                dist['version'] = LooseVersion(dist['version'])
                cache_candidates.append(dist)
            except ValueError:
                continue

    # Candidates sorting
    candidates  = [(dist['version'], 'cache', dist)\
                   for dist in cache_candidates]
    candidates += [(dist['version'], 'repository', dist)\
                   for dist in repo_candidates]

    candidates.sort(key=itemgetter(0))

    while candidates:
        # Iterate over candidates until "usable" package found
        bestmatch_version, bestmatch_from, bestmatch = candidates.pop()

        if bestmatch_from == 'cache':
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
        dist = Dist(str(dist_loc))
        if dist == None:
            if not candidates:
                unretrievables.append((prepare_code.BadArchive, package_spec))
                return prepare_code.BadArchive
            else:
                continue

        # At this point the package is thought to be ok
        # So we can recursvely parse its requirements
        if not dist.fromsetuptools and dist.has_metadata('Requires'):
            requirements = dist.get_metadata('Requires').split(',')
            for requirement in requirements:
                return_code = prepare(requirement)
                if return_code != prepare_code.Ok:
                    unretrievables.append((return_code, requirement))


        installed_package = find_installed_package(package_version)

        if installed_package == None:
            packages_to_install.append(('N', None,
                                        bestmatch_from, dist, bestmatch))
        elif installed_package['version'] == bestmatch_version:
            packages_to_install.append(('R', installed_package['version'],
                                        bestmatch_from, dist, bestmatch))
        elif installed_package['version'] < bestmatch_version:
            packages_to_install.append(('U', installed_package['version'],
                                        bestmatch_from, dist, bestmatch))
        elif installed_package['version'] > bestmatch_version:
            packages_to_install.append(('D', installed_package['version'],
                                        bestmatch_from, dist, bestmatch))

        return prepare_code.Ok

    else:
        # No candidates
        return prepare_code.NoAvailableCandidate



def summary(pretend=False, ask=False, force=False):
    """Prints a summary of operations that will come next
    """
    if len(packages_to_install) > 0:
        if pretend:
            print "Would have installed, in order:"
        else:
            print "Will install, in order:"
        print "Note : some packages may install other dependencies themself"

        for status, installed, origin, dist, infos in packages_to_install:
            print "[%s] %-18.18s [%-12.12s] (from: %s)" % (status,
                                                            infos['name'],
                                                            infos['version'],
                                                            origin),
            if installed:
                print " [%-12.12s]" % installed
            else:
                print

    if len(unretrievables) > 0:
        print
        print "Following packages have not been found:"

        for error, dep in unretrievables:
            if error == prepare_code.NoAvailableCandidate:
                print "%s: no package found in repositories" % dep
            elif error == prepare_code.BadArchive:
                print "%s: the package archive is malformed/unsupported" % dep
            elif error == prepare_code.BadName:
                print "%s: could not understand package name" % dep
            elif error == prepare_code.NotFound:
                print ("%s: present in repository, but unable to "
                       "download") % dep
            else:
                print "%s (error code: %d)" % (dep, error)

        if force:
            print "Please ensure these packages are correctly installed",
            print " in your system."
            print
        else:
            print "Cannot install the package"
            exit(1)

    if not pretend:
        if ask and raw_input("Is this ok?(y/N) ") not in YES:
            return
        install()


def install():
    for status, installed,origin, dist, infos in packages_to_install:
        print "installing %s %s" % (infos['name'],\
                                    infos['version']),
        ret = dist.install()
        if ret == 0:
            print " ... OK"
            continue

        print " ... Failed: ",
        if ret == -1:
            print "Unable to extract files from archive"
        else:
            print "error code : %d", ret



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

    parser.add_option("-f", "--force",
                  dest="force", default=False, action="store_true",
                  help="Force installation even if some dependencies are not"
                      " found")


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

    summary(pretend=options.pretend, ask=options.ask, force=options.force)

