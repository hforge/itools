:mod:`itools.datatypes` Datatypes
*********************************

.. module:: itools.datatypes
   :synopsis: Datatypes

.. index::
   single: Datatypes

.. contents::


Information stored in a file or sent through a network appears as a chain of
bytes, but it represents high level information. For example we may want to
keep some basic data about a master piece book:

.. code-block:: xml

    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:title>100 años de soledad</dc:title>
      <dc:creator>Gabriel Garcia Marquez</dc:creator>
      <dc:date>1999-07-02</dc:date>
      <dc:language>es</dc:language>
    </metadata>

Above we have used the XML language to keep the title, author, date of
publication and language of our book; but we may prefer a different file
format:

.. code-block:: none

    BEGIN:RECORD
      TITLE:100 años de soledad
      CREATOR:Gabriel Garcia Marquez
      DATE:1999-07-02
      LANGUAGE:es
    END:RECORD

Independently of the format used, one thing is sure, we would like to load the
information with a type:

.. code-block:: none

    '100 años de soledad'    -(text)->  u'100 años de soledad'
    'Gabriel Garcia Marquez' -(text)->  u'Gabriel Garcia Marquez'
    '1999-07-02'             -(date)->  datetime.date(1999, 7, 2)
    'es'                     -(noop)->  'es'

This process is called *deserialization*. The opposite operation, which we are
also interested in, is called *serialization*: to transform a value to a chain
of bytes.

Other operations we may be interested include:

* To check whether a string value is correct; for example, to check whether
  the date respects the ISO 8601 standard.
* To provide a default value when a field is missing; for example we may
  assume the language is English if not specified otherwise.

The packages :mod:`itools.datatypes` and :mod:`itools.schema` provide an
infrastructure to do all this and more. What is useful not only to serialize
and deserialize files, but also for other purposes, like validating user input
data.


Datatypes
=========

In Python there are basic types like :class:`unicode`, :class:`integer` or
:class:`float`. And there are more complex types like dates.

The module :mod:`itools.datatypes` provides an infrastructure orthogonal to
the Python types. The basic service provided by this infrastructure is the
deserialization and serialization of values; which is implemented as the
couple of class methods :meth:`decode` and :meth:`encode`, for example::

    >>> from itools.datatypes import DateTime
    >>> datetime = DateTime.decode('2005-05-02T16:47')
    >>> datetime
    datetime.datetime(2005, 5, 2, 16, 47)
    >>> DateTime.encode(datetime)
    '2005-05-02T16:47:00'

This approach, to implement the serialization/deserialization code separate
from the type itself, allows to avoid sub-classing built-in types, what has a
performance impact.

This also illustrates one of the software principles behind the itools coding,
different programming aspects should be clearly distinct in the implementation
and programming interface.


Out of the box
==============

Out-of-the-box :mod:`itools.datatypes` provides support for the following
types:


.. class:: Integer

    An integer number is serialized using ASCII characters. This means a call
    to :meth:`decode(x)` is equivalent to :func:`int(x)`, and
    :meth:`Integer.encode(x)` does the same than :func:`str(x)`.

.. class:: Unicode

    Text strings are serialized using the UTF-8 encoding (by default).

.. class:: String

    A byte string does not needs to be serialized or deserialized, the output
    is always equal to the input.

.. class:: Boolean

     Boolean values are encoded with the "0" character for the *false* value
     and with the "1" character for the *true* value.

.. class:: Date

    Dates are encoded following the ISO 8601 standard [#datatypes-date]_:
    *YYYY-MM-DD*.

.. class:: DateTime

    Date and time is encoded with the pattern: *YYYY-MM-DDThh:mm:ss*.

.. class:: URI

    The URI decoder will build and return one of the URI reference objects
    defined in the :mod:`itools.uri` package, usually it will be an instance
    of the class :class:`itools.uri.generic.Reference`.

.. class:: QName

    An XML qualified name has two parts, the prefix and the local name, so
    our decoder will return a tuple with these two elements::

        >>> from itools.datatypes import QName
        >>> QName.decode('dc:title')
        ('dc', 'title')
        >>> QName.decode('href')
        (None, 'href')

    The encoder expects a two element tuple::

        >>> QName.encode(('dc', 'title'))
        'dc:title'
        >>> QName.encode((None, 'href'))
        'href'

.. class:: itools.fs.FileName

    Usually filenames include extensions to indicate the file type, and
    sometimes other information like the language. The filename decoder will
    parse a filename and return a tuple where the first element is the
    filename, the second element is the file type, and the last element is the
    language. For example::

        >>> from itools.fs import FileName
        >>> FileName.decode('index.html.en')
        ('index', 'html', 'en')
        >>> FileName.decode('index.html')
        ('index', 'html', None)
        >>> FileName.decode('index')
        ('index', None, None)

Defining new datatypes
======================

There are two ways to define a new datatype: sub-classing and instantiating.


Sub-classing
------------

All datatypes inherit from the abstract class
:class:`~itools.datatypes.DataType`. To define a new datatype either subclass
directly from :class:`~itools.datatypes.DataType`, or from any other subclass
of it.

As an example we are going to define a datatype that loads mimetypes as
a two elements tuple::

  import mimetypes
  from itools.datatypes import DataType

  class MimeType(DataType):

      default = None

      @staticmethod
      def decode(data):
          return tuple(data.split('/'))

      @staticmethod
      def encode(value):
          return '%s/%s' % value

      @staticmethod
      def is_valid(data):
          return mimetypes.guess_extension(data) is not None

Two things to highlight:

* We have set the default value to :obj:`None`, though this is not really
  needed since the :class:`~itools.datatypes.DataType` class already defines
  this variable to :obj:`None`.

  Another good default value maybe *('application', 'octet-stream')*.

* We have added the method :meth:`is_valid`, which is not defined by any other
  datatype included in :mod:`itools`. This illustrates that the datatypes can
  be extended with whatever logic, which we could use later in the application
  code.


Instantiating
-------------

This is a more compact way to specialize a datatype, when the changes are
small. For example::

  from itools.datatypes import String

  WorkflowState = String(default='private')

Here we have defined a workflow state as an string, whose default value is
*private*.

Note that a shortcoming of this approach is that, unlike sub-classing, it is
not possible to instantiate a datatype that already is an instance.


.. rubric:: Footnotes

.. [#datatypes-date] http://www.iso.org/iso/en/prods-services/popstds/datesandtime.html
