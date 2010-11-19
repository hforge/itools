:mod:`itools.uri` -- Uniform Resource Identifiers
*************************************************

.. module:: itools.uri
   :synopsis: Uniform Resource Identifiers

.. index:: URI

.. contents::


Resources in the Internet are identified by URIs: *Uniform Resource
Identifiers*. The purpose of :mod:`itools.uri` is to provide a rich
programming interface to work with URIs.

We follow the standard as defined by **RFC2396**.


Usage
=====

The main function provided by :mod:`itools.uri` is :func:`get_reference`,
which expects a byte string and returns a :class:`Reference` object:

.. class:: Reference

.. function:: get_reference(reference)

Here there are a few examples::

    >>> from itools.uri import get_reference
    >>> r1 = get_reference('http://www.w3.org/TR/REC-xml/#sec-intro')
    >>> r2 = get_reference('mailto:jdavid@itaapy.com')
    >>> r3 = get_reference('http://www.ietf.org/rfc/rfc2616.txt')
    >>> r4 = get_reference('http://sf.net/cvs/?group_id=5470')
    >>> r5 = get_reference('news:comp.infosystems.www.servers.unix')


Structure of a URI
==================

The general structure of a URI is::

    uri = <scheme>:<scheme-specific-part>

Basically this means that there are different types of URIs, or to speak more
precisely, different *schemes*. So the actual structure of a URI depends on
its scheme.


The *mailto* scheme
-------------------

An example of a pretty particular scheme is *mailto*::

    >>> r2 = get_reference('mailto:jdavid@itaapy.com')
    >>> print r2
    mailto:jdavi@itaapy.com
    >>> r2
    <itools.uri.mailto.Mailto object at 0x867d53c>
    >>> print r2.scheme
    mailto
    >>> print r2.username
    jdavid
    >>> print r2.host
    itaapy.com

All URI objects have the *scheme* variable that identifies the scheme they
belong to. But the rest of the information that makes up a URI depends on that
scheme, so it may be different one from another.

For the *mailto* scheme this information are the variables :attr:`username`
and :attr:`host`.


Generic URIs
------------

However, most URI schemes (like *http*) have the same general structure, they
are called *Generic URIs*:

.. code-block:: none

    <scheme>://<authority><absolute path>?<query>#<fragment>

As it is easy to guess a generic URI has one variables for every URI
component: :attr:`scheme`, :attr:`authority`, :attr:`path`, :attr:`query` and
:attr:`fragment`. Follows a code snippet to illustrate this::

    >>> r1
    <itools.uri.generic.Reference object at 0x403ebc4c>
    >>> print r1
    http://www.w3.org/TR/REC-xml/#sec-intro
    >>> print r1.scheme
    http
    >>> print r1.authority
    www.w3.org
    >>> print r1.path
    /TR/REC-xml/
    >>> print r1.query
    {}
    >>> print r1.fragment
    sec-intro

Now we are going to quickly see each of these components.


The Scheme
^^^^^^^^^^

Identifies the type of URI. Typically it will define the method or protocol
used to reach the resource: HTTP, FTP, etc.


The Authority
^^^^^^^^^^^^^

Defines the server address (hostname and port) where the resource is. And
maybe the user information required to access the resource:

.. code-block::none

    authority = [<userinfo>@]<hostport>

Schemes like *file* don't have an authority.


Absolute path
^^^^^^^^^^^^^

Within the scope of the authority, the resources are organized in a tree
structure, so the path identifies the resource within the tree. It consists of
a sequence of segments:

.. code-block:: none

    absolute path = /<relative path>
    relative path = <segment>[/<relative path>]


Query
^^^^^

While the **RFC2396** does not define a structure for the *Query*, we have
chosen to interpret it as defined by the ``application/x-www-form-urlencoded``
mimetype [#uri-rfc2396]_, since it is most often used this way.


Fragment
^^^^^^^^

The fragment is an internal reference within the resource.


Relative references
===================

The examples we have seen so far talk about absolute URIs, but there are
relative URI references too. A relative reference is one that lacks, at least,
the scheme.  There are three types of relative references: network paths,
absolute paths, and relative paths:

* **Network paths** Network paths only lack the scheme, they start by a double
  slash and the authority, followed by the absolute path. They are rarely
  used.

  .. code-block:: none

        www.ietf.org/rfc/rfc2396.txt

* **Absolute paths** The absolute paths lack both the scheme and the
  authority. They start by a slash.

  .. code-block:: none

        /rfc/rfc2396.txt

* **Relative paths** Relative paths lack the first slash of absolute paths.
  They can start by the special segment "``.``", or by one or more "``..``".
  Examples are:

  .. code-block:: none

        rfc/rfc2396.txt
        ./rfc/rfc2396.txt
        ../rfc2616.txt


Resolving references
--------------------

The most common operation with relative references is to resolve them. That is
to say, to obtain (with the help of a base reference) the absolute reference
that identifies our resource. This is achieved with the :meth:`resolve`
method::

    >>> base = get_reference('http://www.ietf.org/rfc/rfc2615.txt')
    >>> print base.resolve('//www.ietf.org/rfc/rfc2396.txt')
    http://www.ietf.org/rfc/rfc2396.txt
    >>> print base.resolve('/rfc/rfc2396.txt')
    http://www.ietf.org/rfc/rfc2396.txt
    >>> print base.resolve('rfc2396.txt')
    http://www.ietf.org/rfc/rfc2396.txt


Paths
=====

One component that deserves special attention is the path. It is possible to
build and work with paths indepently from URI objects::

    >>> from itools.uri import Path
    >>>
    >>> path = Path('/a/b/c')
    >>> for name in path:
    ...     print name
    ...
    a
    b
    c

As this example shows paths are iterable. Also, paths may be absolute or
relative, and they can be resolved very much the same way as URI objects::

    >>> p2 = '../d/e'
    >>> print path.resolve(p2)
    /a/d/e


.. rubric:: Footnotes

.. [#uri-rfc2396] http://www.w3.org/TR/REC-html40/interact/forms.html#h-17.13.4.1

