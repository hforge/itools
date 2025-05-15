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
import os
import sys
from subprocess import Popen

# Import from itools
from itools.fs.lfs import LocalFolder
from itools.uri import get_uri_name, Path


class GulpBuilder:
    """
    Run "gulp build" in project's repository & add generated files
     $ ui/{SKINS}/*
    into the project MANIFEST file.
    That allow to avoid commit compiled JS/CSS files into GIT.
    """

    def __init__(self, package_root, worktree, manifest):
        self.package_root = package_root
        if self.package_root != '.':
            self.ui_path = f'{self.package_root}/ui/'
        else:
            self.ui_path = 'ui/'
        self.worktree = worktree
        self.manifest = manifest
        self.fs = LocalFolder('.')
        if self.fs.is_folder(self.ui_path):
            self.dist_folders = tuple([f'{self.ui_path}{x}' for x in LocalFolder(self.ui_path).get_names()])

    def run(self):
        npm_done = self.launch_npm_install()
        gulp_done = self.launch_gulp_build()
        webpack_done = self.launch_webpack()
        # Add DIST files into manifest
        if (npm_done or gulp_done or webpack_done) and self.fs.exists(self.ui_path):
            for path in self.fs.traverse(self.ui_path):
                relative_path = self.fs.get_relative_path(path)
                if (relative_path and
                    relative_path.startswith(self.dist_folders) and self.fs.is_file(path)):
                    self.manifest.add(relative_path)

    def launch_npm_install(self):
        done = False
        for path in self.manifest:
            filename = get_uri_name(path)
            if filename == 'package.json':
                print("***"*25)
                print(f"*** Run $ npm install on {path}")
                print("***"*25)
                path = str(Path(path)[:-1]) + '/'
                p = Popen(['npm', 'install'], cwd=path)
                p.wait()
                if p.returncode == 1:
                    print("***"*25)
                    print(f"*** Error running npm install {path}")
                    print("***"*25)
                    sys.exit(1)
                done = True
        return done

    def launch_gulp_build(self):
        done = False
        for path in self.manifest:
            filename = get_uri_name(path)
            if filename == 'gulpfile.js':
                cwd = str(Path(path)[:-1]) + '/'
                print("***"*25)
                print(f"*** Run $ gulp build on {path} from {cwd}")
                print(f"*** Current working directory: {os.getcwd()}")
                print("***"*25)
                p = Popen(['./node_modules/.bin/gulp', 'build'], cwd=cwd)
                p.wait()
                if p.returncode == 1:
                    print("***"*25)
                    print(f"*** Error running gulp {path}")
                    print("***"*25)
                    sys.exit(1)
                done = True
        return done

    def launch_webpack(self):
        done = False
        for path in self.manifest:
            filename = get_uri_name(path)
            if filename == 'webpack.config.js':
                cwd = str(Path(path)[:-1]) + '/'
                print("***"*25)
                print(f"*** Run $ webpack {path} from {cwd}")
                print(f"*** Current working directory: {os.getcwd()}")
                print("***"*25)
                p = Popen(['./node_modules/.bin/webpack', '--mode=production'], cwd=cwd)
                p.wait()
                if p.returncode == 1:
                    print("***"*25)
                    print(f"*** Error running webpack {path}")
                    print("***"*25)
                    sys.exit(1)
                done = True
        return done
