/*
 * Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
 * Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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


/**************************************************************************
 * The Prolog
 *************************************************************************/

#include <Python.h>
#include <structmember.h>
#include <stdlib.h>

#include "parser.h"


/*************
 * Constants *
 *************/

#define BUFFER_SIZE 512


/**************************************************************************
 * The internal functions/objects
 *************************************************************************/

/********************
 * Interned strings *
 ********************/

/*
 * It's not "interned", just for tests, ...
 */
PyObject *
XMLParser_intern_string (gchar * str)
{
  if (str[0] == '\0')
    {
      Py_INCREF (Py_None);
      return Py_None;
    }

  return PyString_FromString ((char *) str);
}


/***********************
 * The XMLError object *
 ***********************/

static PyObject *XMLError;


/************************
 * The XMLParser object *
 ************************/

typedef struct
{
  PyObject_HEAD
  Parser * parser;
  PyObject *source;
  Event event;
} XMLParser;


/*****************************
 * The translation functions *
 *****************************/

PyObject *
XMLParser_translate_STag (XMLParser * self)
{
  StartTagEvent *event = (StartTagEvent *) & self->event;
  PyObject *uri, *name, *attributes, *qname, *value, *result;
  Attribute *attribute;
  guint idx;

  /* The attributes Dict */
  attributes = PyDict_New ();
  if (attributes == NULL)
    return NULL;

  for (idx = 0, attribute = event->attributes; idx < event->attributes_number;
       idx++, attribute++)
    {
      /* uri */
      uri = XMLParser_intern_string (attribute->uri);
      if (uri == NULL)
        {
          Py_DECREF (attributes);
          return NULL;
        }
      /* name */
      name = XMLParser_intern_string (attribute->name);
      if (name == NULL)
        {
          Py_DECREF (attributes);
          Py_DECREF (uri);
          return NULL;
        }
      /* The tuple (uri, value) */
      qname = Py_BuildValue ("(OO)", uri, name);
      if (qname == NULL)
        {
          Py_DECREF (attributes);
          Py_DECREF (uri);
          Py_DECREF (uri);
          Py_DECREF (name);
          Py_DECREF (name);
          return NULL;
        }
      /* Py_Buildvalue increments the counters */
      Py_DECREF (uri);
      Py_DECREF (name);
      /* The value */
      value = PyString_FromString ((char *) (attribute->value->str));
      if (value == NULL)
        {
          Py_DECREF (attributes);
          Py_DECREF (qname);
          return NULL;
        }
      /* Store the result */
      if (PyDict_SetItem (attributes, qname, value) != 0)
        {
          Py_DECREF (attributes);
          /* XXX two times ??? */
          Py_DECREF (qname);
          Py_DECREF (value);
          return NULL;
        }
      /* PyDict_SetItem increments the counters ?? */
      Py_DECREF (qname);
      Py_DECREF (value);
    }

  /* uri */
  uri = XMLParser_intern_string (event->uri);
  if (uri == NULL)
    {
      Py_DECREF (attributes);
      return NULL;
    }
  /* name */
  name = XMLParser_intern_string (event->name);
  if (name == NULL)
    {
      Py_DECREF (attributes);
      Py_DECREF (uri);
      return NULL;
    }

  /* The result */
  result = Py_BuildValue ("(NNN)", uri, name, attributes);
  if (result == NULL)
    {
      Py_DECREF (uri);
      Py_DECREF (name);
      Py_DECREF (attributes);
      return NULL;
    }

  return result;
}


PyObject *
XMLParser_translate_ETag (XMLParser * self)
{
  EndTagEvent *event = (EndTagEvent *) & self->event;
  PyObject *uri, *name, *result;

  /* uri */
  uri = XMLParser_intern_string (event->uri);
  if (uri == NULL)
    return NULL;

  /* name */
  name = XMLParser_intern_string (event->name);
  if (name == NULL)
    {
      Py_DECREF (uri);
      return NULL;
    }

  /* The result */
  result = Py_BuildValue ("(NN)", uri, name);
  if (result == NULL)
    {
      Py_DECREF (uri);
      Py_DECREF (name);
      return NULL;
    }

  return result;
}


PyObject *
XMLParser_translate_PI (XMLParser * self)
{
  PIEvent *event = (PIEvent *) & self->event;
  return Py_BuildValue ("(ss)", event->pi_target, event->content);
}


PyObject *
XMLParser_translate_Decl (XMLParser * self)
{
  DeclEvent *event = (DeclEvent *) & self->event;
  PyObject *version, *encoding, *standalone, *result;

  /* Version */
  version = PyString_FromString (event->version);
  if (version == NULL)
    return NULL;

  /* Encoding */
  encoding = PyString_FromString (event->encoding);
  if (encoding == NULL)
    {
      Py_DECREF (version);
      return NULL;
    }

  /* standalone */
  if ((event->standalone)[0] == '\0')
    {
      Py_INCREF (Py_None);
      standalone = Py_None;
    }
  else
    {
      standalone = PyString_FromString (event->standalone);
      if (standalone == NULL)
        {
          Py_DECREF (version);
          Py_DECREF (encoding);
          return NULL;
        }
    }

  /* The result */
  result = Py_BuildValue ("(NNN)", version, encoding, standalone);
  if (result == NULL)
    {
      Py_DECREF (version);
      Py_DECREF (encoding);
      Py_DECREF (standalone);
      return NULL;
    }

  return result;
}


/**************************************************************************
 * Methods of XMLParser
 *************************************************************************/

static PyObject *
XMLParser_new (PyTypeObject * type, PyObject * args, PyObject * kwds)
{
  XMLParser *self;

  self = (XMLParser *) type->tp_alloc (type, 0);
  if (self != NULL)
    {
      self->parser = NULL;
      self->source = NULL;
    }

  return (PyObject *) self;
}


static void
XMLParser_reset (XMLParser * self)
{
  if (self->parser != NULL)
    parser_free (self->parser);
  Py_XDECREF (self->source);
}


static void
XMLParser_dealloc (XMLParser * self)
{
  XMLParser_reset (self);
  self->ob_type->tp_free ((PyObject *) self);
}


static int
XMLParser_init (XMLParser * self, PyObject * args, PyObject * kwds)
/* __init__(source, namespaces=None, doctype=None)
 * source: is a string or a file
 * namespaces: a dictionnary (prefix => uri)
 * doctype: a string parsed before the document
 */
{
  PyObject *source;
  PyObject *namespaces = NULL;
  char *doctype = NULL;
  static char *kwlist[] = { "source", "namespaces", "doctype", NULL };

  Parser *parser;

  PyObject *py_prefix, *py_uri;
  char *prefix, *uri;
  Py_ssize_t pos = 0;


  /* Reset, if not new */
  XMLParser_reset (self);

  /* Arguments */
  if (!PyArg_ParseTupleAndKeywords (args, kwds, "O|Os", kwlist, &source,
                                    &namespaces, &doctype))
    return -1;


  /* Check the source */
  if (PyString_CheckExact (source))
    {
      /* Create the parser object */
      parser = parser_new (PyString_AsString (source), NULL);
    }
  else if (PyFile_CheckExact (source))
    {
      /* Set the buffer size */
      PyFile_SetBufSize (source, BUFFER_SIZE);

      /* Create the parser object */
      parser = parser_new (NULL, PyFile_AsFile (source));
    }
  else
    {
      PyErr_SetString (PyExc_TypeError, "argument 1 must be string or file");
      return -1;
    }

  /* End of the creation of the parser object */
  if (parser == NULL)
    {
      PyErr_SetString (PyExc_TypeError, "an error occurred during the "
                       "parser initialization");
      return -1;
    }
  self->parser = parser;


  /* To avoid its destruction */
  Py_INCREF (source);
  self->source = source;

  /* Add the namespaces */
  if (namespaces)
    {
      if (PyDict_Check (namespaces))
        while (PyDict_Next (namespaces, &pos, &py_prefix, &py_uri))
          {
            /* Keep the prefix. */
            if (py_prefix == Py_None)
              prefix = "";
            else
              prefix = PyString_AsString (py_prefix);

            /* Keept the URI. */
            uri = PyString_AsString (py_uri);

            /* And add the namespace */
            parser_add_namespace (parser, prefix, uri);
          }
      else
        {
          PyErr_SetString (PyExc_TypeError, "argument 2 must be dictionnary");
          return -1;
        }
    }

  /* Parse a doctype ? */
  if (doctype)
    if (parser_add_doctype (parser, doctype))
      {
        PyErr_Format (XMLError, "an error occured during the 'doctype' "
                      "argument parsing");
        return -1;
      }

  return 0;
}


static PyObject *
XMLParser_iternext (XMLParser * self)
{
  PyObject *value;

  if (!parser_next (self->parser, &(self->event)))
    {
      switch (self->event.type)
        {
        case XML_DECL:
          value = XMLParser_translate_Decl (self);
          break;
        case START_ELEMENT:
          value = XMLParser_translate_STag (self);
          break;
        case END_ELEMENT:
          value = XMLParser_translate_ETag (self);
          break;
        case DOCUMENT_TYPE:
        case TEXT:
        case COMMENT:
        case CDATA:
          value = PyString_FromString (self->event.text_event.text);
          break;
        case PI:
          value = XMLParser_translate_PI (self);
          break;
        case END_DOCUMENT:
          return NULL;
        case NOT_IMPLEMENTED:
        default:
          value = PyString_FromString ("Not implemented");
        }

      if (value == NULL)
        return PyErr_NoMemory ();

      return Py_BuildValue ("(iNi)", self->event.type, value,
                            self->event.common_event.row);
    }
  else
    {
      return PyErr_Format (XMLError, "%s: line %d, column %d",
                           self->event.error_event.description,
                           self->event.error_event.error_row,
                           self->event.error_event.error_column);
    }
}


/**************************************************************************
 * Declaration of XMLParser
 *************************************************************************/

/* The XMLParser object: type. */
static PyTypeObject XMLParserType = {
  PyObject_HEAD_INIT
  (NULL) 0,                     /* ob_size */
  "itools.xml.parser.XMLParser",/* tp_name */
  sizeof (XMLParser),           /* tp_basicsize */
  0,                            /* tp_itemsize */
  (destructor) XMLParser_dealloc,       /* tp_dealloc */
  0,                            /* tp_print */
  0,                            /* tp_getattr */
  0,                            /* tp_setattr */
  0,                            /* tp_compare */
  0,                            /* tp_repr */
  0,                            /* tp_as_number */
  0,                            /* tp_as_sequence */
  0,                            /* tp_as_mapping */
  0,                            /* tp_hash */
  0,                            /* tp_call */
  0,                            /* tp_str */
  0,                            /* tp_getattro */
  0,                            /* tp_setattro */
  0,                            /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT,           /* tp_flags */
  "Low-Level XML Parser",       /* tp_doc */
  0,                            /* tp_traverse */
  0,                            /* tp_clear */
  0,                            /* tp_richcompare */
  0,                            /* tp_weaklistoffset */
  PyObject_SelfIter,            /* tp_iter */
  (iternextfunc) XMLParser_iternext,    /* tp_iternext */
  0,                            /* tp_methods */
  0,                            /* tp_members */
  0,                            /* tp_getset */
  0,                            /* tp_base */
  0,                            /* tp_dict */
  0,                            /* tp_descr_get */
  0,                            /* tp_descr_set */
  0,                            /* tp_dictoffset */
  (initproc) XMLParser_init,    /* tp_init */
  0,                            /* tp_alloc */
  (newfunc) XMLParser_new,      /* tp_new */
};


/**************************************************************************
 * Module functions
 *************************************************************************/

static PyObject *
pyparser_register_dtd (PyObject * trash, PyObject * args, PyObject * kwds)
{
  static char *kwlist[] = { "urn", "filename", NULL };
  char *urn, *filename;

  /* Arguments */
  if (!PyArg_ParseTupleAndKeywords (args, kwds, "ss", kwlist, &urn,
                                    &filename))
    return NULL;

  /* Register */
  parser_register_dtd (urn, filename);

  Py_RETURN_NONE;
}


/**************************************************************************
 * Declaration of the module
 *************************************************************************/

static PyMethodDef module_methods[] = {
  {"register_dtd", (PyCFunction) pyparser_register_dtd,
   METH_VARARGS | METH_KEYWORDS, "Register a URN"},
  {NULL}                        /* Sentinel */
};


/* declarations for DLL import/export */
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

/* Declaration */
PyMODINIT_FUNC
initparser (void)
{
  /* TODO Make verifications / destructions ... */
  PyObject *module;

  /* Register parser */
  module = Py_InitModule3 ("parser", module_methods, "Low-level XML parser");
  if (module == NULL)
    return;

  /* Register XMLParser */
  if (PyType_Ready (&XMLParserType) != 0)
    return;
  Py_INCREF (&XMLParserType);
  PyModule_AddObject (module, "XMLParser", (PyObject *) & XMLParserType);

  /* Register exceptions */
  XMLError = PyErr_NewException ("itools.xml.parser.XMLError", NULL, NULL);
  Py_INCREF (XMLError);
  PyModule_AddObject (module, "XMLError", XMLError);

  /* Register constants */
  PyModule_AddIntConstant (module, "XML_DECL", XML_DECL);
  PyModule_AddIntConstant (module, "DOCUMENT_TYPE", DOCUMENT_TYPE);
  PyModule_AddIntConstant (module, "START_ELEMENT", START_ELEMENT);
  PyModule_AddIntConstant (module, "END_ELEMENT", END_ELEMENT);
  PyModule_AddIntConstant (module, "TEXT", TEXT);
  PyModule_AddIntConstant (module, "COMMENT", COMMENT);
  PyModule_AddIntConstant (module, "PI", PI);
  PyModule_AddIntConstant (module, "CDATA", CDATA);
}
