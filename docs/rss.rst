:mod:`itools.rss` -- RSS feeds
******************************

.. module:: itools.rss
   :synopsis: A RSS handler

.. index::
   single: RSS

.. contents::


The package :mod:`itools.rss` provides the loading and generating of a RSS 2.0
feed.

This package was designed for simplicity and ease of use. It does not provide
automatic syndication in any way. Instead, it was made as simple as possible,
with a Pythonic API, for you to integrate without pain.

This API is particulary suited to display an RSS feed in a web page throught
the :mod:`itools.stl` template language.


Reading a feed
==============


Example
-------

We will illustrate the usage of this package throught the sample file provided
by the RSS Advisory Board.

Let's open this sample::

    >>> import itools.http
    >>> from itools.handlers import ro_database
    >>> from itools.rss import RSSFile
    >>>
    >>> sample = ro_database.get_handler('http://www.rssboard.org/files/sample-rss-2.xml', RSSFile)

Notice we haven't used the ability of :mod:`vfs` to directly open and load the
feed, because the web server doesn't send the ``application/rss+xml``
mimetype, nor the ``.rss`` file extension. Indeed the :mod:`rss` package has
registered itself in itools to handle both this mimetype and this extension.

Now there are three main entries in the RSSFile API:

.. class:: RSSFile

  .. attribute:: channel

        is a dictionary describing the feed.

  .. attribute:: image

        is an optional dictionary locating an image and its properties,
        :obj:`None` by default.

  .. attribute:: items

        is a list of dictionaries, one per item.

All :attr:`channel`, :attr:`image` and individual :attr:`item` dictionaries
are mapping the RSS 2.0 elements to keys, are their contents to values.


The Channel
-----------

An example is worth a thousand words::

    >>> from pprint import pprint
    >>> pprint(sample.channel)
    {'description': u'Liftoff to Space Exploration.',
     'docs': 'http://blogs.law.harvard.edu/tech/rss',
     'generator': u'Weblog Editor 2.0',
     'language': 'en-us',
     'lastBuildDate': datetime.datetime(2003, 6, 10, 11, 41, 1),
     'link': 'http://liftoff.msfc.nasa.gov/',
     'managingEditor': 'editor@example.com',
     'pubDate': datetime.datetime(2003, 6, 10, 6, 0),
     'title': u'Liftoff News',
     'webMaster': 'webmaster@example.com'}

Now you can see that the most important elements were decoded to Python
objects. Specifically, texts are decoded into unicode. The *link* element is
decoded into a :class:`itools.uri.Reference` object. Notice the datetimes are
converted to your local time zone.


The Items
---------

The :attr:`items` attribute is a list of each :attr:`item` element contained
in the file. The order of these items is respected.

Knowing the number of items in the feed is straightforward::

    >>> len(sample.items)
    4


An Item
^^^^^^^

As for the channel, RSS 2.0 item elements are mapped into a dictionary::

    >>> pprint(sample.items[0])
    {'description': u'How do Americans get ready to work with Russians aboard
                      the International Space Station? They take a crash
                      course in culture, language and protocol at Russia\'s <a
                      href="http://howe.iki.rssi.ru/GCTC/gctc_e.htm">Star
                      City</a>.',
     'guid': 'http://liftoff.msfc.nasa.gov/2003/06/03.html#item573',
     'link': 'http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp',
     'pubDate': datetime.datetime(2003, 6, 3, 11, 39, 21),
     'title': u'Star City'}


Generating a Feed
=================

Now that you know how RSSFile objects look like, you'll understand that
creating a feed is all about filling the dictionaries of a new RSSFile object.

The basis of the :attr:`channel` dictionary is set::

    >>> mysample = RSSFile()
    >>> pprint(mysample.channel)
    {'description': None,
     'lastBuildDate': datetime.datetime(2007, 12, 6, 20, 24, 29, 765501),
     'link': None,
     'title': None}

Required elements were added. The ``lastBuildDate`` element is the datetime
when you create the object. Of course you can replace it. Remember it is
expressed in your local time zone, and will be encoded into GMT (UTC actually)
representation.

No image nor item are created by default::

    >>> pprint(mysample.image)
    None
    >>> pprint(mysample.items)
    []

As when loading a feed without an :attr:`image` element, the :attr:`image`
attribute is set to :obj:`None` by default (and will not be written in the
output feed if not set).

No default dictionary is set for items. Created one from scratch and append it
to the :attr:`items` list.


Writing the Feed
----------------

To turn your channel, maybe your image, and your items into an XML file for
RSS agregators to digest, simply use the :mod:`itools.handlers` API::

    >>> mysample.to_str()
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
       <channel>
          <title>[...]

Notice the default encoding is UTF-8. You can change it throught the
*encoding* keyword parameter.


Sending the Feed
----------------

The idea is to interpret the *IF-Modified-Since* request header, and set the
*Last-Modified* response header when replying with the feed. Or send *304 Not
Modified* if nothing changed meanwhile.

The :mod:`itools.web` server automatically deals with these headers if you
help it. It can even reply to agregators having the latest version.

To help it, you need to set a :meth:`*__mtime__` method along with your method
returning the feed.

For instance, if you implement the :meth:`feed` method in your Web application
to return the RSS feed, set the :meth:`feed__mtime__` method to return a
datetime object. You will basically return the date of the last modified
article.

The server will call this method and compare the value with the date sent by
the agregator.

An example to clarify it::

    from itools.web import BaseView

    class News(BaseView):

        def get_mtime(self, resource):
            # Return for example the modification date
            # of the last published article.
            ...


        def GET(self, resource, context):
            # The server already replied to agregators having the latest
            # version. So there is something to send.
            feed = RSSFile()
            ...

            # Filename and Content-Type, important!
            response = context.response
            response.set_header('Content-Disposition',
                                'inline; filename="articles.rss"')
            response.set_header('Content-Type', 'application/rss+xml')

            # Send the feed, the server will set "Last-Modified"
            return feed.to_str()

More details can be found in the :mod:`itools.web` chapter.


Other Feed Formats
==================

We chose to implement a single feed format, and we chose RSS 2.0 because it is
very simple.

But remember how simple :mod:`itools.rss` is! RSS 1.0 is a bit more complex,
and uses an RDF namespace.

Let's take a look at the Atom format. It is very similar to RSS 2.0 in
simplicity and usage. Implementing Atom is roughly copying the :file:`rss.py`
package and replace the RSS 2.0 element names to Atom names. More or less.


Reference
=========

See http://www.rssboard.org/rss-specification for a description of these
elements.

Most elements are not decoded and provided as a byte string.


Channel
-------


Required elements
^^^^^^^^^^^^^^^^^

    =========== ========
    Name        DataType
    =========== ========
    title       Unicode
    ----------- --------
    link        URI
    ----------- --------
    description Unicode
    =========== ========


Optional elements
^^^^^^^^^^^^^^^^^

    ============== ========
    Name           DataType
    ============== ========
    language       String
    -------------- --------
    copyright      Unicode
    -------------- --------
    managingEditor String
    -------------- --------
    webMaster      String
    -------------- --------
    pubDate        HTTPDate
    -------------- --------
    lastBuildDate  HTTPDate
    -------------- --------
    category       String
    -------------- --------
    generator      Unicode
    -------------- --------
    docs           String
    -------------- --------
    cloud          String
    -------------- --------
    ttl            String
    -------------- --------
    rating         String
    -------------- --------
    textInput      String
    -------------- --------
    skipHours      String
    -------------- --------
    skipDays       String
    ============== ========


Image
-----


Required elements
^^^^^^^^^^^^^^^^^

    ===== ========
    Name  DataType
    ===== ========
    url   URI
    ----- --------
    title Unicode
    ----- --------
    link  URI
    ===== ========


Optional elements
^^^^^^^^^^^^^^^^^

    =========== ========
    Name        DataType
    =========== ========
    width       Integer
    ----------- --------
    height      Integer
    ----------- --------
    description Unicode
    =========== ========


Item
----


Required elements
^^^^^^^^^^^^^^^^^

Either *title* or *description* is required, at your choice. Both are unicode.


Optional elements
^^^^^^^^^^^^^^^^^

    =========== ========
    Name        DataType
    =========== ========
    title       Unicode
    ----------- --------
    link        URI
    ----------- --------
    description Unicode
    ----------- --------
    author      String
    ----------- --------
    category    String
    ----------- --------
    comments    String
    ----------- --------
    enclosure   String
    ----------- --------
    guid        String
    ----------- --------
    pubDate     HTTPDate
    ----------- --------
    source      String
    =========== ========

