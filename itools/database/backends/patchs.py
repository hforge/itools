# Copyright (C) 2020 Sylvain Taverne <sylvain@agicia.com>
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

from datetime import datetime, timedelta
from glob import glob
from time import strftime
from uuid import uuid4
import difflib
import os
import tarfile

# Import from itools
from itools.fs import lfs
from itools.loop import cron


TEST_DB_WITHOUT_PATCHS = bool(int(os.environ.get('TEST_DB_WITHOUT_PATCHS') or 0))


class PatchsBackend:

    rotate_interval = timedelta(weeks=2)

    def __init__(self, db_path, db_fs, read_only):
        self.db_fs = db_fs
        self.db_path = db_path
        # Init patchs folder
        self.patchs_path = f'{db_path}/database/.git/patchs'
        if not lfs.exists(self.patchs_path):
            lfs.make_folder(self.patchs_path)
        self.patchs_fs = lfs.open(self.patchs_path)
        # Launch rotate on patchs folder (only one time, so only on RW database)
        if not read_only:
            self.launch_rotate()


    def get_last_rotate_date(self):
        # Find the more recent date
        dates = []
        n2 = '[0-9][0-9]'
        date_pattern = n2 + n2 + '-' + n2 + '-' + n2 + '_' + n2 + n2
        for name in glob(self.patchs_path + '/' + date_pattern + '.tgz'):
            try:
                date = datetime.strptime(name[-18:-3], '%Y-%m-%d_%H%M')
            except ValueError:
                continue
            dates.append(date)
        if dates:
            dates.sort()
            return dates[-1]
        return None


    def launch_rotate(self):
        # FIXME it's too slow, we need to optimize it
        return
        last = self.get_last_rotate_date()
        # If here, there is no rotated files => so, we create one
        if not last:
            last = datetime.now()
            self.rotate()
        # Compute the next call
        next_call = last + self.rotate_interval - datetime.now()
        if next_call <= timedelta(0):
            next_call = timedelta(seconds=1)
        # Call cron
        cron(self.rotate, next_call)


    def rotate(self):
        gzip_folders = []
        for name in self.patchs_fs.get_names():
            try:
                patchs_date = datetime.strptime(name, '%Y%m%d')
            except ValueError:
                continue
            delta = datetime.now() - patchs_date
            if delta > self.rotate_interval:
                gzip_folders.append(self.patchs_path + '/' + name)
        # Check if we have something to gzip ?
        if not gzip_folders:
            return self.rotate_interval
        print('[Database] Launch patchs rotation. May take time')
        # Create TAR file
        tar_destination = self.patchs_path + f"/{strftime('%Y-%m-%d_%H%M')}.tgz"
        with tarfile.open(tar_destination, "w:gz" ) as tar:
            for gzip_folder in gzip_folders:
                tar.add(gzip_folder)
        # Remove old folders
        for gzip_folder in gzip_folders:
            self.patchs_fs.remove(gzip_folder)
        # We return always True to be "cron" compliant
        return self.rotate_interval



    def create_patch(self, added, changed, removed, handlers, git_author):
        """
        We create a patch into database/.git/patchs at each transaction.
        The idea is to commit into GIT each N transactions on big databases to avoid
        performances problems.
        We want to keep a diff on each transaction, to help debug.
        """
        if TEST_DB_WITHOUT_PATCHS is True:
            return
        author_id, author_email = git_author
        diffs = {}
        # Added
        for key in added:
            if key.endswith('.metadata'):
                after = handlers.get(key).to_str().splitlines(True)
                diff = difflib.unified_diff('', after, fromfile=key, tofile=key)
                diffs[key] = ''.join(diff)
        # Changed
        for key in changed:
            if key.endswith('.metadata'):
                with self.db_fs.open(key) as f:
                    before = f.readlines()
                before = [x.decode() for x in before]
                after = handlers.get(key).to_str().splitlines(True)
                diff = difflib.unified_diff(before, after, fromfile=key, tofile=key)
                diffs[key] = ''.join(diff)
        # Removed
        for key in removed:
            if key.endswith('.metadata'):
                with self.db_fs.open(key) as f:
                    before = f.readlines()
                before = [x.decode() for x in before]
                after = ''
                diff = difflib.unified_diff(before, after, fromfile=key, tofile=key)
                diffs[key] = ''.join(diff)
        # Create patch
        base_path = datetime.now().strftime('.git/patchs/%Y%m%d/')
        if not self.db_fs.exists(base_path):
            self.db_fs.make_folder(base_path)
        the_time = datetime.now().strftime('%Hh%Mm%S.%f')
        patch_key = f'{base_path}/{the_time}-user{author_id}-{uuid4()}.patch'
        data = ''.join(diffs[x] for x in sorted(diffs))
        data = data.encode()
        # Write
        with self.db_fs.open(patch_key, 'w') as f:
            f.write(data)
            f.truncate(f.tell())
