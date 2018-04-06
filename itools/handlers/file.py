# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007-2008 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2009-2010 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009-2010 Hervé Cauwelier <herve@oursours.net>
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
from copy import deepcopy
from cStringIO import StringIO
from datetime import datetime
from sys import exc_info

# Import from itools
from itools.fs import lfs

# Import from itools.handlers
from base import Handler
from registry import register_handler_class



class File(Handler):
    """This is the base handler class for any file handler. It is also used
    as the default handler class for any file resource that has not a more
    specific handler.

    The variables 'timestamp' and 'dirty' define the state of the file
    handler:

      +--------------------------------------+
      | timestamp/dirty => means...          |
      +--------------------------------------+
      | None/None => not loaded (yet)        |
      | None/<dt> => new, or moved           |
      | <dt>/None => loaded, but not changed |
      | <dt>/<dt> => loaded, and changed     |
      +--------------------------------------+

    """

    # By default handlers are not loaded
    # XXX We should remove timestamp variable
    timestamp = None
    dirty = None
    loaded = False


    def __init__(self, key=None, string=None, database=None, **kw):
        if database is not None:
            self.database = database
        else:
            try:
                from database import ro_database
                self.database = ro_database
            except:
                print('Cannot attach this handler to a database')
                with open(key, 'r') as f:
                    string = f.read()
        if key is None:
            self.reset()
            self.dirty = datetime.now()
            if string is not None:
                # A handler from a byte string
                self.load_state_from_string(string)
            else:
                # A handler from some input data
                self.new(**kw)
        else:
            self.key = self.database.normalize_key(key)


    def reset(self):
        pass


    def new(self, data=''):
        self.data = data


    def __getattr__(self, name):
        # Not attached to a key or already loaded (should be correctly
        # initialized)
        if self.key is None or self.timestamp is not None:
            message = "'%s' object has no attribute '%s'"
            raise AttributeError, message % (self.__class__.__name__, name)

        # Load and try again
        self.load_state()
        return getattr(self, name)


    #########################################################################
    # Load / Save
    #########################################################################
    def _load_state_from_file(self, file):
        """Method to be overriden by sub-classes."""
        self.data = file.read()


    def load_state(self):
        data = self.database.get_handler_data(self.key)
        self.reset()
        try:
            self.load_state_from_string(data)
        except Exception as e:
            # Update message to add the problematic file
            message = '{0} on "{1}"'.format(e.message, self.key)
            self._clean_state()
            raise type(e), type(e)(message), exc_info()[2]
        self.timestamp = None
        self.dirty = None


    def load_state_from_uri(self, uri):
        file = lfs.open(uri)
        try:
            self.load_state_from_file(file)
        finally:
            file.close()


    def load_state_from_file(self, file):
        self.set_changed()
        self.reset()
        try:
            self._load_state_from_file(file)
        except Exception:
            self._clean_state()
            raise
        self.loaded = True


    def load_state_from_string(self, string):
        file = StringIO(string)
        self.load_state_from_file(file)


    def save_state(self):
        if not self.dirty:
            return
        # Save
        self.save_state_to(self.key)
        # Update timestamp/dirty
        self.timestamp = None
        self.dirty = None


    def save_state_to(self, key):
        fs = self.database.fs if self.database else lfs
        # If there is an empty folder in the given key, remove it
        if fs.is_folder(key) and not fs.get_names(key):
            fs.remove(key)

        # Save the file
        if not fs.exists(key):
            file = fs.make_file(key)
        else:
            file = fs.open(key, 'w')
        try:
            self.save_state_to_file(file)
        finally:
            file.close()


    def save_state_to_file(self, file):
        # We call "to_str" so this method will be good for sub-classes
        data = self.to_str()
        # Write and truncate (calls to "_save_state" must be done with the
        # pointer pointing to the beginning)
        file.write(data)
        file.truncate(file.tell())


    clone_exclude = frozenset(['database', 'key', 'timestamp', 'dirty'])
    def clone(self, cls=None):
        # Define the class to build
        if cls is None:
            cls = self.__class__
        elif not issubclass(cls, self.__class__):
            msg = 'the given class must be a subclass of the object'
            raise ValueError, msg

        # Load first, if needed
        if self.dirty is None:
            if self.key is not None and self.timestamp is None:
                self.load_state()

        # Copy the state
        copy = object.__new__(cls)
        copy.reset()
        for name in self.__dict__:
            if name not in cls.clone_exclude:
                value = getattr(self, name)
                value = deepcopy(value)
                setattr(copy, name, value)
        copy.dirty = datetime.now()
        return copy


    def set_changed(self):
        # Set as changed
        key = self.key
        # Invalid handler
        if key is None and self.dirty is None:
            raise RuntimeError, 'cannot change an orphaned file handler'
        # Ignore if not already loaded for the first time
        if not self.loaded:
            return
        # Set as dirty
        self.dirty = datetime.now()
        # Free handler (not attached to a database)
        database = self.database
        if database is None:
            return
        # Attached
        database.touch_handler(key, self)


    def _clean_state(self):
        names = [ x for x in self.__dict__ if x not in ('database', 'key') ]
        for name in names:
            delattr(self, name)


    def abort_changes(self):
        # Not attached to a key or not changed
        if self.key is None or self.dirty is None:
            return
        # Abort
        self._clean_state()


    #########################################################################
    # API
    #########################################################################
    def get_mtime(self):
        """Returns the last modification time.
        """
        # Modified or new handler
        if self.dirty is not None:
            return self.dirty

        # Loaded but not modified
        if self.timestamp is not None:
            return self.timestamp

        # Not yet loaded, check the FS
        return self.database.get_handler_mtime(self.key)


    def to_str(self):
        return self.data


    def set_data(self, data):
        self.set_changed()
        self.data = data


    def to_text(self):
        raise NotImplementedError


    def is_empty(self):
        raise NotImplementedError



register_handler_class(File)
