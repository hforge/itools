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

#include <Python.h>
#include <structmember.h>
#include <stdlib.h>

#include "parser.h"


/**************************************************************************
 * XMLError
 *************************************************************************/

static PyObject *XMLError;


/**************************************************************************
 * DocType
 *************************************************************************/

/************************
 * The PyDocType object *
 ************************/
typedef struct
{
  PyObject_HEAD
  DocType * doctype;
} PyDocType;


/**********************
 * DocType public API *
 **********************/
static PyObject *
PyDocType_new (PyTypeObject * type, PyObject * args, PyObject * kwds)
{
  PyDocType *self;

  self = (PyDocType *) type->tp_alloc (type, 0);
  if (self != NULL)
    self->doctype = NULL;

  return (PyObject *) self;
}


static void
PyDocType_dealloc (PyDocType * self)
{
  /* Reset, if not new */
  if (self->doctype)
    doctype_free (self->doctype);

  Py_TYPE(self)->tp_free ((PyObject *) self);
}


static int
PyDocType_init (PyDocType * self, PyObject * args, PyObject * kwds)
/* __init__(PubidLiteral=None, SystemLiteral=None, intSubset=None)
 */
{
  char *PubidLiteral = NULL;
  char *SystemLiteral = NULL;
  char *intSubset = NULL;
  static char *kwlist[] =
    { "PubidLiteral", "SystemLiteral", "intSubset", NULL };
  DocType *doctype;
  char *error_msg;

  /* Reset, if not new */
  if (self->doctype)
    doctype_free (self->doctype);

  /* Arguments */
  if (!PyArg_ParseTupleAndKeywords (args, kwds, "|zzz", kwlist, &PubidLiteral,
                                    &SystemLiteral, &intSubset))
    return -1;

  /* Creation of a new DocType object */
  doctype = doctype_new (PubidLiteral, SystemLiteral, intSubset, &error_msg);
  if (!doctype)
    {
      PyErr_SetString (XMLError, error_msg);
      return -1;
    }
  self->doctype = doctype;

  /* ALL OK */
  return 0;
}


static PyObject *
PyDocType_to_str (PyDocType * self, PyObject * trash1, PyObject * trash2)
{
  return PyUnicode_FromString (doctype_to_str (self->doctype));
}


static PyObject *
PyDocType_copy (PyDocType * self, PyObject * trash1, PyObject * trash2)
{
  Py_INCREF (self);
  return (PyObject *) self;
}


/********************************
 * Declaration of PyDocTypeType *
 ********************************/
static PyMethodDef PyDocType_methods[] = {
  {"to_str", (PyCFunction) PyDocType_to_str, METH_NOARGS, "Return a 'ready "
   "to insert' representation of the doctype"},
  {"__copy__", (PyCFunction) PyDocType_copy, METH_NOARGS, "copy handler"},
  {"__deepcopy__", (PyCFunction) PyDocType_copy, METH_VARARGS, "deepcopy "
   "handler"},
  {NULL}                        /* Sentinel */
};

static PyTypeObject PyDocTypeType = {
  PyVarObject_HEAD_INIT(NULL, 0)  /* ob_size */
  "itools.xml.parser.DocType",    /* tp_name */
  sizeof (PyDocType),             /* tp_basicsize */
  0,                              /* tp_itemsize */
  (destructor) PyDocType_dealloc, /* tp_dealloc */
  0,                              /* tp_print */
  0,                              /* tp_getattr */
  0,                              /* tp_setattr */
  0,                              /* tp_compare */
  0,                              /* tp_repr */
  0,                              /* tp_as_number */
  0,                              /* tp_as_sequence */
  0,                              /* tp_as_mapping */
  0,                              /* tp_hash */
  0,                              /* tp_call */
  0,                              /* tp_str */
  0,                              /* tp_getattro */
  0,                              /* tp_setattro */
  0,                              /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE ,             /* tp_flags */
  "The DocType object",           /* tp_doc */
  0,                              /* tp_traverse */
  0,                              /* tp_clear */
  0,                              /* tp_richcompare */
  0,                              /* tp_weaklistoffset */
  0,                              /* tp_iter */
  0,                              /* tp_iternext */
  PyDocType_methods,              /* tp_methods */
  0,                              /* tp_members */
  0,                              /* tp_getset */
  0,                              /* tp_base */
  0,                              /* tp_dict */
  0,                              /* tp_descr_get */
  0,                              /* tp_descr_set */
  0,                              /* tp_dictoffset */
  (initproc) PyDocType_init,      /* tp_init */
  0,                              /* tp_alloc */
  (newfunc) PyDocType_new,        /* tp_new */
};


/**************************************************************************
 * XMLParser
 *************************************************************************/

#define BUFFER_SIZE 512

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

  return PyUnicode_FromString ((char *) str);
}


/************************
 * The XMLParser object *
 ************************/
typedef struct
{
  PyObject_HEAD
  Parser * parser;
  PyObject *source;
  PyObject *py_doctype;
  Event event;
} XMLParser;


/*************************
 * XMLParser private API *
 *************************/
static PyObject *
XMLParser_translate_Decl (XMLParser * self)
{
  DeclEvent *event = (DeclEvent *) & self->event;
  PyObject *version, *encoding, *standalone, *result;

  /* Version */
  version = PyUnicode_FromString (event->version);
  if (version == NULL)
    return NULL;

  /* Encoding */
  encoding = PyUnicode_FromString (event->encoding);
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
      standalone = PyUnicode_FromString (event->standalone);
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


static PyObject *
XMLParser_translate_DocType (XMLParser * self)
{
  DocTypeEvent *event = (DocTypeEvent *) & self->event;
  PyDocType *py_doctype;
  PyObject *name, *result;

  /* Name */
  name = PyUnicode_FromString (event->name);
  if (!name)
    return NULL;

  /* Creation of a new PyDocType object */
  py_doctype = PyObject_New (PyDocType, &PyDocTypeType);
  if (!py_doctype)
    {
      Py_DECREF (name);
      return NULL;
    }
  py_doctype->doctype = event->doctype;
  self->py_doctype = (PyObject *) py_doctype;
  Py_INCREF (py_doctype);

  /* The result */
  result = Py_BuildValue ("(NN)", name, py_doctype);
  if (result == NULL)
    {
      Py_DECREF (name);
      Py_DECREF (py_doctype);
      return NULL;
    }

  return result;
}


static PyObject *
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
      qname = Py_BuildValue ("(NN)", uri, name);
      if (qname == NULL)
        {
          Py_DECREF (attributes);
          Py_DECREF (uri);
          Py_DECREF (name);
          return NULL;
        }
      /* The value */
      value = PyUnicode_FromString ((char *) (attribute->value->str));
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
          Py_DECREF (qname);
          Py_DECREF (value);
          return NULL;
        }
      /* PyDict_SetItem increments the counters */
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


static PyObject *
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


static PyObject *
XMLParser_translate_PI (XMLParser * self)
{
  PIEvent *event = (PIEvent *) & self->event;
  return Py_BuildValue ("(ss)", event->pi_target, event->content);
}


/************************
 * XMLParser public API *
 ************************/
static PyObject *
XMLParser_new (PyTypeObject * type, PyObject * args, PyObject * kwds)
{
  XMLParser *self;

  self = (XMLParser *) type->tp_alloc (type, 0);
  if (self != NULL)
    {
      self->parser = NULL;
      self->source = NULL;
      self->py_doctype = NULL;
    }

  return (PyObject *) self;
}


static void
XMLParser_reset (XMLParser * self)
{
  if (self->parser != NULL)
    parser_free (self->parser);
  Py_XDECREF (self->source);
  Py_XDECREF (self->py_doctype);
}


static void
XMLParser_dealloc (XMLParser * self)
{
  XMLParser_reset (self);
  Py_TYPE(self)->tp_free ((PyObject *) self);
}


static int
XMLParser_init (XMLParser * self, PyObject * args, PyObject * kwds)
/* __init__(source, namespaces=None, doctype=None)
 * source: is a string or a file
 * namespaces: a dictionnary (prefix => uri)
 * doctype: a PyDocType object
 */
{
  PyObject *source;
  PyObject *namespaces = NULL;
  PyObject *py_doctype = NULL;
  DocType *doctype = NULL;
  static char *kwlist[] = { "source", "namespaces", "doctype", NULL };

  Parser *parser;

  PyObject *py_prefix, *py_uri;
  const char *prefix, *uri;
  Py_ssize_t pos = 0;


  /* Reset, if not new */
  XMLParser_reset (self);

  /* Arguments */
  if (!PyArg_ParseTupleAndKeywords (args, kwds, "O|OO", kwlist, &source,
                                    &namespaces, &py_doctype))
    return -1;

  /* A DocType ? */
  if (py_doctype && py_doctype != Py_None)
    {
      /* A DocType object ? */
      if (!PyObject_TypeCheck (py_doctype, &PyDocTypeType))
        {
          PyErr_SetString (PyExc_TypeError, "the doctype argument must be "
                           "DocType object");
          return -1;
        }

      doctype = ((PyDocType *) py_doctype)->doctype;
    }

  int fd = PyObject_AsFileDescriptor(source);

  /* Check the source */
  if (PyUnicode_CheckExact (source))
    {
      /* Create the parser object */
      parser = parser_new (PyUnicode_AsUTF8 (source), NULL, doctype);
    }
  else if (fd != -1)
    {
      parser = parser_new (NULL, fdopen(fd, "w"), doctype);
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


  /* To avoid their destructions */
  Py_INCREF (source);
  self->source = source;
  Py_XINCREF (py_doctype);
  self->py_doctype = py_doctype;

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
              prefix = PyUnicode_AsUTF8 (py_prefix);

            /* Keep the URI. */
            uri = PyUnicode_AsUTF8 (py_uri);

            /* prefix and uri should be two strings */
            if (!prefix || !uri)
              {
                PyErr_SetString (PyExc_TypeError, "argument 2 must be a "
                                 "dictionary of {None or string: string}");
                return -1;
              }

            /* And add the namespace */
            parser_add_namespace (parser, prefix, uri);
          }
      else
        {
          PyErr_SetString (PyExc_TypeError, "argument 2 must be a "
                           "dictionary of {None or string: string}");
          return -1;
        }
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
        case DOCUMENT_TYPE:
          value = XMLParser_translate_DocType (self);
          break;
        case START_ELEMENT:
          value = XMLParser_translate_STag (self);
          break;
        case END_ELEMENT:
          value = XMLParser_translate_ETag (self);
          break;
        case TEXT:
        case COMMENT:
        case CDATA:
          value = PyUnicode_FromString (self->event.text_event.text);
          break;
        case PI:
          value = XMLParser_translate_PI (self);
          break;
        case END_DOCUMENT:
          return NULL;
        default:
          value = PyUnicode_FromString ("Not implemented");
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


/****************************
 * Declaration of XMLParser *
 ****************************/
static PyTypeObject XMLParserType = {
  PyVarObject_HEAD_INIT(NULL, 0)     /* ob_size */
  "itools.xml.parser.XMLParser",     /* tp_name */
  sizeof (XMLParser),                /* tp_basicsize */
  0,                                 /* tp_itemsize */
  (destructor) XMLParser_dealloc,    /* tp_dealloc */
  0,                                 /* tp_print */
  0,                                 /* tp_getattr */
  0,                                 /* tp_setattr */
  0,                                 /* tp_compare */
  0,                                 /* tp_repr */
  0,                                 /* tp_as_number */
  0,                                 /* tp_as_sequence */
  0,                                 /* tp_as_mapping */
  0,                                 /* tp_hash */
  0,                                 /* tp_call */
  0,                                 /* tp_str */
  0,                                 /* tp_getattro */
  0,                                 /* tp_setattro */
  0,                                 /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT,                /* tp_flags */
  "Low-Level XML Parser",            /* tp_doc */
  0,                                 /* tp_traverse */
  0,                                 /* tp_clear */
  0,                                 /* tp_richcompare */
  0,                                 /* tp_weaklistoffset */
  0, /* XXX set later: PyObject_SelfIter, */                /* tp_iter */
  (iternextfunc) XMLParser_iternext, /* tp_iternext */
  0,                                 /* tp_methods */
  0,                                 /* tp_members */
  0,                                 /* tp_getset */
  0,                                 /* tp_base */
  0,                                 /* tp_dict */
  0,                                 /* tp_descr_get */
  0,                                 /* tp_descr_set */
  0,                                 /* tp_dictoffset */
  (initproc) XMLParser_init,         /* tp_init */
  0,                                 /* tp_alloc */
  (newfunc) XMLParser_new,           /* tp_new */
};



/**************************************************************************
 * Module functions
 *************************************************************************/
static PyObject *
pyparser_register_dtd (PyObject * trash, PyObject * args, PyObject * kwds)
{
  static char *kwlist[] = { "filename", "urn", "uri", NULL };
  char *filename, *urn = NULL, *uri = NULL;

  /* Arguments */
  if (!PyArg_ParseTupleAndKeywords (args, kwds, "s|zz", kwlist, &filename,
                                    &urn, &uri))
    return NULL;


  /* Arguments verification */
  if (!urn && !uri)
    {
      PyErr_SetString (PyExc_TypeError,
                       "urn and uri cannot be simultaneously None");
      return NULL;
    }


  /* Register */
  doctype_register_dtd (filename, urn, uri);

  Py_RETURN_NONE;
}


/**************************************************************************
 * Declaration of the module
 *************************************************************************/

static PyMethodDef module_methods[] = {
  {"register_dtd", (PyCFunction) pyparser_register_dtd,
   METH_VARARGS | METH_KEYWORDS, "Register a URN or a URI"},
  {NULL}                        /* Sentinel */
};


/* declarations for DLL import/export */
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

static struct PyModuleDef Combinations =
{
    PyModuleDef_HEAD_INIT,
    "Combinations", /* name of module */
    "usage: Combinations.uniqueCombinations(lstSortableItems, comboSize)\n", /* module documentation, may be NULL */
    -1,   /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    module_methods
};

/* Declaration */
PyMODINIT_FUNC
initparser (void)
{
  /* TODO Make verifications / destructions ... */
  PyObject *module;

  /* XXX Fix tp_Iter for cygwin */
  XMLParserType.tp_iter = PyObject_SelfIter;

  /* Register parser */
  module = PyModule_Create(&Combinations);
  if (module == NULL)
    return NULL;

  /* Register XMLParser */
  if (PyType_Ready (&XMLParserType) != 0)
    return NULL;
  Py_INCREF (&XMLParserType);
  PyModule_AddObject (module, "XMLParser", (PyObject *) & XMLParserType);


  /* Register DocType (PyDocType) */
  if (PyType_Ready (&PyDocTypeType) != 0)
    return NULL;
  Py_INCREF (&PyDocTypeType);
  PyModule_AddObject (module, "DocType", (PyObject *) & PyDocTypeType);

  /* Register exceptions */
  XMLError = PyErr_NewException ("itools.xml.parser.XMLError",
                                 PyExc_Exception, NULL);
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
  return 0;
}
