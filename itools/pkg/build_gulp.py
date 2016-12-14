# -*- coding: UTF-8 -*-
# Copyright (C) 2016 Sylvain Taverne <taverne.sylvain@gmail.com>
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
from subprocess import call

# Import from itools
from itools.fs.vfs import Folder


class GulpBuilder(object):
    """
    Run "gulp build" in project's repository & add generated files
     $ ui/{SKINS}/dist/*
    into the project MANIFEST file.
    That allow to avoid commit compiled JS/CSS files into GIT.
    """


    def __init__(self, worktree, manifest):
        self.worktree = worktree
        self.manifest = manifest
        self.vfs = Folder('.')
        if self.vfs.is_folder('ui/'):
            self.dist_folders = tuple(['ui/{0}/dist'.format(x)
              for x in Folder('ui/').get_names()])
        self.all_files = list(self.vfs.traverse('.'))


    def run(self):
        if not 'gulpfile.js' in self.manifest:
            return
        # Launch gulp
        self.launch_gulp_if_needed()
        # Add DIST files into manifest
        for path in self.vfs.traverse('ui/'):
            relative_path = self.vfs.get_relative_path(path)
            if (relative_path and
                relative_path.startswith(self.dist_folders) and self.vfs.is_file(path)):
                self.manifest.add(relative_path)


    def launch_gulp_if_needed(self):
        dist_min_mtime = self.get_dist_min_mtime()
        if dist_min_mtime:
            has_to_run_gulp = self.has_to_run_gulp(dist_min_mtime)
            if not has_to_run_gulp:
                # Don't need to build gulp. All JS files are up to date
                return
        call(['npm', 'install'])
        call(['gulp', 'build'])


    def get_dist_min_mtime(self):
        min_mtime = None
        for path in self.all_files:
            relative_path = self.vfs.get_relative_path(path)
            if not relative_path:
                continue
            if (relative_path.startswith(self.dist_folders) and
                self.vfs.is_file(path)):
                mtime = self.vfs.get_mtime(path)
                if not min_mtime or mtime < min_mtime:
                    min_mtime = mtime
        return min_mtime


    compiled_extensions = ('.js', '.css', '.less', '.scss', '.json')
    def has_to_run_gulp(self, dist_min_mtime):
        ignore_folders = ('build/', 'gulpfile.js',) + self.dist_folders
        for path in self.all_files:
            relative_path = self.vfs.get_relative_path(path)
            if not relative_path:
                continue
            if relative_path.startswith(ignore_folders):
                continue
            if path.endswith(self.compiled_extensions):
                mtime = self.vfs.get_mtime(path)
                if mtime > dist_min_mtime:
                    print '* {} has changed'.format(relative_path)
                    return True
        return False
