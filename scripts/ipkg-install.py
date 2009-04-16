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
ipkg-install.py [options] package-spec

If the package is installed in package-spec do nothing.
If the package is not installed, then download if available from index-url to
cache-dir, "python setup.py build install" it, check if built with setuptools
or distutils, if it was with setuptools stop here, else check dependencies and
treat them with something like a "install_package" function.
"""

# Import from the Standard Library
from distutils.version import LooseVersion
from distutils.versionpredicate import VersionPredicate
from operator import itemgetter
from optparse import OptionParser
from os import sep
from os.path import join
from sys import path, exit
from tempfile import gettempdir
from xml.parsers.expat import ExpatError
from xmlrpclib import Server, ProtocolError
import socket

# Import from itools
from itools import __version__
from itools.pkg import parse_package_name, download, get_installed_info
from itools.pkg import EXTENSIONS, Bundle
from itools.vfs import exists, get_names, make_folder
from itools import vfs


# See --cache-dir option description
TMP_DIR = '%s/Packages' % gettempdir()
PYPI_REPO = 'http://pypi.python.org/pypi'
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
    """ global variables used :
           * repositories
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
        # XXX
        if not repo_str.startswith('http://'):
            repo_str = 'http://' + repo_str
        try:
            repo = Server(repo_str)
            for repo_ver in repo.package_releases(package_version.name):
                if package_version.satisfied_by(repo_ver):
                    releases = repo.release_urls(package_version.name,
                                                 repo_ver)
                    # XXX
                    # Take only acceptable package type and with python
                    # version compatible
                    for release in releases:
                        # We must check following attributes
                        #release['packagetype'] == 'bdist_egg',
                        # 'bdist_wininst', 'bdist_rpm', 'bdist_dumb',
                        # 'bdist_msi'
                        #release['python_version'] == '2.4', '2.5', 'any',
                        # 'source'
                        if release['packagetype'] == 'sdist':
                            release['name'] = package_version.name
                            release['version'] = LooseVersion(repo_ver)
                            release['str_version'] = repo_ver
                            release['pypi_server'] = repo
                            release['pypi_location'] = repo_str
                            repo_candidates.append(release)
        # Any error related to the CheeseShop server
        except (IOError, ExpatError, ProtocolError, socket.error):
            print ("WARNING: %s is not a valid CheeseShop repository" %
                   repo_str)

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

        requirements = []
        if bestmatch_from == 'cache':
            dist_loc = join(CACHE_DIR, bestmatch['file'])
            dist = Bundle(str(dist_loc))

            if dist == None:
                if candidates:
                    continue
                unretrievables.append((prepare_code.BadArchive,
                                       package_spec))
                return prepare_code.BadArchive

            if not dist.fromsetuptools:
                requires = dist.get_metadata('Requires')
                if requires is not None:
                    requirements = requires.split(',')

        elif bestmatch_from == 'repository':
            pypi_server = bestmatch['pypi_server']
            release_data = pypi_server.release_data(package_version.name,
                                                    bestmatch['str_version'])
            requirements = release_data['requires']

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

        total_download = 0
        for code, installed, origin, dist, data in packages_to_install:
            print "[%s] %-14.14s [%-19.19s] (from %s)" % (code,
                                                          data['name'],
                                                          data['version'],
                                                          origin),

            if origin == 'repository':
                total_download += data['size']

            print installed and "[%-19.19s]" % installed or ''

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

    #XXX better formating
    print "%d.%d ko will be downloaded" % ((total_download / 1024),
                                           (total_download % 1024))

    if not pretend:
        if ask and raw_input("Is this ok?(y/N) ") not in YES:
            return
        install()


def install():
    for status, installed, origin, dist, data in packages_to_install:
        print "installing %s %s" % (data['name'],
                                    data['version'])

        if origin == 'repository':
           print "Downloading %s ..." % data['url']
           dist_loc = download(data['url'], CACHE_DIR)
           dist = Bundle(str(dist_loc))

        ret = dist.install()

        if ret == 0:
            print "%s %s has been successfully installed" % (data['name'],
                                                            data['version'])
            continue

        print "%s %s failed to install" % (data['name'],
                                           data['version'])
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

    parser.add_option("-r", "--repository",
                  dest="repository", default="",
                  help="comma separated list of packages index url")

    parser.add_option("-c", "--cache-dir",
                  dest="cache_dir", default=TMP_DIR,
                  help="Cache directory, will download and decompress "\
                     "archives there")

    parser.add_option("-p", "--pretend",
                  dest="pretend", default=False, action="store_true",
                  help="Only print what ipkg-install.py will do")

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

    INDEX_URLS = options.repository
    repositories = INDEX_URLS.split(',') + [PYPI_REPO]

    return_code = prepare(PACKAGE_SPEC)

    if return_code == prepare_code.NoAvailableCandidate:
        print "%s has not been found" % PACKAGE_SPEC
        exit(1)

    summary(pretend=options.pretend, ask=options.ask, force=options.force)

