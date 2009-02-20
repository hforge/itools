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
#include <goo/gtypes.h>
#include <poppler/GlobalParams.h>
#include <poppler/Object.h>
#include <poppler/Stream.h>
#include <poppler/PDFDoc.h>
#include <poppler/TextOutputDev.h>
#include <string>

#define DECODE_ERROR_HANDLER "ignore"
// The biggest size seen was 452
#define STREAM_BUFFER_SIZE 1024
#define SEPARATOR " "



// Allocate a buffer to store the words for the callback
static char stream_buffer[STREAM_BUFFER_SIZE];



class MemStreamPython: public MemStream {
    public:
        MemStreamPython(char *bufA, Guint startA, Guint lengthA,
                        Object *dictA);
        ~MemStreamPython();
        PyObject *get_text();
        std::string *words;
};


MemStreamPython::MemStreamPython(char *bufA, Guint startA, Guint lengthA,
                                 Object *dictA):
        MemStream(bufA, startA, lengthA, dictA) {
    words = new std::string();
}


MemStreamPython::~MemStreamPython(void) {
    delete words;
}


PyObject *MemStreamPython::get_text(void) {
    PyObject *text;

    text = PyUnicode_DecodeUTF8(words->c_str(), words->size(),
                                DECODE_ERROR_HANDLER);
    return text;
}



static void text_output_func(void *stream, char *text, int len) {
    MemStreamPython *stream_out;
    std::string *words;

    stream_out = (MemStreamPython *)stream;
    words = stream_out->words;
    words->append(text, 0, len);
    words->append(SEPARATOR);
}



static PyObject *pdf_to_text(PyObject *self, PyObject *args) {
    const char *buffer_in;
    int size;
    MemStreamPython *stream_out;
    /* Python */
    PyObject *return_value = NULL;
    /* Poppler */
    Object obj_in, obj_out;
    PDFDoc *doc;
    TextOutputDev *text_out;

    if (!PyArg_ParseTuple(args, "s#", &buffer_in, &size)) {
        return NULL;
    }

    if (!size) {
        PyErr_SetString(PyExc_ValueError, "data is empty");
        goto err0;
    }

    obj_in.initNull();
    doc = new PDFDoc(new MemStream((char *)buffer_in, 0, size, &obj_in),
                     // owner password
                     NULL,
                     // user password
                     NULL);

    if (!doc->isOk()) {
        PyErr_SetString(PyExc_ValueError, "bad PDF file");
        goto err1;
    }

    obj_out.initNull();
    stream_out = new MemStreamPython(stream_buffer, 0, STREAM_BUFFER_SIZE,
                                     &obj_out);
    text_out = new TextOutputDev(text_output_func, stream_out,
                                 // maintain original physical layout
                                 gFalse,
                                 // keep strings in content stream order
                                 gFalse);
    if (!text_out->isOk()) {
        PyErr_SetString(PyExc_ValueError, "unable to convert to text");
        goto err2;
    }

    doc->displayPages(text_out, 1, doc->getNumPages(), 72, 72,
                      // rotate
                      0,
                      // use media box
                      gTrue,
                      // crop
                      gFalse,
                      // printing
                      gFalse);


    return_value = stream_out->get_text();

err2:
    delete text_out;
    // Has not deleted its stream
    delete stream_out;
err1:
    delete doc;
    // Has deleted its stream along
err0:

    return return_value;
}



static PyMethodDef pdf_methods[] = {
    {"pdf_to_text", pdf_to_text, METH_VARARGS,
     "Return text contained in the PDF stored in 'data'.\n"
     "data: byte string of the PDF\n"
     "@return: unicode of textual content"},
    {NULL, NULL, 0, NULL} /* sentinel */
};



/* declarations for DLL import/export */
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif

extern "C" PyMODINIT_FUNC initpdftotext(void) {
    PyObject *module;

    module = Py_InitModule("pdftotext", pdf_methods);
    if (module == NULL) {
        return;
    }

    globalParams = new GlobalParams();
    globalParams->setTextPageBreaks(gFalse);
    globalParams->setErrQuiet(gTrue);
}
