#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from datetime import datetime
from optparse import OptionParser
from subprocess import PIPE, Popen
import sys

# Import from itools
import itools
from itools import vfs


def parse_copyright(line):
    """
    From a copyright line:

        Copyright (C) 2005 Toto <toto@example.com>

    Extract the email address and the years.
    """
    line = line[16:].strip()
    # Split
    for i in range(len(line)):
        c = line[i]
        if not c.isdigit() and c not in (' ', ',', '-'):
            break
    name, email = line[i:].split('<')
    line = line[:i]
    # The email
    email = email[:-1]
    # The years
    years = set()
    for year in line.split(','):
        year = year.strip()
        if '-' in year:
            start, end = year.split('-')
            years.update(range(int(start), int(end) + 1))
        else:
            years.add(int(year))

    return email, name.strip(), years




if __name__ == '__main__':
    # The command line parser
    usage = '%prog [OPTIONS] FILES'
    version = 'itools %s' % itools.__version__
    description = (
        "Modifies the copyright notice in the given FILES. Uses 'git blame'"
        " to figure out the authors.")
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option('-k', '--keep', action='store_true', default=False,
        help='keep old copyright (a more conservative approach)')

    options, args = parser.parse_args()
    if len(args) == 0:
        parser.error('incorrect number of arguments')

    # Load CREDITS
    credits_names = {}  # Mapping from canonical email to real full name
    credits_mails = {}  # Mapping from secondary email to canonical email
    emails = []
    if vfs.exists('CREDITS'):
        with vfs.open('CREDITS') as file:
            for line in file.readlines():
                line = line.strip()
                if line:
                    key, value = line.split(':', 1)
                    value = value.lstrip()
                    if key == 'N':
                        name = value
                    elif key == 'E':
                        emails.append(value)
                        if len(emails) == 1:
                            credits_names[value] = name
                        else:
                            credits_mails[value] = emails[0]
                else:
                    emails = []

    # Go!
    for filename in args:
        # Call "git blame"
        popen = Popen(['git', 'blame', '-p', filename], stdout=PIPE)
        out, err = popen.communicate()

        header = True
        authors = {}
        for line in out.splitlines():
            if line.startswith('author '):
                name = line[7:]
            elif line.startswith('author-mail '):
                email = line[13:-1]
                if email in credits_mails:
                    email = credits_mails[email]
                if email in credits_names:
                    name = credits_names[email]
            elif line.startswith('author-time '):
                year = datetime.fromtimestamp(int(line[12:])).year
            elif line.startswith('\t'):
                # Don't consider the file header (copyright, license) as code
                data = line.lstrip()
                if not data.startswith('#'):
                    header = False
                if header is False:
                    authors.setdefault(email, (name, set()))
                    authors[email][1].add(year)

        # Keep old copyright
        if options.keep:
            lines = open(filename).readlines()
            # Skip shebang and encoding
            i = 0
            while not lines[i].startswith('# Copyright (C) '):
                i += 1
            # Process
            while lines[i].startswith('# Copyright (C) '):
                line = lines[i]
                email, name, years = parse_copyright(line)
                if email in credits_mails:
                    email = credits_mails[email]
                if email in credits_names:
                    name = credits_names[email]
                authors.setdefault(email, (name, set()))
                authors[email][1].update(years)
                i += 1

        # Format the lines
        copyright = []
        for email in authors:
            name, years = authors[email]
            years = list(years)
            years.sort()
            # Format the years ranges
            # [(year, year), year]
            aux = [years[0]]
            for year in years[1:]:
                if isinstance(aux[-1], int):
                    if aux[-1] == (year - 1):
                        aux[-1] = (aux[-1], year)
                    else:
                        aux.append(year)
                else:
                    if aux[-1][1] == (year - 1):
                        aux[-1] = (aux[-1][0], year)
                    else:
                        aux.append(year)
            # ['year-year', 'year']
            years = []
            for x in aux:
                if isinstance(x, int):
                    years.append(str(x))
                else:
                    years.append('%s-%s' % x)
            years = ', '.join(years)
            copyright.append('# Copyright (C) %s %s <%s>\n' % (years, name,
                email))
        copyright.sort()

        # Replace the old copyright by the new one
        lines = open(filename).readlines()
        i = 0
        while not lines[i].startswith('# Copyright (C) '):
            i += 1
        while lines[i].startswith('# Copyright (C) '):
            del lines[i]
        lines = lines[:i] + copyright + lines[i:]

        # Write
        open(filename, 'w').write(''.join(lines))
