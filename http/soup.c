/*
 * Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>
#include <soup.h>

/* Variable names are prefixed by one letter:
 *   p_xxx - is a Python object
 *   g_xxx - is a glib object
 *   s_xxx - is a libsoup object
 *
 * Variables without a prefix are standard C types.
 */


/**************************************************************************
 * Access Log
 *************************************************************************/

static gchar *
get_request_line (SoupMessage * s_msg)
{
  SoupHTTPVersion s_http_version;
  gchar * format;
  SoupURI * s_uri;
  char * uri;
  gchar * request_line;

  /* The request URI */
  s_uri = soup_message_get_uri (s_msg);
  uri = soup_uri_to_string (s_uri, TRUE);

  /* The HTTP version */
  s_http_version = soup_message_get_http_version (s_msg);
  if (s_http_version == SOUP_HTTP_1_0)
    format = "%s %s HTTP/1.0";
  else
    format = "%s %s HTTP/1.1";

  request_line = g_strdup_printf (format, s_msg->method, uri);
  free (uri);
  return request_line;
}


static gchar *
get_access_log_line (SoupMessage * s_msg, SoupClientContext * s_client)
{
  /* Common Log Format
   *  - IP address of the client
   *  - RFC 1413 identity (not available)
   *  - username (TODO not provided right now, should we?)
   *  - time (FIXME we use the timezone name, use the offset, e.g. +0100)
   *  - the request line
   *  - the status code
   *  - content length of the response
   */
  time_t ts_t;
  struct tm * ts_tm;
  char ts[32];
  gchar * request_line;
  gchar * log_line;

  /* Timestamp */
  ts_t = time (NULL);
  ts_tm = gmtime (&ts_t);
  strftime (ts, sizeof(ts), "%d/%b/%Y:%H:%M:%S %Z", ts_tm);

  /* The log line */
  request_line = get_request_line (s_msg),
  log_line = g_strdup_printf ("%s - - [%s] \"%s\" %d %d\n",
                              soup_client_context_get_host (s_client),
                              ts, request_line, s_msg->status_code,
                              (int) s_msg->response_body->length);
  free (request_line);

  return log_line;
}



/**************************************************************************
 * PyMessage
 *************************************************************************/

typedef struct
{
  PyObject_HEAD
  SoupMessage * s_msg;
} PyMessage;


static PyObject *
PyMessage_get_method (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  return PyString_FromString (self->s_msg->method);
}


static PyObject *
PyMessage_get_uri (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  SoupURI * s_uri;
  char * uri;
  PyObject * p_uri;

  /* The request URI */
  s_uri = soup_message_get_uri (self->s_msg);
  uri = soup_uri_to_string (s_uri, FALSE);

  p_uri = PyString_FromString (uri);
  free (uri);
  return p_uri;
}


static PyObject *
PyMessage_set_header (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  char *name, *value;

  if (!PyArg_ParseTuple (args, "ss", &name, &value))
    return NULL;

  soup_message_headers_replace (self->s_msg->response_headers, name, value);

  Py_RETURN_NONE;
}


static PyObject *
PyMessage_set_response (PyMessage * self, PyObject * args, PyObject *kwdict)
{
  char *content_type, *body;
  gsize content_length;

  if (!PyArg_ParseTuple (args, "ss#", &content_type, &body, &content_length))
    return NULL;

  soup_message_set_response (self->s_msg, content_type, SOUP_MEMORY_COPY, body,
                             content_length);

  Py_RETURN_NONE;
}


static PyObject *
PyMessage_set_status (PyMessage * self, PyObject * args, PyObject * kwdict)
{
  guint status;

  if (!PyArg_ParseTuple (args, "I", &status))
    return NULL;

  soup_message_set_status (self->s_msg, status);

  Py_RETURN_NONE;
}


static PyMethodDef PyMessage_methods[] = {
  {"get_method", (PyCFunction) PyMessage_get_method, METH_NOARGS,
   "Get the request method"},
  {"get_uri", (PyCFunction) PyMessage_get_uri, METH_NOARGS,
   "Get the request uri"},
  {"set_header", (PyCFunction) PyMessage_set_header, METH_VARARGS,
   "Set the given response header"},
  {"set_response", (PyCFunction) PyMessage_set_response, METH_VARARGS,
   "Set the repsonse body"},
  {"set_status", (PyCFunction) PyMessage_set_status, METH_VARARGS,
   "Set the response status code"},
  {NULL} /* Sentinel */
};


static PyTypeObject PyMessageType = {
  PyObject_HEAD_INIT(NULL)
  0,                                         /* ob_size */
  "itools.http.soup.SoupMessage",            /* tp_name */
  sizeof (PyMessage),                        /* tp_basicsize */
  0,                                         /* tp_itemsize */
  0,                                         /* tp_dealloc */
  0,                                         /* tp_print */
  0,                                         /* tp_getattr */
  0,                                         /* tp_setattr */
  0,                                         /* tp_compare */
  0,                                         /* tp_repr */
  0,                                         /* tp_as_number */
  0,                                         /* tp_as_sequence */
  0,                                         /* tp_as_mapping */
  0,                                         /* tp_hash */
  0,                                         /* tp_call */
  0,                                         /* tp_str */
  0,                                         /* tp_getattro */
  0,                                         /* tp_setattro */
  0,                                         /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT,                        /* tp_flags */
  "Wrapper of SoupMessage",                  /* tp_doc */
  0,                                         /* tp_traverse */
  0,                                         /* tp_clear */
  0,                                         /* tp_richcompare */
  0,                                         /* tp_weaklistoffset */
  0,                                         /* tp_iter */
  0,                                         /* tp_iternext */
  PyMessage_methods,                         /* tp_methods */
  0,                                         /* tp_members */
  0,                                         /* tp_getset */
  0,                                         /* tp_base */
  0,                                         /* tp_dict */
  0,                                         /* tp_descr_get */
  0,                                         /* tp_descr_set */
  0,                                         /* tp_dictoffset */
  0,                                         /* tp_init */
  0,                                         /* tp_alloc */
  PyType_GenericNew,                         /* tp_new */
};


/**************************************************************************
 * PyServer
 *************************************************************************/

typedef struct
{
  PyObject_HEAD
  SoupServer * s_server;
} PyServer;


void
s_server_callback (SoupServer * s_server, SoupMessage * s_msg,
                   const char * path, GHashTable * g_query,
                   SoupClientContext * s_client, gpointer server)
{
  PyMessage * p_message;
  gchar * log_line;

  /* Create the Python Message object */
  p_message = PyObject_New (PyMessage, &PyMessageType);
  if (!p_message)
    /* ERROR */
    return;

  p_message->s_msg = s_msg;

  /* Call the Python callback */
  if (!PyObject_CallMethod (server, "callback", "Os", p_message, path))
    {
      /* The Python callback should never fail, it is its responsability to
       * catch and handle exceptions */
      printf("ERROR! Python's callback failed, this should never happen\n");
      abort ();
    }

  /* Acces Log */
  log_line = get_access_log_line (s_msg, s_client);
  if (!PyObject_CallMethod (server, "log_access", "s", log_line))
    {
      /* The Python callback should never fail, it is its responsability to
       * catch and handle exceptions */
      printf("ERROR! Python's access log failed, this should never happen\n");
      abort ();
    }

  /* Ok */
  free (log_line);
  return;
}


static int
PyServerType_init (PyServer * self, PyObject * args, PyObject * kwdict)
{
  /* Defines the parameters */
  static char *kwlist[] = { "address", "port", NULL };
  char *address = "";
  guint port = 8080;
  /* libsoup variables */
  SoupAddress *s_address;
  SoupServer *s_server;

  /* Arguments */
  if (!PyArg_ParseTupleAndKeywords (args, kwdict, "|sI", kwlist, &address,
                                    &port))
    return -1;

  /* http://bugzilla.gnome.org/show_bug.cgi?id=532778 */
  g_thread_init (NULL);

  /* TODO This does not work, soup_server_new fails with SOUP_SERVER_INTERFACE
   * Loosely related, http://bugzilla.gnome.org/show_bug.cgi?id=561547
   */
  s_address = soup_address_new (address, port);
  if (!s_address)
    /* TODO Set Python error condition */
    return -1;

  s_server = soup_server_new (SOUP_SERVER_SERVER_HEADER, "itools.http",
                              /* SOUP_SERVER_INTERFACE, s_address, */
                              SOUP_SERVER_PORT, port, NULL);
  if (!s_server)
    /* TODO Set Python error condition */
    return -1;
  self->s_server = s_server;

  /* Handler */
  soup_server_add_handler (s_server, "/", s_server_callback, self, NULL);

  return 0;
}


static PyObject *
PyServerType_stop (PyServer * self, PyObject * args, PyObject * kwdict)
{
  soup_server_quit (self->s_server);

  Py_RETURN_NONE;
}


static PyObject *
PyServerType_start (PyServer * self, PyObject * args, PyObject * kwdict)
{
  /* Run */
  soup_server_run_async (self->s_server);

  Py_RETURN_NONE;
}


static PyMethodDef PyServer_methods[] = {
  {"stop", (PyCFunction) PyServerType_stop, METH_NOARGS, "Stop the server"},
  {"start", (PyCFunction) PyServerType_start, METH_NOARGS, "Start the server"},
  {NULL} /* Sentinel */
};


static PyTypeObject PyServerType = {
  PyObject_HEAD_INIT(NULL)
  0,                                         /* ob_size */
  "itools.http.soup.SoupServer",             /* tp_name */
  sizeof (PyServer),                         /* tp_basicsize */
  0,                                         /* tp_itemsize */
  0,                                         /* tp_dealloc */
  0,                                         /* tp_print */
  0,                                         /* tp_getattr */
  0,                                         /* tp_setattr */
  0,                                         /* tp_compare */
  0,                                         /* tp_repr */
  0,                                         /* tp_as_number */
  0,                                         /* tp_as_sequence */
  0,                                         /* tp_as_mapping */
  0,                                         /* tp_hash */
  0,                                         /* tp_call */
  0,                                         /* tp_str */
  0,                                         /* tp_getattro */
  0,                                         /* tp_setattro */
  0,                                         /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  /* tp_flags */
  "HTTP Server",                             /* tp_doc */
  0,                                         /* tp_traverse */
  0,                                         /* tp_clear */
  0,                                         /* tp_richcompare */
  0,                                         /* tp_weaklistoffset */
  0,                                         /* tp_iter */
  0,                                         /* tp_iternext */
  PyServer_methods,                          /* tp_methods */
  0,                                         /* tp_members */
  0,                                         /* tp_getset */
  0,                                         /* tp_base */
  0,                                         /* tp_dict */
  0,                                         /* tp_descr_get */
  0,                                         /* tp_descr_set */
  0,                                         /* tp_dictoffset */
  (initproc) PyServerType_init,              /* tp_init */
  0,                                         /* tp_alloc */
  PyType_GenericNew,                         /* tp_new */
};



/**************************************************************************
 * Declaration of the module
 *************************************************************************/

static PyMethodDef module_methods[] = {
  {NULL}                        /* Sentinel */
};


/* declarations for DLL import/export */
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

/* Declaration */
PyMODINIT_FUNC
initsoup (void)
{
  PyObject *module;

  /* Intialilze module */
  module = Py_InitModule3 ("soup", module_methods, "Wrapper of libsoup");
  if (module == NULL)
    return;

  /* Server Type */
  if (PyType_Ready (&PyServerType) != 0)
    return;
  Py_INCREF (&PyServerType);
  PyModule_AddObject (module, "SoupServer", (PyObject *) & PyServerType);

  /* Message Type */
  if (PyType_Ready (&PyMessageType) != 0)
    return;
  Py_INCREF (&PyMessageType);
  PyModule_AddObject (module, "SoupMessage", (PyObject *) & PyMessageType);
}
