# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007-2008, 2010-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2010 David Versmisse <versmisse@lil.univ-littoral.fr>
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
import fnmatch
from logging import getLogger

# Import from itools
from itools.fs import lfs
from itools.handlers import Folder

# Import from here
from .backends import backends_registry
from .registry import get_register_fields
from .ro import RODatabase

log = getLogger("itools.database")

MSG_URI_IS_BUSY = 'The "%s" URI is busy.'


class RWDatabase(RODatabase):

    read_only = False

    def __init__(self, path, size_min, size_max, backend='git'):
        proxy = super(RWDatabase, self)
        proxy.__init__(path, size_min, size_max, backend)
        # Changes on DB
        self.added = set()
        self.changed = set()
        self.removed = set()
        self.has_changed = False

        # The resources that been added, removed, changed and moved can be
        # represented as a set of two element tuples.  But we implement this
        # with two dictionaries (old2new/new2old), to be able to access any
        # "tuple" by either value.  With the empty tuple we represent the
        # absence of change.
        #
        #  Tuple        Description                Implementation
        #  -----------  -------------------------  -------------------
        #  ()           nothing has been done yet  {}/{}
        #  (None, 'b')  resource 'b' added         {}/{'b':None}
        #  ('b', None)  resource 'b' removed       {'b':None}/{}
        #  ('b', 'b')   resource 'b' changed       {'b':'b'}/{'b':'b'}
        #  ('b', 'c')   resource 'b' moved to 'c'  {'b':'c'}/{'c':'b'}
        #  ???          resource 'b' replaced      {'b':None}/{'b':None}
        #
        # In real life, every value is either None or an absolute path (as a
        # byte stringi).  For the description that follows, we use the tuples
        # as a compact representation.
        #
        # There are four operations:
        #
        #  A(b)   - add "b"
        #  R(b)   - remove "b"
        #  C(b)   - change "b"
        #  M(b,c) - move "b" to "c"
        #
        # Then, the algebra is:
        #
        # ()        -> A(b) -> (None, 'b')
        # (b, None) -> A(b) -> (b, b)
        # (None, b) -> A(b) -> error
        # (b, b)    -> A(b) -> error
        # (b, c)    -> A(b) -> (b, b), (None, c) FIXME Is this correct?
        #
        # TODO Finish
        #
        self.resources_old2new = {}
        self.resources_new2old = {}
        self.resources_old2new_catalog = {}
        self.resources_new2old_catalog = {}


    def check_catalog(self):
        pass


    def close(self):
        self.abort_changes()
        self.backend.close()


    def _sync_filesystem(self, key):
        # Don't check if handler has been modified since last loading,
        # we only have one writer
        handler = self.cache.get(key)
        return handler

    #######################################################################
    # Layer 0: handlers
    #######################################################################
    def has_handler(self, key):
        key = self.normalize_key(key)

        # A new file/directory is only in added
        n = len(key)
        for f_key in self.added:
            if f_key[:n] == key and (len(f_key) == n or f_key[n] == '/'):
                return True

        # Normal case
        return super(RWDatabase, self).has_handler(key)


    def _get_handler(self, key, cls=None, soft=False):
        # A hook to handle the new directories
        base = key + '/'
        n = len(base)
        for f_key in self.added:
            if f_key[:n] == base:
                return Folder(key, database=self)

        # The other files
        return super(RWDatabase, self)._get_handler(key, cls, soft)


    def set_handler(self, key, handler):
        # TODO: We have to refactor the set_changed()
        # mechanism in handlers/database
        # At first load we don't have to set handler as changed
        # But if we set values without loading handler, the
        # handler should be set as changed
        handler.loaded = True
        handler.set_changed()
        if type(handler) is Folder:
            raise ValueError('unexpected folder (only files can be "set")')

        if handler.key is not None:
            raise ValueError('only new files can be added, try to clone first')

        key = self.normalize_key(key)
        if self._get_handler(key, soft=True) is not None:
            raise RuntimeError(MSG_URI_IS_BUSY % key)

        # Added or modified ?
        if key not in self.added and self.has_handler(key):
            self.changed.add(key)
        else:
            self.added.add(key)
        # Push in cache
        self.push_handler(key, handler)
        # Changed
        self.removed.discard(key)
        self.has_changed = True


    def del_handler(self, key):
        key = self.normalize_key(key)

        # Case 1: file
        handler = self._get_handler(key)
        if type(handler) is not Folder:
            self._discard_handler(key)
            if key in self.added:
                self.added.remove(key)
            else:
                self.changed.discard(key)
                # Changed
                self.removed.add(key)
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
        # Changed
        self.removed.add(key)
        self.has_changed = True


    def touch_handler(self, key, handler=None):
        key = self.normalize_key(key)
        # Mark the handler as dirty
        handler.dirty = datetime.now()
        # Do some checks
        if handler is None:
            raise ValueError
        if key in self.removed:
            raise ValueError
        # Set database has changed
        self.has_changed = True
        # Set in changed list
        if key not in self.added:
            self.changed.add(key)



    def save_handler(self, key, handler):
        self.backend.save_handler(key, handler)


    def get_handler_names(self, key):
        key = self.normalize_key(key)
        # On the filesystem
        names = super(RWDatabase, self).get_handler_names(key)
        names = set(names)
        # In added
        if key:
            base = key + '/'
        else:
            base = ''
        n = len(base)
        for f_key in self.added:
            if f_key[:n] == base:
                name = f_key[n:].split('/', 1)[0]
                names.add(name)
        return list(names)


    def copy_handler(self, source, target, exclude_patterns=None):
        source = self.normalize_key(source)
        target = self.normalize_key(target)

        # The trivial case
        if source == target:
            return

        # Ignore copy of some handlers
        if exclude_patterns is None:
            exclude_patterns = []
        for exclude_pattern in exclude_patterns:
            if fnmatch.fnmatch(source, exclude_pattern):
                return

        # Check the target is free
        if self._get_handler(target, soft=True) is not None:
            raise RuntimeError(MSG_URI_IS_BUSY % target)

        handler = self._get_handler(source)
        if type(handler) is Folder:
            raise ValueError('Cannot copy folders')
        handler = handler.clone()
        self.push_handler(target, handler)
        self.added.add(target)

        # Changed
        self.removed.discard(target)
        self.has_changed = True


    def move_handler(self, source, target):
        source = self.normalize_key(source)
        target = self.normalize_key(target)

        # The trivial case
        if source == target:
            return

        # Check the target is free
        if self._get_handler(target, soft=True) is not None:
            raise RuntimeError(MSG_URI_IS_BUSY % target)

        # Go
        cache = self.cache

        # Case 1: file
        handler = self._get_handler(source)
        if type(handler) is not Folder:

            # Remove source
            self.added.discard(source)
            self.changed.discard(source)
            self.cache.pop(source)

            # Add target
            self.push_handler(target, handler)
            self.added.add(target)

            # Changed
            self.removed.add(source)
            self.removed.discard(target)
            self.has_changed = True
            return

        # In target in cache
        self.added.add(target)
        self.push_handler(target, handler)

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

        # Changed
        self.removed.add(source)
        self.removed.discard(target)
        self.has_changed = True


    #######################################################################
    # Layer 1: resources
    #######################################################################
    def remove_resource(self, resource):
        self.has_changed = True
        old2new = self.resources_old2new
        new2old = self.resources_new2old
        for x in resource.traverse_resources():
            path = str(x.abspath)
            old2new[path] = None
            new2old.pop(path, None)
            self.resources_old2new_catalog[path] = None
            self.resources_new2old_catalog.pop(path, None)


    def add_resource(self, resource):
        self.has_changed = True
        new2old = self.resources_new2old
        # Catalog
        for x in resource.traverse_resources():
            path = str(x.abspath)
            new2old[path] = None


    def change_resource(self, resource):
        self.has_changed = True
        old2new = self.resources_old2new
        new2old = self.resources_new2old
        # Case 1: added, moved in-here or already changed
        path = str(resource.abspath)
        if path in new2old:
            return
        # Case 2: removed or moved away
        if path in old2new and not old2new[path]:
            raise ValueError('cannot change a resource that has been removed')
        # Case 3: not yet touched
        old2new[path] = path
        new2old[path] = path
        self.resources_old2new_catalog[path] = path
        self.resources_new2old_catalog[path] = path


    def is_changed(self, resource):
        """We use for this function only the 2 dicts old2new and new2old.
        """
        old2new = self.resources_old2new
        new2old = self.resources_new2old
        path = str(resource.abspath)
        return path in old2new or path in new2old


    def move_resource(self, source, new_path):
        self.has_changed = True
        old2new = self.resources_old2new
        new2old = self.resources_new2old

        old_path = source.abspath
        for x in source.traverse_resources():
            source_path = x.abspath
            target_path = new_path.resolve2(old_path.get_pathto(source_path))

            source_path = str(source_path)
            target_path = str(target_path)
            if source_path in old2new and not old2new[source_path]:
                err = 'cannot move a resource that has been removed'
                raise ValueError(err)

            source_path = new2old.pop(source_path, source_path)
            if source_path:
                old2new[source_path] = target_path
                self.resources_old2new_catalog[source_path] = target_path
            new2old[target_path] = source_path
            self.resources_new2old_catalog[target_path] = source_path


    #######################################################################
    # Transactions
    #######################################################################
    def _cleanup(self):
        super(RWDatabase, self)._cleanup()
        self.has_changed = False


    def _abort_changes(self):
        # 1. Handlers
        cache = self.cache
        for key in self.added:
            self._discard_handler(key)
        for key in self.changed:
            if cache.has_key(key):
                # FIXME
                # We check cache since an handler
                # can be added & changed at one
                # (Maybe we have to change this behaviour)
                cache[key].abort_changes()

        # 2. Abort in backend
        self.backend.abort_transaction()

        # Reset state
        self.added.clear()
        self.changed.clear()
        self.removed.clear()

        # Resources
        self.resources_old2new.clear()
        self.resources_new2old.clear()
        self.resources_old2new_catalog.clear()
        self.resources_new2old_catalog.clear()


    def abort_changes(self):
        if not self.has_changed:
            return

        self._abort_changes()
        self._cleanup()


    def _before_commit(self):
        """This method is called before 'save_changes', and gives a chance
        to the database to check for preconditions, if an error occurs here
        the transaction will be aborted.

        The value returned by this method will be passed to '_save_changes',
        so it can be used to pre-calculate whatever data is needed.
        """
        return None, None, None, [], []


    def _save_changes(self, data, commit_msg=None):
        # Get data informations
        the_author, the_date, the_msg, docs_to_index, docs_to_unindex = data
        # Check
        if (not self.added and not self.changed and not self.removed and
            not docs_to_index and not docs_to_unindex):
            msg = 'No changes, should never happen'
            raise ValueError(msg)
        # Do transaction
        self.backend.do_transaction(commit_msg,
            data, self.added, self.changed, self.removed, self.cache,
            docs_to_index, docs_to_unindex)
        # 6. Clear state
        self.changed.clear()
        self.added.clear()
        self.removed.clear()


    def save_changes(self, commit_message=None):
        if not self.has_changed:
            return
        # Prepare for commit, do here the most you can, if something fails
        # the transaction will be aborted
        try:
            data = self._before_commit()
        except Exception as e:
            log.error("Transaction failed", exc_info=True)
            try:
                self._abort_changes()
            except Exception as e:
                log.error("Aborting failed", exc_info=True)
            self._cleanup()
            raise

        # Commit
        try:
            self._save_changes(data, commit_message)
        except Exception as e:
            log.error("Transaction failed", exc_info=True)
            try:
                self._abort_changes()
            except Exception as e:
                log.error("Aborting failed", exc_info=True)
            raise e
        finally:
            self._cleanup()


    def flush_catalog(self):
        """ Flush changes in catalog without commiting
        (allow to search in catalog on changed elements)
        """
        try:
            data = self._before_commit()
        except Exception as e:
            log.error("Transaction failed", exc_info=True)
            try:
                self._abort_changes()
            except Exception as e:
                log.error("Aborting failed", exc_info=True)
            self._cleanup()
            raise
        _, _, _, docs_to_index, docs_to_unindex = data
        self.backend.flush_catalog(docs_to_unindex, docs_to_index)


    def reindex_catalog(self, base_abspath, recursif=True):
        """Reindex the catalog & return nb resources re-indexed
        """
        catalog = self.catalog
        base_resource = self.get_resource(base_abspath, soft=True)
        if base_resource is None:
            return 0
        n = 0
        # Recursif ?
        if recursif:
            for item in base_resource.traverse_resources():
                values = item.get_catalog_values()
                catalog.index_document(values)
                n += 1
        else:
            # Reindex resource
            values = base_resource.get_catalog_values()
            catalog.index_document(values)
            n = 1
        # Save catalog if has changes
        if n > 0:
            catalog.save_changes()
        # Ok
        return n


def make_database(path, size_min, size_max, fields=None, backend=None):
    """Create a new empty database if the given path does not exists or
    is a folder.
    """
    path = lfs.get_absolute_path(path)
    if fields is None:
        fields = get_register_fields()
    # Init backend
    backend_cls = backends_registry[backend]
    backend_cls.init_backend(path, fields)
    # Ok
    return RWDatabase(path, size_min, size_max)
