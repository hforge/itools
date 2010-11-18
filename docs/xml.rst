:mod:`itools.xml` eXtensible Markup Language (XML)
**************************************************

.. module:: itools.xml
   :synopsis: eXtensible Markup Language (XML)

.. index:: XML

.. contents::


The package :mod:`itools.xml` offers a programming interface to work with XML
files. Here we will explain the core elements of this API: the parser, the
namespaces, the doctypes and the file handler.

.. _xml-parser:

The parser
==========

The lowest-level layer offered by :mod:`itools.xml` is an event driven parser.
See this usage example::

    >>> from itools.xml import (XMLParser, START_ELEMENT,
    ...     END_ELEMENT, TEXT)
    >>>
    >>> data = 'Hello <em>Baby</em>'
    >>> for type, value, line in XMLParser(data):
    ...     if type == START_ELEMENT:
    ...         tag_uri, tag_name, attributes = value
    ...         print 'START TAG :', tag_name
    ...     elif type == END_ELEMENT:
    ...         tag_uri, tag_name = value
    ...         print 'END TAG   :', tag_name
    ...     elif type == TEXT:
    ...         print 'TEXT      :', value
    ...
    TEXT      : Hello
    START TAG : em
    TEXT      : Baby
    END TAG   : em

This example just prints a message to the standard output each time the start
of an element, the end of an element or a text node is found.

The parser returns a list of events, where every event is a tuple of three
values: the event type, the value (which depends on the event type) and the
line number. The events implemented are:

    =============== ===================================
    Event           Value
    =============== ===================================
    *XML_DECL*      ``(version, encoding, standalone)``
    --------------- -----------------------------------
    *DOCUMENT_TYPE* ``(name, doctype)``
    --------------- -----------------------------------
    *START_ELEMENT* ``(tag uri, tag name, attributes)``
    --------------- -----------------------------------
    *END_ELEMENT*   ``(tag uri, tag name)``
    --------------- -----------------------------------
    *TEXT*          ``value``
    --------------- -----------------------------------
    *COMMENT*       ``value``
    --------------- -----------------------------------
    *PI*            ``(name, value)``
    --------------- -----------------------------------
    *CDATA*         ``value``
    =============== ===================================

All values (text nodes, comments, attribute values, etc.) are returned as byte
strings, in the source encoding. ``doctype`` is an instance of a
:class:`DocType` object.


Attributes
----------

The element attributes are returned as a dictionary where the key is a tuple
of the namespace URI and the local name of the attribute, and the value is the
value of the attribute.

For example, when processing the XML fragment:

.. code-block:: xml

    <x xmlns="namespace1" xmlns:n2="namespace2" >
      <test a="1" n2:b="2" />
    </x>

For the tag "``test``", the parser will return the attributes this way::

    ('namespace1', 'test', {('namespace2', 'b'): '2', (None, 'a'): '1'})

The parser always resolves the element and attribute prefixes and returns the
namespace URIs instead. The namespace declarations are returned as attributes.


Namespaces
==========

If the parser returns always byte strings for all text nodes and attribute
values, it is up to the programmer to correctly interpret them; for example to
transform the value of *href* attributes to URI references so we can work with
them more comfortably (see chapter :mod:`itools.uri` for details on URI
references).

To make this task easier :mod:`itools` offers support, *out of the box*, for
several common XML namespaces. One of them is XHTML::

    >>> from itools.xml import XMLParser, START_ELEMENT
    >>> from itools.xml import get_attr_datatype
    >>> import itools.html
    >>>
    >>> data = ('<a xmlns="http://www.w3.org/1999/xhtml"'
    ...         ' href="http://www.example.com"'
    ...         ' title="Example" />')
    >>>
    >>> for type, value, line in XMLParser(data):
    ...     if type == START_ELEMENT:
    ...         tag_uri, tag_name, attributes = value
    ...         for attr_uri, attr_name in attributes:
    ...             type = get_attr_datatype(tag_uri, tag_name,
    ...                                      attr_uri, attr_name)
    ...             attr_value = attributes[(attr_uri, attr_name)]
    ...             attr_value = type.decode(attr_value)
    ...             print attr_name, type
    ...             print repr(attr_value)
    ...             print
    xmlns <class 'itools.datatypes.primitive.String'>
    'http://www.w3.org/1999/xhtml'

    href <class 'itools.datatypes.primitive.URI'>
    'http://www.example.com'

    title <class 'itools.datatypes.base.Unicode({'context': 'title attribute'})'>
    u'Example'

The function :func:`get_attr_datatype` will directly return the datatype (see
chapter :mod:`itools.datatypes`) for a given namespace/tag/attribut
namespace/attribut name. It will allow us to deserialize the attribute
value.

The package :mod:`itools.html` is the one that actually implements the
namespace handler for XHTML.


Documents
=========

The package :mod:`itools.xml` also includes a handler class for XML files.
The state of the handler is just the very same events the parser returns::

    >>> from itools.xmlfile import XMLFile
    >>> from itools.handlers import ro_database
    >>>
    >>> document = ro_database.get_handler('hello.xml', XMLFile)
    >>> for type, value, line in document.events:
    ...     print 'Line:', line
    ...     print 'Type:', type
    ...     print 'Value:', repr(value)
    ...     print
    Line: 1
    Type: 0
    Value: ('1.0', 'UTF-8', None)

    Line: 1
    Type: 4
    Value: '\n'

    Line: 2
    Type: 2
    Value: (None, 'html', {})

    Line: 2
    Type: 4
    Value: '\n  '
    ...

This means that the same logic can be used to manipulate the stream of events
returned by the parser or the list of events kept by the handler.

