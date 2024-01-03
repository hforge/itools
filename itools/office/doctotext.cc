/*
 * Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
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
#include <string.h>
#include <wv2/global.h>
#include <wv2/handlers.h>
#include <wv2/parser.h>
#include <wv2/parserfactory.h>
#include <wv2/word97_generated.h>
#include <wv2/ustring.h>



using namespace wvWare;



static PyObject *DocRtfException;
static PyObject *separator;
static PyObject *empty;



class PythonTextHandler: public TextHandler {
    public:
        PythonTextHandler();
        ~PythonTextHandler();
        virtual void runOfText(const UString& text,
                               SharedPtr<const Word97::CHP> chp);
#ifdef WV2_VERSION
        // 0.3.0 is the first one to add both these header and callback
        virtual void pictureFound(const PictureFunctor& picture,
                                  SharedPtr<const Word97::PICF>,
                                  SharedPtr<const Word97::CHP>);
#endif
        PyObject *get_text();
        PyObject *words;
};


PythonTextHandler::PythonTextHandler(void): TextHandler() {
    words = PyList_New(0);
}


PythonTextHandler::~PythonTextHandler(void) {
    Py_DECREF(words);
}


void PythonTextHandler::runOfText(const UString& text,
                                  SharedPtr<const Word97::CHP> chp) {
    unsigned short unicode;
    PyObject *character;

    for (int i = 0; i < text.length(); i++) {
        unicode = text[i].unicode();
        if ((character = PyUnicode_FromOrdinal(unicode))) {
            PyList_Append(words, character);
            Py_DECREF(character);
        }
    }
    PyList_Append(words, separator);

    TextHandler::runOfText(text, chp);
}


#ifdef WV2_VERSION
void PythonTextHandler::pictureFound(const PictureFunctor& picture,
                                     SharedPtr<const Word97::PICF>,
                                     SharedPtr<const Word97::CHP>) {
    // Completely ignore pictures because of an abort signal when trying to
    // uncompres uncompressed images in version 0.3.0.
    // Too bad if there is text (legend?).
}
#endif


PyObject *PythonTextHandler::get_text(void) {
    PyObject *text;

    text = PyUnicode_Join(empty, words);
    return text;
}



static PyObject *doc_to_text(PyObject *self, PyObject *args) {
    const unsigned char *buffer_in;
    int size;
    /* Python */
    PyObject *return_value = NULL;
    /* Wv2 */

    if (!PyArg_ParseTuple(args, "s#", &buffer_in, &size)) {
        return NULL;
    }

    if (!size) {
        PyErr_SetString(PyExc_ValueError, "data is empty");
        return NULL;
    }

    if (!(strncmp((char *)buffer_in, "{\\rtf", 5))) {
        PyErr_SetString(DocRtfException, "file is RTF not DOC");
        return NULL;
    }

    SharedPtr<Parser> parser(ParserFactory::createParser(buffer_in, size));
    if (parser) {
        PythonTextHandler *handler(new PythonTextHandler);
        parser->setTextHandler(handler);
        parser->parse();
        return_value = handler->get_text();
        delete handler;
    }
    else {
        PyErr_SetString(PyExc_ValueError, "bad DOC file");
    }

    return return_value;
}



static PyMethodDef doc_methods[] = {
    {"doc_to_text", (PyCFunction)doc_to_text, METH_VARARGS,
     "Return text contained in the DOC stored in 'data'.\n"
     "data: byte string of the DOC\n"
     "@return: unicode of textual content"},
    {NULL, NULL, 0, NULL} /* sentinel */
};

static struct PyModuleDef ModuleDef = {
    PyModuleDef_HEAD_INIT,
    "doctotext", /* name of module */
    "XXX\n", /* module documentation, may be NULL */
    -1,   /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    doc_methods
};


/* declarations for DLL import/export */
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

extern "C" PyMODINIT_FUNC initdoctotext(void) {
    PyObject *module = PyModule_Create(&ModuleDef);
    if (module == NULL) {
        return NULL;
    }

    if (!(DocRtfException = PyErr_NewException(
                    (char *)"doctotext.DocRtfException", NULL, NULL))) {
        goto err0;
    }
    Py_INCREF(DocRtfException);
    PyModule_AddObject(module, "DocRtfException", DocRtfException);

    if (!(separator = PyUnicode_DecodeUTF8(" ", 1, "ignore"))) {
        goto err1;
    }

    if (!(empty = PyUnicode_DecodeUTF8("", 0, "ignore"))) {
        goto err1;
    }
    return module;

err1:
    Py_DECREF(DocRtfException);
err0:
    PyErr_SetString(PyExc_MemoryError, "out of memory to initialize");
    Py_DECREF(module);
    return NULL;
}
