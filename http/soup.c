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


/*
 * HTTP Server
 */

typedef struct
{
  PyObject_HEAD
} Server;


static PyObject *
PyServer_start (PyObject * self, PyObject * args, PyObject * kwds)
{
  GMainLoop *loop;
  SoupServer *server;

  /* HTTP Server */
  g_thread_init (NULL);
  server = soup_server_new (SOUP_SERVER_PORT, 8080, NULL);
  soup_server_run_async (server);

  /* Main loop */
  loop = g_main_loop_new (NULL, FALSE);
  g_main_loop_run (loop);

  return Py_None;
}


static PyMethodDef PyServer_methods[] = {
  {"start", (PyCFunction) PyServer_start, METH_NOARGS, "Start the server"},
  {NULL} /* Sentinel */
};

static PyTypeObject PyServer = {
  PyObject_HEAD_INIT(NULL)
  0,                                /* ob_size */
  "itools.http.soup.HTTPServer",    /* tp_name */
  sizeof (Server),                  /* tp_basicsize */
  0,                                /* tp_itemsize */
  0,                                /* tp_dealloc */
  0,                                /* tp_print */
  0,                                /* tp_getattr */
  0,                                /* tp_setattr */
  0,                                /* tp_compare */
  0,                                /* tp_repr */
  0,                                /* tp_as_number */
  0,                                /* tp_as_sequence */
  0,                                /* tp_as_mapping */
  0,                                /* tp_hash */
  0,                                /* tp_call */
  0,                                /* tp_str */
  0,                                /* tp_getattro */
  0,                                /* tp_setattro */
  0,                                /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT,               /* tp_flags */
  "HTTP Server",                    /* tp_doc */
  0,                                /* tp_traverse */
  0,                                /* tp_clear */
  0,                                /* tp_richcompare */
  0,                                /* tp_weaklistoffset */
  0,                                /* tp_iter */
  0,                                /* tp_iternext */
  PyServer_methods,                 /* tp_methods */
  0,                                /* tp_members */
  0,                                /* tp_getset */
  0,                                /* tp_base */
  0,                                /* tp_dict */
  0,                                /* tp_descr_get */
  0,                                /* tp_descr_set */
  0,                                /* tp_dictoffset */
  0,                                /* tp_init */
  0,                                /* tp_alloc */
  PyType_GenericNew,                /* tp_new */
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

  /* Server Object */
  if (PyType_Ready (&PyServer) != 0)
    return;
  Py_INCREF (&PyServer);
  PyModule_AddObject (module, "HTTPServer", (PyObject *) & PyServer);
}
