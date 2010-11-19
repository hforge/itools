:mod:`itools.fs` -- Virtual File System
***************************************

.. module:: itools.fs
   :synopsis: Virtual File System

.. index::
   single: VFS

.. contents::


A *virtual file system* provides a file oriented interface for resources
accessed through different protocols, may they be stored in the local file
system, in a remote web or ftp server, or somewhere else.

The package :mod:`itools.fs` provides such an interface. It is based on the
couple gio/gvfs from the gnome project.


Usage
=====

`itools.fs` is organised into 2 modules:

- `itools.fs.vfs`: The real virtual file system.
- `itools.fs.lfs`: A specific implementation for local use only.

The programming interface of :mod:`itools.fs.vfs` or `itools.fs.lfs` appears as
a set of global functions. To be used this way::

    >>> from itools.fs import vfs
    >>> import itools.http
    >>>
    >>> uri = 'http://example.com/'
    >>> if vfs.exists(uri):
    ...     file = vfs.open(uri)
    ...     print file.read()
    ...     file.close()

A resource is identified by a URI. That is what most functions in the
programming interface expect as parameters: URIs; either as byte strings (like
in the example above), or instances of the *URI Reference* class (see
:mod:`itools.uri` for the details).

If the URI given is relative, it will be resolved relative to the *current
working directory*.


Files
-----

The function :func:`vfs.open`, seen in the example above, returns an object
that offers the same programming interface of Python files.

We are not going to explain what this programming interface is, just check
the Python's documentation.


Folders
-------

From the point of view of :mod:`itools.fs` a folder is an object which offers
exactly the same programming interface of :obj:`vfs`, but which resolves
relative URIs not to the current working directory, but to some URI.

For example::

    # Use the global API
    >>> for name in vfs.get_names('.'):
    ...     print name
    ...
    README
    gettext
    stl

    # Use the folder's API
    >>> folder = vfs.open('.')
    >>> for name in folder.get_names():
    ...     print name
    ...
    README
    gettext
    stl

As this example shows the folder's method :meth:`get_names` not even requires
to pass a URI. In this case the action affects the URI associated with the
folder.


Summary of the API
==================

Here we introduce the programming interface of :mod:`itools.fs.[lv]fs`, for the
details check the reference chapter.


Informational
-------------

.. function:: exists(reference)

.. function:: is_file(reference)

.. function:: is_folder(reference)

.. function:: can_read(reference)

.. function:: can_write(reference)

.. function:: get_ctime(reference)

.. function:: get_mtime(reference)

.. function:: get_atime(reference)

.. function:: get_mimetype(reference)

.. function:: get_size(reference)

.. function:: get_uri(reference)


Make and Open
^^^^^^^^^^^^^

.. function:: make_file(reference)

.. function:: make_folder(reference)

.. function:: open(reference, mode=None)

.. function:: mount_archive(reference)


Remove, Copy and Move
^^^^^^^^^^^^^^^^^^^^^

.. function:: remove(reference)

.. function:: copy(source, target)

.. function:: move(source, target)


Only for Folders
^^^^^^^^^^^^^^^^

.. function:: get_names(reference)

.. function:: traverse(reference)


