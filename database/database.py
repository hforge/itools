# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from datetime import datetime
from os.path import dirname
from subprocess import CalledProcessError

# Import from itools
from itools.core import LRUCache, send_subprocess, freeze
from itools.datatypes import ISODateTime
from itools.fs import lfs
from itools.handlers import Folder, RODatabase
from itools.uri import Path



MSG_URI_IS_BUSY = 'The "%s" URI is busy.'


class ROGitDatabase(RODatabase):

    def __init__(self, path, size_min=4800, size_max=5200):
        if not lfs.is_folder(path):
            raise ValueError, '"%s" should be a folder, but it is not' % path

        # Initialize the database, but chrooted
        fs = lfs.open(path)
        super(ROGitDatabase, self).__init__(size_min, size_max, fs=fs)

        # Keep the path close, to be used by 'send_subprocess'
        self.path = '%s/' % fs.path

        # The git cache
        self.git_cache = LRUCache(900, 1100)


    def normalize_key(self, path, __root=Path('/')):
        # Performance is critical so assume the path is already relative to
        # the repository.
        key = __root.resolve(path)
        if key and key[0] == '.git':
            err = "bad '%s' path, access to the '.git' folder is denied"
            raise ValueError, err % path

        return '/'.join(key)


    def push_phantom(self, key, handler):
        handler.database = self
        handler.key = key


    def is_phantom(self, handler):
        return handler.timestamp is None and handler.dirty is not None


    def get_diff(self, revision):
        cmd = ['git', 'show', revision, '--pretty=format:%an%n%at%n%s']
        data = send_subprocess(cmd, path=self.path)
        lines = data.splitlines()

        ts = int(lines[1])
        return {
            'author_name': lines[0],
            'author_date': datetime.fromtimestamp(ts),
            'subject': lines[2],
            'diff': '\n'.join(lines[2:])}


    def get_files_affected(self, revisions):
        """Get the unordered set of files affected by a list of revisions.
        """
        cmd = ['git', 'show', '--numstat', '--pretty=format:'] + revisions
        data = send_subprocess(cmd, path=self.path)
        lines = data.splitlines()
        files = set()
        for line in lines:
            if not line:
                continue
            before, after, filename = line.split('\t')
            files.add(filename)
        return freeze(files)


    def get_stats(self, from_, to=None, paths=[]):
        if to is None:
            cmd = ['git', 'show', '--pretty=format:', '--stat', from_]
        else:
            cmd = ['git', 'diff', '--stat', from_, to]

        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return send_subprocess(cmd, path=self.path)


    def get_diff_between(self, from_, to='HEAD', paths=[]):
        """Get the diff of the given path from the given commit revision to
        HEAD.

        If "stat" is True, get a diff stat only.
        """
        cmd = ['git', 'diff', from_, to]
        if paths:
            cmd.append('--')
            cmd.extend(paths)
        return send_subprocess(cmd, path=self.path)


    def get_blob(self, hash, cls):
        if type(hash) is not str:
            raise TypeError, 'get_blob expects a string, %s found' % type(hash)

        if len(hash) != 40:
            raise ValueError, 'a git hash is 40 chars long, not %d' % len(hash)

        if hash in self.git_cache:
            return self.git_cache[hash]

        cmd = ['git', 'show', hash]
        blob = send_subprocess(cmd, path=self.path)
        blob = cls(string=blob)
        self.git_cache[hash] = blob
        return blob


    def get_commit_hashs(self, file):
        """Give the hashs for all commit concerning file
        """
        cmd = ['git', 'log', '--reverse', '--pretty=format:%H', file]
        log = send_subprocess(cmd, path=self.path)
        return log.splitlines()


    def get_blob_by_revision_and_path(self, revision, path, cls):
        """Get the file contents located at the given path after the given
        commit revision has been committed.
        """
        arg = '%s:%s' % (revision, path)
        cmd = ['git', 'rev-parse', arg]
        hash = send_subprocess(cmd, path=self.path)
        hash = hash.rstrip('\n')
        return self.get_blob(hash, cls)



class GitDatabase(ROGitDatabase):

    def __init__(self, path, size_min, size_max):
        super(GitDatabase, self).__init__(path, size_min, size_max)

        # The "git add" arguments
        self.added = set()
        self.changed = set()
        self.has_changed = False


    def is_phantom(self, handler):
        # Phantom handlers are "new"
        if handler.timestamp or not handler.dirty:
            return False
        # They are attached to this database, but they are not in the cache
        return handler.database is self and handler.key not in self.cache


    def has_handler(self, key):
        key = self.normalize_key(key)

        # A new file/directory is only in added
        n = len(key)
        for f_key in self.added:
            if f_key[:n] == key and (len(f_key) == n or f_key[n] == '/'):
                return True

        # Normal case
        return super(GitDatabase, self).has_handler(key)


    def get_handler(self, key, cls=None):
        key = self.normalize_key(key)

        # A hook to handle the new directories
        base = key + '/'
        n = len(base)
        for f_key in self.added:
            if f_key[:n] == base:
                if cls is None:
                    cls = Folder
                return cls(key, database=self)

        # The other files
        return super(GitDatabase, self).get_handler(key, cls)


    def set_handler(self, key, handler):
        if isinstance(handler, Folder):
            raise ValueError, 'unexpected folder (only files can be "set")'

        if handler.key is not None:
            raise ValueError, 'only new files can be added, try to clone first'

        key = self.normalize_key(key)
        if self.has_handler(key):
            raise RuntimeError, MSG_URI_IS_BUSY % key

        self.push_handler(key, handler)
        self.added.add(key)
        # Changed
        self.has_changed = True


    def del_handler(self, key):
        key = self.normalize_key(key)

        # Case 1: file
        handler = self.get_handler(key)
        if not isinstance(handler, Folder):
            self._discard_handler(key)
            if key in self.added:
                self.added.remove(key)
            else:
                self.changed.discard(key)
                self.fs.remove(key)
            # Changed
            self.has_changed = True
            return

        # Case 2: folder
        base = key + '/'
        for k in self.added.copy():
            if k.startswith(base):
                self._discard_handler(k)
                self.added.discard(k)

        for k in self.changed.copy():
            if k.startswith(base):
                self._discard_handler(k)
                self.changed.discard(k)

        if self.fs.exists(key):
            self.fs.remove(key)

        # Changed
        self.has_changed = True


    def touch_handler(self, key, handler=None):
        key = self.normalize_key(key)

        # Useful for the phantoms
        if handler is None:
            handler = self.get_handler(key)

        # The phantoms become real files
        if self.is_phantom(handler):
            self.cache[key] = handler
            self.added.add(key)
            self.has_changed = True
            return

        if handler.dirty is None:
            # Load the handler if needed
            if handler.timestamp is None:
                handler.load_state()
            # Mark the handler as dirty
            handler.dirty = datetime.now()
            # Update database state (XXX Should we do this?)
            self.changed.add(key)
            # Changed
            self.has_changed = True


    def get_handler_names(self, key):
        key = self.normalize_key(key)

        # On the filesystem
        names = super(GitDatabase, self).get_handler_names(key)
        names = set(names)

        # In added
        base = key + '/'
        n = len(base)
        for f_key in self.added:
            if f_key[:n] == base:
                name = f_key[n:].split('/', 1)[0]
                names.add(name)

        # Remove .git
        if key == "":
            names.discard('.git')

        return list(names)


    def copy_handler(self, source, target):
        source = self.normalize_key(source)
        target = self.normalize_key(target)

        # The trivial case
        if source == target:
            return

        # Check the target is free
        if self.has_handler(target):
            raise RuntimeError, MSG_URI_IS_BUSY % target

        handler = self.get_handler(source)

        # Folder
        if isinstance(handler, Folder):
            fs = self.fs
            for name in handler.get_handler_names():
                self.copy_handler(fs.resolve2(source, name),
                                  fs.resolve2(target, name))
        # File
        else:
            handler = handler.clone()
            self.push_handler(target, handler)
            self.added.add(target)

        # Changed
        self.has_changed = True


    def move_handler(self, source, target):
        source = self.normalize_key(source)
        target = self.normalize_key(target)

        # The trivial case
        if source == target:
            return

        # Check the target is free
        if self.has_handler(target):
            raise RuntimeError, MSG_URI_IS_BUSY % target

        # Go
        fs = self.fs
        cache = self.cache

        # Case 1: file
        handler = self.get_handler(source)
        if not isinstance(handler, Folder):
            if fs.exists(source):
                fs.move(source, target)

            # Remove source
            self.added.discard(source)
            self.changed.discard(source)
            del cache[source]
            # Add target
            self.push_handler(target, handler)
            self.added.add(target)

            # Changed
            self.has_changed = True
            return

        # Case 2: Folder
        n = len(source)
        base = source + '/'
        for key in self.added.copy():
            if key.startswith(base):
                new_key = '%s%s' % (target, key[n:])
                handler = cache.pop(key)
                self.push_handler(new_key, handler)
                self.added.remove(key)
                self.added.add(new_key)

        for key in self.changed.copy():
            if key.startswith(base):
                new_key = '%s%s' % (target, key[n:])
                handler = cache.pop(key)
                self.push_handler(new_key, handler)
                self.changed.remove(key)

        if fs.exists(source):
            fs.move(source, target)
        for path in fs.traverse(target):
            if not fs.is_folder(path):
                path = fs.get_relative_path(path)
                self.added.add(path)

        # Changed
        self.has_changed = True


    #######################################################################
    # API / Transactions
    def _cleanup(self):
        super(GitDatabase, self)._cleanup()
        self.has_changed = False


    def _abort_changes(self):
        cache = self.cache
        # Added handlers
        for key in self.added:
            self._discard_handler(key)
        # Changed handlers
        for key in self.changed:
            cache[key].abort_changes()

        # And now, clean the filesystem
        try:
            # In a try/except to avoid a problem with new repositories
            send_subprocess(['git', 'reset', '--hard', '-q'], path=self.path)
        except CalledProcessError:
            pass
        if self.added:
            send_subprocess(['git', 'clean', '-fxdq'], path=self.path)

        # Reset state
        self.added.clear()
        self.changed.clear()


    def _rollback(self):
        pass


    def _before_commit(self):
        """This method is called before 'save_changes', and gives a chance
        to the database to check for preconditions, if an error occurs here
        the transaction will be aborted.

        The value returned by this method will be passed to '_save_changes',
        so it can be used to pre-calculate whatever data is needed.
        """
        return None, None, None


    def _save_changes(self, data):
        # Synchronize eventually the handlers and the filesystem
        for key in self.added:
            handler = self.cache.get(key)
            if handler and handler.dirty:
                parent_path = dirname(key)
                if not self.fs.exists(parent_path):
                    self.fs.make_folder(parent_path)
                handler.save_state()

        for key in self.changed:
            handler = self.cache[key]
            handler.save_state()

        self.changed.clear()

        # Call a "git add" eventually for new and/or moved files
        if self.added:
            send_subprocess(['git', 'add'] + list(self.added), path=self.path)
            self.added.clear()

        # Commit
        git_author, git_date, git_message = data
        command = ['git', 'commit', '-aq', '-m', git_message or 'no comment']
        if git_author:
            command.append('--author=%s' % git_author)
        if git_date:
            git_date = ISODateTime.encode(git_date)
            command.append('--date=%s' % git_date)
        try:
            send_subprocess(command, path=self.path)
        except CalledProcessError, excp:
            # Avoid an exception for the 'nothing to commit' case
            # FIXME Not reliable, we may catch other cases
            if excp.returncode != 1:
                raise


    def save_changes(self):
        if not self.has_changed:
            return

        # Prepare for commit, do here the most you can, if something fails
        # the transaction will be aborted
        try:
            data = self._before_commit()
        except:
            self._abort_changes()
            self._cleanup()
            raise

        # Commit
        try:
            self._save_changes(data)
        except Exception:
            self._rollback()
            self._abort_changes()
            raise
        finally:
            self._cleanup()




def make_git_database(path, size_min, size_max):
    """Create a new empty Git database if the given path does not exists or
    is a folder.

    If the given path is a folder with content, the Git archive will be
    initialized and the content of the folder will be added to it in a first
    commit.
    """
    path = lfs.get_absolute_path(path)
    if not lfs.exists(path):
        lfs.make_folder(path)

    # Init
    send_subprocess(['git', 'init', '-q'], path=path)

    # Add
    send_subprocess(['git', 'add', '.'], path=path)

    # Commit or not ?
    try:
        send_subprocess(['git', 'commit', '-q', '-m', 'Initial commit'],
                        path=path)
    except CalledProcessError:
        pass

    # Ok
    return GitDatabase(path, size_min, size_max)
