#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2020 Sylvain Taverne <taverne.sylvain@gmail.com>
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

# Import from standard library
from os.path import islink, isdir

# Import from itools
from itools.pkg.build import ipkg_build, get_manifest
from itools.pkg.git import open_worktree
from itools.pkg.handlers import SetupConf


if __name__ == '__main__':
    config = SetupConf('setup.conf')
    worktree = open_worktree('.')
    manifest = { x for x in get_manifest() if not islink(x) and not isdir(x)}
    ipkg_build(worktree, manifest, config)
