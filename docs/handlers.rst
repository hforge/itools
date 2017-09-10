:mod:`itools.handlers` -- Handlers
**********************************

.. module:: itools.handlers
   :synopsis: The handlers

.. index::
   single: Handlers

.. contents::


By the word *handler* we mean a *file handler*, this is to say an object that
allows to handle a file: inspect the data it contains, and change it.

The :mod:`itools.handlers` package relies on the :mod:`itools` *Virtual File
System*  (see :mod:`itools.fs`) and the database object. This means that we
can handle remote files, for example we can do this::

    >>> from itools.handlers import ro_database
    >>> from itools.html import HTMLFile
    >>> page = ro_database.get_handler('http://example.com/', HTMLFile)

The database system offers *lazy load*, *caching* and *atomic transactions*.


File Handlers
=============

The :mod:`itools` package includes handlers for many file formats, like XML,
HTML or CSV. Each one is able to parse and load the content of the file into
an appropriate data structure; for example a CSV handler will store the data
as a table: a list of rows, where each row is a list of values. Each handler
class provides a distinct API to inspect and manipulate this data structure.

When there is not a handler class available that understands the file format
at hand, we can always use the basic :class:`File` class, that offers access
to the file's content as a raw byte string::

    >>> from itools.handlers import File
    >>>
    >>> file = ro_database.get_handler('itools.pdf', File)
    >>> print file.key
    file:///home/jdavid/sandboxes/hforge-docs/itools.pdf

The instance variable :attr:`key` is the unique identifier where the file
handler is attached to on the file system. The default file system is a virtual
file system (fs) that supports various storage methods so we use URIs.

To inspect its data we can type::

    >>> print type(file.data)
    <type 'str'>
    >>> print len(file.data)
    994739

The API to access and change the data of a basic file handler is quite simple:

.. class:: File

  .. method:: to_str()

        Returns the content of the handler (a byte string) [#handlers-rq1]_.

  .. method:: set_data(data)

        Changes the content of the handler to the given byte string.

The :class:`File` class is the base class for all file handlers. The following
figure shows a subset of the handler classes included in :mod:`itools`.

.. figure:: figures/handlers.*
    :align: center

    Some file handler classes included in :mod:`itools`.


Text Files
----------

When the file we want to work with is a text file, we can use the
:class:`TextFile` handler class. This one represents the file's content as a
text string::

    >>> from itools.handlers import TextFile
    >>>
    >>> file = ro_database.get_handler('itools.tex', TextFile)
    >>> print type(file.data)
    <type 'unicode'>
    >>> print file.data[:40]
    \documentclass{book}

    \usepackage{color}

The public API is much similar to the base :class:`File` handler's API:

.. class:: TextFile

  .. method:: to_str(encoding='utf-8')

        Returns a byte string with the content of the handler, using the given
        encoding (by default *UTF-8*).

  .. method:: set_data(data)

        Changes the content of the handler to the given text string.

Here the method :meth:`set_data` expects a text string instead of a byte
string. And the method :meth:`to_str` accepts an optional parameter to define
the encoding used to serialize the handler's content.


Configuration Files
-------------------

While not a standard file format, the format supported by the
:class:`ConfigFile` class can be used for example to manage some configuration
files found in Unix systems.

It is also useful to study this handler class as an example of a file handler
with some structure. This is an excerpt of the :file:`setup.conf` file from
the :mod:`itools` package::

    # The name of the package
    name = itools

    # The author details
    author_name = "J. David Ibáñez"
    author_email = jdavid@itaapy.com

    # The license
    license = "GNU General Public License (GPL)"

We have comments and variables::

    >>> from itools.handlers import ConfigFile
    >>>
    >>> config = ro_database.get_handler('setup.conf', ConfigFile)
    >>> print config.get_value('author_name')
    J. David Ibáñez

The code above shows how to get the value of a variable. Follows an excerpt
of the public API specific to the :class:`ConfigFile` class:

.. class:: ConfigFile

  .. method::set_value(name, value, comment=None)

        Sets the variable with the given name to the given value. If a comment
        is given, attach it to the variable.

  .. method:: get_value(name, type=None, default=None)

        Returns the value of the variable with the given name. The value
        returned will be a byte string, unless the *type* parameter is passed.

        If the *type* parameter is passed, the value will be deserialized
        using that type.

  .. method:: has_value(name)

        Returns :obj:`True` if there is a variable with the given name,
        :obj:`False` otherwise.

  .. method:: get_comment(name)

        Returns the comment associated to the given variable.


Loading
-------

File handlers support lazy load, what means that the handler is only loaded
when we try to retrieve its data::

    >>> from itools.handlers import TextFile, ro_database
    >>>
    >>> file = ro_database.get_handler('itools.tex', TextFile)
    >>> print file.__dict__.keys()
    ['key', 'database']
    >>>
    >>> print len(file.data)
    994739
    >>> print file.__dict__.keys()
    ['encoding', 'timestamp', 'database', 'dirty', 'key', 'data']

Here two new instance variables show up:

.. attribute:: File.timestamp

      The modification time of the file, the last time the handler and the
      file were synchronised through the :meth:`load` or :meth:`save`
      operations.

.. attribute:: File.dirty

      A :class:`datetime` value, the last time the state of the handler has
      changed, or None while the handler and the file are synchronised.

These variables are *read-only*: do not change them by hand! The
:attr:`dirty` variable will be studied in the section :ref:`handlers-saving`.

The :attr:`timestamp` variable allows to know whether the file resource was
changed after the file handler was loaded, what means that our file handler is
*out-of-date*::

    # Create a file
    $ echo "Hello" > test.txt
    # Start the Python interpreter
    $ python
    ...
    >>> from itools.handlers import TextFile, RWDatabase
    >>> rw_database = RWDatabase()
    >>>
    >>> test = rw_database.get_handler('test.txt', TextFile)
    >>> test.load_state()
    >>> print test.timestamp
    2007-11-19 20:14:57


Programming Interface
^^^^^^^^^^^^^^^^^^^^^

This is the full collection of load related methods:

.. method:: File.load_state()

      (Re)loads the handler's state from its associated file resource. The
      timestamp is updated.

.. method:: File.load_state_from_string(string)

      Updates the handler's state with the contents of the given byte
      string.

.. method:: File.load_state_from_file(file)

      Updates the handler's state with the contents of the given open file.

.. method:: File.load_state_from(key)

      Updates the handler's state with the contents of the file resource
      identified by the given key reference. The key is specific to the file
      system used by the handler (absolute URI, absolute path...).


Note that the last three methods actually modify the handler's state with a
content that is alien to the associated file resource.  This does not change
the timestamp, but sets the :attr:`dirty` variable to the current datetime,
meaning that the handler's state has changed and is *newer* than the
associated file resource.

This brings us to the next section :ref:`handlers-saving`.


.. _handlers-saving:

Saving
------

We continue with our test file above, now we are going to change the handler's
state::

    >>> print test.dirty
    None
    >>> test.set_data(u'The king is naked.\n')
    >>> print test.dirty
    2008-03-27 14:25:54.080461
    >>> print test.to_str()
    The king is naked.

    # From another console...
    $ cat test.txt
    Bye

To know whether the handler has been modified to become *newer* than the
associated file resource we just check the :attr:`dirty` variable. To save
the changes made to the associated file resource we use :meth:`save_state`::

    >>> test.save_state()
    >>> print test.dirty
    None
    # From another console...
    $ cat test.txt
    The king is naked.


Programming Interface
^^^^^^^^^^^^^^^^^^^^^

This is the programming interface for save operations:

.. attribute:: File.dirty

      Read-only datetime variable tells when the handler has been modified
      or None.

.. method:: File.save_state()

      Saves the handler's state to its associated file. So the handler and
      its file resource are synchronized again.

.. method:: File.save_state_to(key)

      Saves the handler's state to the file resource identified by the given
      key.

.. method:: File.save_state_to_file(file)

  Saves the handler's state to the given open file.

Note that the last two methods do not set the :attr:`dirty` variable to
:obj:`None`, since the handler's state has not been saved to its associated
file resource, but to some other file.


The Registry
------------

So far we have explicitly chosen which handler class we want to use to work
with some file. It is also possible to let :mod:`itools.handlers` to choose
the better handler class available for us, with the :meth:`get_handler`
function::

    >>> from itools.handlers import ro_database
    >>>
    >>> ro_database.get_handler('itools.pdf')
    <itools.handlers.file.File object at 0x2b65c5f01910>

Here the :meth:`get_handler` method did not found a specific handler class
for the PDF document, so it chose the basic :class:`File` class. But we can
do it better::

    >>> import itools.pdf
    >>>
    >>> ro_database.get_handler('itools.pdf')
    <itools.pdf.pdf.PDFFile object at 0xf5d450>

The :mod:`itools.handlers` package provides the basic infrastructure, and a
few handler classes. For most specific handler classes the right package must
be imported, like :mod:`itools.pdf`, :mod:`itools.xml` or :mod:`itools.odf`.


How it works
^^^^^^^^^^^^

To find out the best available handler class for a file :mod:`itools` uses the
file's mimetype [#handlers-mimetype]_, and keeps a registry from mimetype to
handler class.

The programming interface of the registry is:

.. function:: register_handler_class(handler_class)

    Registers the given handler class into the registry. The class must define
    the variable :attr:`class_mimetypes`, which must be a list with the
    mimetypes the handler class is able to manage.

To illustrate the register interface, this is how a handler class looks
like::

    from itools.handlers import File
    from itools.handlers import register_handler_class

    class PDFFile(File):
        class_mimetypes = ['application/pdf']

    register_handler_class(PDFFile)


New Handlers
^^^^^^^^^^^^

So far we have seen how to load a file handler for a file resource that
already exists, in the local filesystem or somewhere else. But sometimes we
want to create new files, or just to work with temporary files that will never
be stored anywhere::

    >>> from itools.html import HTMLFile
    >>>
    >>> file = HTMLFile()
    >>> print file.key
    None

Note that we have created the handler calling to the handler class, but
without passing any arguments. This creates a new handler that is not
associated to any resource, the value of :attr:`handler.key` is :obj:`None`.
The general prototype for a handler class is:

*<handler_class>(key=None, \*\*kw)*

    If a key reference is given, build a handler instance for it.

    If a key reference is not given, create a new handler that is not
    associated to any resource. Named parameters may be passed, they will be
    used to initialize the handler's state (which named parameters are
    accepted depends on the handler class).

For instance, we are going to build an HTML handler with some title::

    >>> file = HTMLFile(title='Hello World')
    >>> print file.to_str()
    <html>
      <head>
        <meta http-equiv="Content-Type" content="text/html; ...
        <title>Hello World</title>
      </head>
      <body></body>
    </html>

Those specific keyword parameters are different for each handler class.


State initialization
^^^^^^^^^^^^^^^^^^^^

When writing a new handler class the method :meth:`new` must be implemented,
it initializes the handler's state for handlers not associated to a file
resource. For example, the handler class for a PDF file may look like::

    from itools.handlers import File

    class PDFFile(File):
        class_mimetypes = ['application/pdf']

        def new(self):
            self.data = '%PDF-1.4\n'

Note that the example above only intent is to show the prototype of the
:meth:`new` method, don't expect it to work properly (I don't really know the
PDF file format).


.. _handlers-database:

The Database System
===================

In this section we are going to see the database system for file handlers,
which adds some nice features: *caching* and *transactions*.

Itools provides a default read only database::

    >>> from itools.handlers import ro_database as db
    >>>
    >>> file = db.get_handler('itools.pdf')
    >>> print file.database
    <itools.handlers.database.RODatabase object at 0x2b138fde6910>


Caching
-------

The database supports caching. Every time we call :meth:`get_handler`, we get
always the same file handler, because it is stored in the cache::

    >>> db.get_handler('itools.pdf')
    <itools.handlers.file.File object at 0x2b1392fdd510>
    >>> db.get_handler('itools.pdf')
    <itools.handlers.file.File object at 0x2b1392fdd510>

We can inspect the cache::

    >>> for key in db.cache:
    ...     print key
    ...     print db.cache[key]
    ...     print
    ...
    file:///home/jdavid/sandboxes/hforge-docs/itools.pdf
    <itools.handlers.file.File object at 0x2b1392fdd510>

The cache is just a mapping from key to file handler. Because the database
uses fs file system by default, we can keep in the database remote handlers.


Programming Interface
---------------------

This is the programming interface provided by the database:

.. class:: RWDatabase


  .. method:: get_handler(self, key, cls=None)

        Returns the handler for the given key reference.  If there is not any
        handler at the given key, raises the :exc:`LookupError` exception.

        By default it will figure out the best handler class to use.  The
        parameter *cls* allows to explicitly choose the handler class to use.

  .. method:: has_handler(key)

        Returns :obj:`True` if there is a handler at the given key reference,
        :obj:`False` if there is not.

  .. method:: get_handler_names(key)

        If the given key reference identifies a folder (instead of a file),
        this method will return a list with all the names of the resources
        within that folder.

  .. method:: get_handlers(key)

        If the given key reference identifies a folder, this method will
        return all the handlers within that folder.  This method is a
        generator.

  .. method:: set_handler(key, handler)

        If there is not a resource at the given key reference, adds the given
        handler to it.

        This method is meant to be used to add new files::

            >>>
            # Create a new file
            >>> file = TextFile()
            >>> print file.database
            None
            >>> print file.key
            None
            # Add the new file
            >>> db.set_handler('/tmp/test.txt', file)
            >>> print file.database
            <itools.handlers.database.Database object at 0x2b1392fdd590>
            >>> print file.key
            file:///tmp/test.txt

        The file handler is attached to the database at the given key
        reference.

  .. method:: del_handler(key)

        Removes the handler at the given key reference. If it is a folder
        removes all its content recursively.

  .. method:: copy_handler(source, target)

        Copies the handler from the given *source* key reference to the given
        *target* key reference.  If it is a folder the all its content is
        copied recursively.

  .. method:: move_handler(source, target)

        Moves the handler from the given *source* key reference to the given
        *target* key reference. If it is a folder the all its content is
        moved.

All modification methods do the changes in-memory. Changes can be later
aborted or saved. This makes up transaction. Section
:ref:`handlers-transactions` explains the details.


Folders
-------

All the :mod:`itools.handlers` package is about files, not folders. Files are
the things that contain data, folders are there just to simplify our lives.

When the :meth:`get_handler` method is called for a folder resource, a folder
handler is returned::

    >>> db.get_handler('/tmp')
    <itools.handlers.folder.Folder object at 0x2b1392fdd690>
    >>> db.get_handler('/tmp')
    <itools.handlers.folder.Folder object at 0x2b1392fdd5d0>

First difference with file handlers: folders are not cached. Every time we ask
for a folder resource, a different handler will be returned. Since folders
don't keep any data, there is no point to cache them. And the lack of state
means they do not have the :attr:`timestamp` and :attr:`dirty` variables
either.

Folders are just a key in a database::

    >>> tmp = db.get_handler('/tmp')
    >>> print tmp.database
    <itools.handlers.database.Database object at 0x2afa17af4910>
    >>> print tmp.key
    file:///tmp

The folder's API is basically the same of the database's API we have seen in
Section :ref:`handlers-database`. The difference is that with the database
API relative key references are resolved against the *current working
directory*; while with folders they are resolved against the folder's key
reference.

So these lines are equivalent::

    >>>
    # Database: key references relative to working directory
    >>> print db.has_handler('/tmp/test.txt')
    False
    # Folder: key references relative to folder's key
    >>> print tmp.has_handler('test.txt')
    False


.. _handlers-transactions:

Transactions
------------

As explained above changes done to the database are kept in memory, so they can
later be aborted or saved. This makes-up a transaction::

    >>> from itools.handlers import TextFile
    >>>
    # Create a new file
    >>> test = TextFile()
    >>> test.set_data(u'hello world\n')
    # Add the new file
    >>> tmp.set_handler('test.txt', test)
    >>> print tmp.has_handler('test.txt')
    True
    # Copy the file
    >>> tmp.copy_handler('test.txt', 'test2.txt')
    >>> copy = tmp.get_handler('test2.txt')
    # Modify the first file
    >>> test.set_data(u'First post\n')
    # Check the files content
    >>> print test.data
    First post

    >>> print copy.data
    hello world

If you check the file system, you will see there is not any file named
:file:`test.txt` or :file:`test2.txt` in the temporary folder. Reached this
point you can either abort the changes::

    >>> db.abort_changes()
    >>> print tmp.has_handler('test.txt')
    False
    >>> print tmp.has_handler('test2.txt')
    False

Or save them::

    >>> db.save_changes()
    >>> print tmp.has_handler('test.txt')
    True
    >>> print tmp.has_handler('test2.txt')
    True

The programming interface for transactions is pretty simple:

.. method:: File.abort_changes()

      Abort the transaction.

.. method:: File.save_changes()

      Save the transaction.


A *bullet-proof* Database
=========================

The database system seen before is simple and nice, but not very robust. For
example, if there is a power shut-down while the :meth:`save_changes` method
is running, the transaction will be half saved, and our filesystem database
will be left in an inconsistent state.

To address this issue, for applications that require the transactions to be
atomic whatever happens, the :mod:`itools.database` package includes the
:class:`GitDatabase` class. See func:`make_git_database` to start with.

An even safer approach is to not allow any modification at all. RODatabase
and ROGitDatabase follow this approach.


Changing Filesystems
====================

If you need more performance, You can limit yourself to the local filesystem
and benefit from faster access.

Itools brings a :class:`lfs` object limited to the local filesystem but
faster than :class:`vfs`. The GitDatabase uses it because Git itself could
only commit files physically written in its repository.

To create a database that benefits from it is straightforward::

    >>> from itools.fs import lfs
    >>> from itools.handlers import RWDatabase
    >>>
    >>> database = RWDatabase(fs=lfs)

Everything else you learnt about databases apply, except of course URIs are
not supported anymore::

    >>> test = database.get_handler('/tmp/test.txt')
    >>> test.key
    >>> '/tmp/test.txt'
    >>> database.get_handler('http://example.com/')
    Traceback (most recent call last):
    [...]
    LookupError: the resource "/home/jdavid/sandboxes/hforge-docs/http:/example.com" does not exist


.. _handlers-example:

Example: Write your own handler class
=====================================

We have seen how to use the handlers classes available, now we are going to
learn how create our own handler classes.

The explanation will be driven by an example: we are going to write a task
tracker. The code can be found in the directory :file:`examples/handlers`.


Functional scope
----------------

Lets start by defining the functional scope of our task tracker. It is going
to be very simple, it will be a collection of tasks where every task will have
three fields:

* :attr:`title`, a short sentence describing the task.
* :attr:`description`, a longer description detailing the task.
* :attr:`state`, it may be *open* (if the task has not been finished yet), or
  *closed* (if the task has been finished).

The task tracker will provide an API to manipulate the collection of tasks:
create a new task, see either the open or the closed tasks, and close a task.


The file format
---------------

Now that we know what we want to do, we have to decide where and how the
information will be stored.

We will keep the tasks in a single text file, with a format somewhat similar
to the one used by the standards *vCard* and *iCal*, for example:

.. code-block:: none

    title:Re-write the chapter about writing handler classes.
    description:A new chapter that explains how to write file
     handler classes must be written, it should go immediately
     after the chapter that introduces file handlers.
    state:closed

    title:Finish the chapter about folder handlers.
    description:The chapter about folder handlers needs much
     more work.  For example the skeleton of folder handlers
     must be explained.
    state:open

Each task is separated from the next one by a blank line. Every field starts
by the field name followed by the field value, both separated by a colon. If a
field value is very long it can be written in multiple lines, where the second
and next lines start by a space.


De-serialization
----------------

The first draft of our handler class will be able to load (de-serialize) the
resource into a data structure on memory.
::

    from itools.handlers import TextFile


    class Task(object):
        def __init__(self, title, description, state='open'):
            self.title = title
            self.description = description
            self.state = state


    class TaskTracker(TextFile):

        def _load_state_from_file(self, file):
            # Split the raw data in lines.
            lines = file.readlines()
            # Append None to signal the end of the data.
            lines.append(None)

            # Initialize the internal data structure
            self.tasks = []
            # Parse and load the tasks
            fields = {}
            for line in lines:
                if line is None or line.strip() == '':
                    if fields:
                        task = Task(fields['title'],
                                    fields['description'],
                                    fields['state'])
                        self.tasks.append(task)
                        fields = {}
                else:
                    if line.startswith(' '):
                        fields[field_name] += line.rstrip()
                    else:
                        field_name, field_value = line.split(':', 1)
                        fields[field_name] = field_value.rstrip()

First, our handler class :class:`TaskTracker` inherits from the handler class
:class:`TextFile`, because it is intended to manage a text file.

The method :meth:`_load_state_from_file` is the one to implement to parse and
load a new file format. It is responsible to de-serialize the resource and
build a data structure on memory that represents it.

Lets try the code::

    >>> from pprint import pprint
    >>> from textwrap import fill
    >>> from tracker import TaskTracker
    >>> from itools.handlers import ro_database
    >>>
    >>> task_tracker = ro_database.get_handler('itools.tt')
    >>>
    >>> pprint(task_tracker.tasks)
    [<tracker.Task object at 0xb7aebd4c>,
     <tracker.Task object at 0xb7aebe6c>]
    >>>
    >>> task = task_tracker.tasks[0]
    >>> print task.title
    Re-write the chapter about writing handler classes.

    >>> print fill(task.description, width=60)
    A new chapter that explains how to write file handler
    classes must be written, it should go immediately after the
    chapter that introduces file handlers.
    >>> print task.state
    closed


Serialization
-------------

Now we are going to write the other half, the serialization process, just
adding the :meth:`to_str` method to the :class:`TaskTracker` class::

        def to_str(self, encoding='utf-8'):
            lines = []
            for task in self.tasks:
                lines.append('title:%s' % task.title)
                description = 'description:%s' % task.description
                description = wrap(description)
                lines.append(description[0])
                for line in description[1:]:
                    lines.append(' %s' % line)
                lines.append('state:%s' % task.state)
                lines.append('')
            return '\n'.join(lines)

Lets try our new code::

    >>> print task_tracker.to_str()
    title:Re-write the chapter about writing handler classes.
    description:A new chapter that explains how to write file handler
     classes must be written, it should go immediately after the chapter
     that introduces file handlers.
    state:closed

    title:Finish the chapter about folder handlers.
    description:The chapter about folder handlers needs much more work.
     For example the skeleton of folder handlers must be explained.
    state:open


The API
-------

Now it is time to write the API to manage the tasks, here is an excerpt::

    def add_task(self, title, description):
        task = Task(title, description)
        self.tasks.append(task)


    def show_open_tasks(self):
        for id, task in enumerate(self.tasks):
            if task.state == 'open':
                print 'Task #%d: %s' % (id, task.title)
                print
                print fill(task.description)
                print
                print


    def close_task(self, id):
        task = self.tasks[id]
        task.state = u'closed'

The first method, :meth:`add_task` creates a new task, whose state will be
*open*. The method :meth:`show_open_tasks` prints the list of open tasks with
a human readable format (we could write a method that returns HTML instead, to
use our task tracker on the web). Finally, the method :meth:`close_task`
closes the task.


Init new handlers
-----------------

To illustrate the :meth:`new` method we are going to initialize the handler
with a dummy task::

    def new(self):
        self.tasks = []
        task = Task('Read the docs!',
            'Read the itools documentation, it is so gooood.',
            'open')
        self.tasks.append(task)

To exercise the whole thing we are going to create a new task tracker, we will
close the first task, add a new one, and look at what we have.
::

    >>> from tracker import TaskTracker
    >>>
    >>> task_tracker = TaskTracker()
    >>> task_tracker.show_open_tasks()
    Task #0: Read the docs!

    Read the itools documentation, it is so gooood.


    >>> task_tracker.close_task(0)
    >>> task_tracker.add_task('Join itools!',
    ...   'Subscribe to the itools mailing list.')
    >>> task_tracker.show_open_tasks()
    Task #1: Join itools!

    Subscribe to the itools mailing list.

Now, don't forget to save the task tracker in the file system, so you can come
back to it later::

    >>> from itools.handlers import RWDatabase
    >>>
    >>> db = RWDatabase()
    >>> db.set_handler('/tmp/test_tracker.tt', task_tracker)
    >>> db.save_changes()


Register
--------

However::

    >>> from itools.handlers import ro_database
    >>>
    >>> task_tracker = ro_database.get_handler('/tmp/test_tracker.tt')
    >>> print task_tracker
    <itools.handlers.text.TextFile object at 0xb7c00f0c>

It would be nice if the code above worked. To achieve it we will associate the
new mimetype ``text/x-task-tracker`` to the file extension ``tt``, we will
tell our handler class is able to manage that mimetype with the variable class
:attr:`class_mimetypes`, and we will register our handler class to its
parent::

    from itools.core import add_type
    from itools.handlers import register_handler_class

    add_type('text/x-task-tracker', '.tt')

    class TaskTracker(TextFile):

        class_mimetypes = ['text/x-task-tracker']
        [...]


    register_handler_class(TaskTracker)

And *voilà*::

    >>> task_tracker = ro_database.get_handler('/tmp/test_tracker.tt')
    >>> print task_tracker
    <tracker.TaskTracker object at 0xb7af084c>

The full code can be found in :file:`examples/handlers/TaskTracker.py`.



.. rubric:: Footnotes


.. [#handlers-rq1]

      handlers must implement the :meth:`to_str` method, which serializes the
      handler's content to a byte string.  It is required for the correct
      working of the load/save API explained later.

.. [#handlers-mimetype]

      To find out the file's mimetype the :func:`vfs.get_mimetype` function is
      used, see :mod:`itools.vfs`.

