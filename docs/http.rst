:mod:`itools.http` -- HTTP
**************************

.. module:: itools.http
   :synopsis: HTTP

.. index::
   single: HTTP

.. contents::

The :mod:`itools.http` package offers an HTTP server with a simple programming
interface. It builds on the HTTP server provided by the `libsoup
<http://live.gnome.org/LibSoup>`_ C library.

.. note::

   This is a low-level programming interface. For a high-level web framework
   see the :mod:`itools.web` package.

Example:

.. code-block:: python

   from itools.http import HTTPServer
   from itools.loop import Loop

   class Ping(HTTPServer):
       def listen(self, address, port):
           super(Ping, self).listen(address, port)
           self.add_handler('/', self.path_callback)

       def path_callback(self, soup_message, path):
           method = soup_message.get_method()
           body = '%s %s' % (method, path)
           soup_message.set_status(200)
           soup_message.set_response('text/plain', body)

   server = Ping()
   server.listen('localhost', 8080)

   loop = Loop()
   loop.run()
