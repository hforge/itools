The packaging system (ipkg)
###########################

.. index:: Packaging

.. contents::


Introduction
============

As most other Python packages, :mod:`itools` uses the standard *Python
Distribution Utilities* (a.k.a. :mod:`distutils`).  Above them :mod:`itools`
adds a thin layer to simplify the work of making up a new Python package.

This document describes this thin layer, and two related scripts from the
*isetup* family: :file:`ipkg-build.py` and :file:`ipkg-update-locale.py`.


Anatomy of an :mod:`itools` based package
=========================================

An :mod:`itools` based package has this structure:

.. code-block:: none

    __init__.py
    setup.py
    setup.conf
    locale/
    scripts/
    test/

The :file:`locale`, :file:`scripts` and :file:`test` folders are optional.
The :file:`locale` folder is only required if the package is going to be
multilingual (see :ref:`i18n` for the details).  The :file:`scripts` folder is
where we will put the scripts, if there are any.  The :file:`test` folder is
for the unit tests.

One difference with normal Python packages, is that :mod:`itools` based
packages have a more normalized structure.


The configuration file
======================

With :mod:`distutils` the :file:`setup.py` module defines the package.  We
believe that a Python module is not the most appropiate file format to define
a package.  For this purpose :mod:`itools` uses a configuration file, what
reduces the :file:`setup.py` module to a few lines of boilerplate:

:file:`setup.py`::

    # Import from itools
    from itools.pkg import setup

    if __name__ == '__main__':
        setup()


Example: :file:`mypkg`
----------------------

A minimal configuration file must at least define the package name.  But it is
recommended to add a few description fields:

:file:`setup.conf`::

    # The name of the package
    name = mypkg

    # Recommended metadata
    title = "This package is a test."
    url = http://www.example.com/
    author_name = "J. David Ibáñez"
    author_email = jdavid@itaapy.com
    license = "GNU General Public License (GPL)"


Options
-------

Here we list the options currently supported by the configuration file:

* ``name`` The package name is the only mandatory option.
* ``title`` A short summary (one line) describing the package.
* ``url`` The URL of the package, the home Web Site.
* ``author_name`` The full name of the main author.
* ``author_email`` The email address of the main author.
* ``license`` The name of the license.
* ``description`` A multi-line description of the package.
* ``packages`` The list of sub-packages, if any.
* ``scripts`` The list of scripts, if any.
* ``source_language`` The source language of the package, generally ``en`` for
  English.
* ``target_languages`` The list of human languages the package is translated
  to, other than the source language.


Limits
^^^^^^

It is true that as of today the configuration file does not allow to do
everything, for example there is no way to define extension modules (modules
written in C).  When a feature not supported by the configuration file is
required, we will need a more elaborate :file:`setup.py` module than the
boilerplate seen before.

The :mod:`itools` package itself is an example of a more complex package that
requires a more elaborate :file:`setup.py` module.


The version number
==================

Note that the version number is not an option of the configuration file. We
prefer to store it in the :file:`version.txt` file, for instance:

:file:`version.txt`:

.. code-block:: none

    1.0.2

The first advantage of this approach is the possibility to automatize the
generation of the version number with the help of external tools.  This is
what we do with *Git* [#packaging-git]_  (see :ref:`git`) and the
:file:`ipkg-build.py` script (see section :ref:`packaging-build`).

The second advantage is the possibility to export the version number with just
two lines of boilerplate in the init module:

:file:`__init__.py`::

    # Import from itools
    from itools.core import get_version

    __version__ = get_version()

This way we can easily know the version of an installed package::

    >>> import mypkg
    >>> print mypkg.__version__
    1.0.2


Git
===

*Git* is a *Source Code Management* tool. Unlike the most widely used CVS
[#packaging-cvs]_ , *Git* belongs to the new generation of distributed *SCMs*,
and is best known to be the tool used to manage the Linux [#packaging-kernel]_
source code.

As of today the :mod:`itools` packaging system relies heavily on *Git*.  This
means that our package must be managed by *Git*, if we want to use the
:mod:`itools` packaging facilities.

Following our example, so far we have three files with the content seen
before:

.. code-block:: none

    mypkg/
      __init__.py
      setup.py
      setup.conf

At this point we are going to initialize the *Git* archive:

.. code-block:: sh

    $ git init
    Initialized empty Git repository in .git/
    $ git add __init__.py setup.conf setup.py
    $ git commit -m "Initial commit."
    Created initial commit 41a1f72: Initial commit.
    2 files changed, 8 insertions(+), 0 deletions(-)
    create mode 100644 __init__.py
    create mode 100644 setup.conf
    create mode 100644 setup.py

It is not the purpose of this document to explain *Git*, for that we recommend
the :ref:`git`.  For the scope of this document this is all you need to know
about *Git*.


.. _packaging-build:

The build, install and release processes
========================================

With :mod:`itools` the procedure to install a package from the source
checkout, or to make a release are two lines.


Build & Install
---------------

.. code-block:: sh

    $ ipkg-build.py
    $ python setup.py install


Make a source release
---------------------

.. code-block:: sh

    $ ipkg-build.py
    $ python setup.py sdist


The :file:`ipkg-build.py` script
--------------------------------

The :file:`ipkg-build.py` script uses *Git* and the configuration file to
automatize a few tasks.  We can test it with our example:

.. code-block:: sh

    $ ipkg-build.py
    * Version: master-200712081934
    * Build MANIFEST file (list of files to install)


The version number
^^^^^^^^^^^^^^^^^^

First thing the :file:`ipkg-build.py` script does is to figure out the
version number, which is made up of two parts:

.. code-block:: none

    <branch or tag name>-<timestamp>

With *Git* the default branch name is *master*.  The timestamp is the date and
time of the last commit. This explains why the version number of the example
above is *master-200712081934*.

But if we are in a branch named ``1.0``, and we have a tag named ``1.0.2``,
the version number will be ``1.0.2-<timestamp>``. If it happens to be that the
tag points to the last commit, then the timestamp will be omitted, and the
version number will just be ``1.0.2``.

With this versioning scheme we will be able to produce releases numbered like
this:

.. code-block:: none

    1.0.0
    1.0.0-200712251143
    1.0.0-200712271622
    ...
    1.0.1
    1.0.1-200712281203
    ...
    1.0.2

As you may have guessed, this is the versioning scheme used by :mod:`itools`
and :mod:`itools` based packages like :mod:`ikaaro`.  The versions with a
timestamp are development snapshots not released to the public.  The versions
without the timestamp are public releases.


The :file:`MANIFEST` file
^^^^^^^^^^^^^^^^^^^^^^^^^

The last thing the :file:`ipkg-build` script does is to build the
:file:`MANIFEST` file: the list of files that make up the package. This list
is made up of:

* all files kept in the *Git* archive, this is to say, the source files;
* the automatically generated :file:`MANIFEST` and :file:`version.txt` files;
* the automatically generated files needed in a multilingual package (see
  :ref:`i18n`).


Multilingual packages
=====================

Now, say you want to offer a multilingual user interface, and you choose to
use :mod:`itools` to do the job (a wise decission).

The details on software internationalization and localization with
:mod:`itools` are explained on the library documentation available from the
:mod:`itools` web site, see in particular the chapter :ref:`i18n`.

Here we are going to explain the aspects related to packaging.


The source and target languages
-------------------------------

The first thing to do is to define the source and target languages in the
configuration file:

:file:`setup.conf`:

.. code-block:: none

    # Languages
    source_language = en
    target_languages = es fr

In this example the source language is English, and there are two target
languages, Spanish and French.


The :file:`ipkg-update-locale.py` script
----------------------------------------

Running the :file:`ipkg-update-locale.py` at this point will automatically
create the :file:`locale` folder, the POT template, and a PO file for each
language:

.. code-block:: sh

    $ ipkg-update-locale.py
    * Extract text strings from Python files..
    * Update PO template
    * Update PO files:
      en.po (new)
      es.po (new)
      fr.po (new)
    $ tree locale
    locale
    |-- en.po
    |-- es.po
    |-- fr.po
    `-- locale.pot

Since the PO files belong to the source, we should add them to the *Git*
archive every time we run the :file:`ipkg-update-locale.py` script:

.. code-block:: sh

    $ git add locale/locale.pot locale/*.po
    $ git commit -m "Update PO files."
    Created commit d79de97: Update PO files.
    ...


Building a multilinguage package
--------------------------------

At this point we must come back to the :file:`ipkg-build.py` script. If we
run it again, once the package has been internationalized, we will find out it
does a little more than before:

.. code-block:: sh

    $ ipkg-build.py
    * Version: master-200712101700
    * Compile message catalogs: en es fr
    * Build MANIFEST file (list of files to install)
    $ tree locale
    locale
    |-- en.mo
    |-- en.po
    |-- es.mo
    |-- es.po
    |-- fr.mo
    |-- fr.po
    `-- locale.pot

The :file:`ipkg-build.py` script has compiled the PO files to produce one
binary MO file per language. These binary files will be used at run time by
the internationalization logic to expose a multilingual interface to the user.


Tell *Git* to ignore non-source files
=====================================

This may be a good time to make a break in the exposition and explain how to
tell *Git* to ignore non-source files.

We have seen the :file:`ipkg-build.py` script produces a number of files
that do not belong to the source code, but that are required to make a new
relase. These files must not be tracked by *Git*. To tell *Git* to ignore the
non-source files we must create the :file:`.gitignore` file:

:file:`.gitignore`:

.. code-block:: none

    *.pyc
    version.txt
    MANIFEST
    locale/*.mo

The example above shows that "compiled" Python files must be ignored, as well
as the automatically generated :file:`version.txt` and :file:`MANIFEST` files,
and the binary language files. Now we should commit :file:`.gitignore`:

.. code-block:: sh

    $ git add .gitignore
    $ git commit -m "Tell Git to ignore non-source files."
    Created commit 6790c7c: Tell Git to ignore non-source files.
    1 files changed, 4 insertions(+), 0 deletions(-)
    create mode 100644 .gitignore


The release procedure
=====================

To summarize up everything seen in this document, this is the procedure to
make a public release of a multilingual package:

* Once the strings in the user interface are frozen, we must update the
  translations.  To do so we first extract the text strings from the source
  files with the help of the :file:`ipkg-update-locale.py` script, as seen
  before:

  .. code-block:: sh

      $ ipkg-update-locale.py
      * Extract text strings from Python files..
      * Extract text strings from XHTML files
      * Update PO template
      * Update PO files:
        en.po . done.
        es.po . done.
        fr.po . done.
      $ git add locale/locale.pot locale/*.po
      $ git commit -m "Update PO files."

* Now it is time for the human translators to update the translations for each
  target language.
* Once this is done we can tell the source is ready, so we make a new tag.
  For example, if we are in the ``1.0`` branch, we may want to make the
  release number ``1.0.2``:

  .. code-block:: sh

      $ git tag 1.0.2

* At last, we are ready to make the source release:

  .. code-block:: sh

      $ ipkg-build.py
      * Version: 1.0.2
      * Compile message catalogs: en es fr
      * Build MANIFEST file (list of files to install)
      $ python setup.py sdist
      ...


.. rubric:: Footnotes

.. [#packaging-git] http://git.or.cz

.. [#packaging-cvs] http://en.wikipedia.org/wiki/Concurrent_Versions_System

.. [#packaging-kernel] http://www.kernel.org/

