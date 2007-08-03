
#include <Python.h>
#include "structmember.h"
/* To call Python from C */
#include <import.h>
#include <graminit.h>
#include <pythonrun.h>

/* Tokens */
#define XML_DECL 0
#define DOCUMENT_TYPE 1
#define START_ELEMENT 2
#define END_ELEMENT 3
#define TEXT 4
#define COMMENT 5
#define PI 6
#define CDATA 7

/* Errors */
#define BAD_XML_DECL "XML declaration not well-formed: line %d, column %d"
#define INVALID_TOKEN "not well-formed (invalid token): line %d, column %d"
#define MISMATCH "mismatched tag: line %d, column %d"
#define BAD_ENTITY_REF "error parsing entity reference: line %d, column %d"
#define BAD_CHAR_REF "error parsing character reference: line %d, column %d"
#define DUP_ATTR "duplicate attribute: line %d, column %d"

#define ERROR(msg, line, column) PyErr_Format(XMLError, msg, line, column)

/* FIXME, limits to be removed */
#define TAG_STACK_SIZE 200 /* Maximum deepness of the element tree */
#define NS_INDEX_SIZE 10


/**************************************************************************
 * Global variables
 *************************************************************************/

/* Import from Python */
PyObject* p_htmlentitydefs;
PyObject* p_name2codepoint;


/* Exceptions */
static PyObject* XMLError;


/* Constants */
PyObject* xml_prefix;
PyObject* xml_ns;
PyObject* xmlns_prefix;
PyObject* xmlns_uri;



/**************************************************************************
 * The data structure below defines the parser state. 
 **************************************************************************/
typedef struct {
    PyObject_HEAD
    /* Specific fields */
    PyObject* data;
    char* cursor;
    int line_no;
    int column;
    /* Tag tag stack (used to check every open tag has a close tag) */
    PyObject* tag_stack[TAG_STACK_SIZE];
    int tag_stack_top;
    /* Namespace stack */
    PyObject* tag_ns_stack[TAG_STACK_SIZE]; /* FIXME: hardcoded limit */
    int tag_ns_index[NS_INDEX_SIZE]; /* FIXME: hardcoded limit */
    int tag_ns_index_top;
    PyObject* namespaces;
    PyObject* default_namespaces;
    /* The end tag in an empty element */
    PyObject* left_token; /* FIXME: hardcoded limit */
} Parser;


static void Parser_dealloc(Parser* self) {
    int idx;

    Py_XDECREF(self->data);
    for (idx=0; idx<self->tag_stack_top; idx++) {
        Py_DECREF(self->tag_stack[idx]);
        Py_XDECREF(self->tag_ns_stack[idx]);
    }

    Py_XDECREF(self->left_token);

    self->ob_type->tp_free((PyObject*)self);
}


static PyObject* Parser_new(PyTypeObject* type, PyObject* args, PyObject* kw) {
    Parser* self;

    /* Allocate memory */
    self = (Parser*)type->tp_alloc(type, 0);
    if (self == NULL)
        return NULL;

    self->data = NULL;
    self->cursor = NULL;
    self->line_no = 1;
    self->column = 1;
    self->tag_stack_top = 0;
    self->tag_ns_index_top = 0;
    self->namespaces = NULL;
    self->default_namespaces = NULL;
    self->left_token = NULL;

    return (PyObject*)self;
}


static int Parser_init(Parser* self, PyObject* args, PyObject* kw) {
    PyObject* data;
    PyObject* namespaces;
    int idx;

    /* Load the input data */
    namespaces = NULL;
    if (!PyArg_ParseTuple(args, "S|O!", &data, &PyDict_Type, &namespaces))
        return -1;

    Py_XDECREF(self->data);
    Py_INCREF(data);
    self->data = data;

    /* Initialize variables */
    self->cursor = PyString_AsString(data);
    self->line_no = 1;
    self->column = 1;

    /* The stacks are empty */
    for (idx=0; idx<self->tag_stack_top; idx++) {
        Py_DECREF(self->tag_stack[idx]);
        Py_XDECREF(self->tag_ns_stack[idx]);
    }
    self->tag_stack_top = 0;
    self->tag_ns_index_top = 0;

    /* For empty elements, "left_token" keeps the closing tag. */
    Py_XDECREF(self->left_token);
    self->left_token = NULL;

    /* Namespaces */
    self->namespaces = namespaces;
    Py_XDECREF(self->default_namespaces);
    Py_XINCREF(namespaces);
    self->default_namespaces = namespaces;

    return 0;
}


/* Merges two dictionaries into a new one, when conflict happens the second
 * dict has priority. The first dictionary, "a", maybe NULL, then the second
 * dictionary, "b", is returned.
 *
 * Returns a new reference. The reference count of the items from the
 * source dicts that get into the new dict are incremented.
 */
PyObject* merge_dicts(PyObject* a, PyObject* b) {
    PyObject* c;

    /* If "a" is NULL return b */
    if (a == NULL) {
        Py_INCREF(b);
        return b;
    }

    /* Make a copy of "a" */
    c = PyDict_Copy(a);
    if (c == NULL)
        return NULL;

    /* Update with "b" */
    if (PyDict_Update(c, b) == -1) {
        Py_DECREF(c);
        return NULL;
    }

    return c;
}


/* Adds a new tag to the tag stack. Updates the namespaces structure.
 *
 * We take ownership of "value". */
int push_tag(Parser* self, PyObject* value, PyObject* namespaces) {
    PyObject* new_namespaces;

    if (self->tag_stack_top >= TAG_STACK_SIZE)
        return -1;

    if (PyDict_Size(namespaces)) {
        if (self->tag_ns_index_top >= NS_INDEX_SIZE)
            return -1;
        /* Create the new namespaces */
        new_namespaces = merge_dicts(self->namespaces, namespaces);
        if (new_namespaces == NULL)
            return -1;
        /* Update the current namespaces */
        self->namespaces = new_namespaces;
        /* Update ns index */
        self->tag_ns_index[self->tag_ns_index_top] = self->tag_stack_top;
        self->tag_ns_index_top++;
    } else
        new_namespaces = NULL;

    Py_INCREF(value);
    self->tag_stack[self->tag_stack_top] = value;
    self->tag_ns_stack[self->tag_stack_top] = new_namespaces;
    self->tag_stack_top++;

    return 0;
}


/* Pops the given tag, if it matches the last tag in the stack. Otherwise
 * return an error condition.
 * 
 * Steals the reference to "value". Returns a new reference. */
PyObject* pop_tag(Parser* self, PyObject* value) {
    PyObject* last_open_tag;
    PyObject* namespaces;
    PyObject* prefix;
    PyObject* uri;
    PyObject* name;
    PyObject* result;

    /* Check the stack is not empty */
    if (self->tag_stack_top == 0) {
        Py_DECREF(value);
        return NULL;
    }

    /* Pop the top value from the stack */
    self->tag_stack_top--;
    last_open_tag = self->tag_stack[self->tag_stack_top];
    namespaces = self->tag_ns_stack[self->tag_stack_top];

    /* Check the values match */
    if (PyObject_Compare(value, last_open_tag)) {
        Py_DECREF(value);
        Py_DECREF(last_open_tag);
        Py_XDECREF(namespaces);
        return NULL;
    }

    /* Don't need the "last_open_tag" anymore */
    Py_DECREF(last_open_tag);

    /* Find out the URI from the prefix */
    prefix = PyTuple_GetItem(value, 0);
    if (self->namespaces == NULL)
        uri = Py_None;
    else if (PyDict_Contains(self->namespaces, prefix)) {
        uri = PyDict_GetItem(self->namespaces, prefix);
        if (uri == NULL) {
            Py_DECREF(value);
            Py_XDECREF(namespaces);
            return NULL;
        }
    } else
        uri = Py_None;

    /* Build the return value */
    name = PyTuple_GetItem(value, 1);
    result = Py_BuildValue("(OO)", uri, name);

    /* Update the namespaces data structure if needed */
    if (namespaces) {
        self->tag_ns_index_top--;
        self->namespaces = self->tag_ns_stack[self->tag_ns_index[self->tag_ns_index_top - 1]];
        Py_DECREF(namespaces);
    } else if (self->tag_ns_index_top == 0) {
        self->namespaces = self->default_namespaces;
    }

    Py_DECREF(value);
    return result;
}


/**************************************************************************
 * The parsing code
 **************************************************************************/

/* Move forward the cursor  */
void move_cursor(Parser* self) {
    if (*(self->cursor) == '\n') {
        self->line_no++;
        self->column = 1;
    } else
        self->column++;

    self->cursor++;
}


/* Tests wether the following data matches the "expected" string, and moves
 * the cursor forward if that is the case (updates the "column" index). The
 * variable "expected" must not contain new lines, the "line_no" index is
 * not updated. */
int read_string(Parser* self, char* expected) {
    int size;

    size = strlen(expected);
    if (strncmp(self->cursor, expected, size))
        return -1;

    self->cursor += size;
    self->column += size;
    return 0;
}


/* Name (http://www.w3.org/TR/REC-xml/#NT-Name)
 *
 * Returns a new reference. */
PyObject* xml_name(Parser* self) {
    int size;
    char c;
    char* base;

    /* First character must be a letter */
    c = *(self->cursor);
    if (!isalpha(c))
        return NULL;

    /* Get the value */
    base = self->cursor;
    self->cursor++;
    self->column++;
    for (size=1; 1; size++, self->cursor++, self->column++) {
        c = *(self->cursor);
        if (isalnum(c))
            continue;
        if ((c == '.') || (c == '-') || (c == '_') || (c == ':'))
            continue;
        break;
    }

    /* Update the state */
    return Py_BuildValue("s#", base, size);
}


/* Prefix + Name (http://www.w3.org/TR/REC-xml-names/#ns-decl)
 *
 * Returns a new reference. */
PyObject* xml_prefix_name(Parser* self) {
    char c;
    char* base;
    int size;
    PyObject* name;

    /* First character must be a letter */
    c = *(self->cursor);
    if (!isalpha(c))
        return NULL;

    /* Get the value */
    base = self->cursor;
    self->cursor++;
    self->column++;
    for (size=1; 1; size++, move_cursor(self)) {
        c = *(self->cursor);
        if (isalnum(c))
            continue;
        if ((c == '.') || (c == '-') || (c == '_'))
            continue;
        break;
    }

    if (c == ':') {
        /* With prefix */
        self->cursor++;
        self->column++;
        name = xml_name(self);
        if (name == NULL)
            return NULL;
        return Py_BuildValue("(s#N)", base, size, name);
    }

    /* No Prefix */
    return Py_BuildValue("(Os#)", Py_None, base, size);
}


/* White Space (http://www.w3.org/TR/REC-xml/#NT-S) */
int xml_space(Parser* self) {
    for (; isspace(*(self->cursor)); move_cursor(self));
    return 0;
}


/* Equal (http://www.w3.org/TR/REC-xml/#NT-Eq) */
int xml_equal(Parser* self) {
    /* White Space */
    for (; isspace(*(self->cursor)); move_cursor(self));
    /* Equal */
    if (*(self->cursor) != '=')
        return -1;
    move_cursor(self);
    /* White Space */
    for (; isspace(*(self->cursor)); move_cursor(self));
    return 0;
}

/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-EntityRef)
 *
 * Returns a new reference. */
PyObject* xml_entity_reference(Parser* self) {
    PyObject* value;
    PyObject* cp;
    PyObject* u_char;

    /* Read the name */
    value = xml_name(self);
    if (value == NULL)
        return NULL;

    /* Read ";" */
    if (*(self->cursor) != ';') {
        Py_DECREF(value);
        return NULL;
    }
    self->cursor++;
    self->column++;

    /* To codepoint */
    /* XXX Specific to HTML */
    /* htmlentitydefs.name2unicodepoint[value] */
    cp = PyDict_GetItem(p_name2codepoint, value);
    Py_DECREF(value);
    if (cp == NULL)
        return NULL;

    /* unichr(codepoint) */
    u_char = PyUnicode_FromOrdinal(PyInt_AS_LONG(cp));

    /* value.encode('utf-8') */
    value = PyUnicode_AsUTF8String(u_char);
    Py_DECREF(u_char);

    return value;
}

/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-CharRef)
 *
 * Returns a new reference. */
PyObject* xml_char_reference(Parser* self) {
    int cp = 0;
    char c;
    PyObject* u_char;
    PyObject* value;

    c = *(self->cursor);
    if (c == 'x') {
        /* Read "x" */
        self->cursor++;
        self->column++;
        /* Check there is ate least one digit */
        c = *(self->cursor);
        if (!isxdigit(c))
            return NULL;
        /* Hex */
        for (; 1; self->cursor++, self->column++) {
            c = *(self->cursor);
            if (c == ';')
                break;
            /* Decode char */
            cp = cp * 16;
            if (c >= '0' && c <= '9')
                cp = cp + (c - '0');
            else if (c >= 'A' && c <= 'F')
                cp = cp + (c - 'A') + 10;
            else if (c >= 'a' && c <= 'f')
                cp = cp + (c - 'a') + 10;
            else
                return NULL;
        }
    } else {
        /* Check there is ate least one digit */
        if (!isdigit(c)) {
            return NULL;
        }
        /* Dec */
        for (; 1; self->cursor++, self->column++) {
            c = *(self->cursor);
            if (c == ';')
                break;
            /* Decode char */
            cp = cp * 10;
            if (c >= '0' && c <= '9')
                cp = cp + (c - '0');
            else
                return NULL;
        }
    }

    /* Read ";" */
    self->cursor++;
    self->column++;

    /* unichr(codepoint) */
    u_char = PyUnicode_FromOrdinal(cp);
    /* value.encode('utf-8') */
    value = PyUnicode_AsUTF8String(u_char);
    Py_DECREF(u_char);

    return value;
}



/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-AttValue)
 *
 * Returns a new reference. */
PyObject* xml_attr_value(Parser* self) {
    PyObject* aux = NULL;
    PyObject* result = NULL;
    PyObject* ref;
    char delimiter;
    char* base;
    int size;

    /* The heading quote */
    delimiter = *(self->cursor);
    if ((delimiter != '"') && (delimiter != '\''))
        return NULL;

    self->cursor++;
    self->column++;

    /* The value */
    base = self->cursor;
    for (size=0; 1;) {
        char c = *(self->cursor);

        /* Stop */
        if (c == delimiter)
            break;

        /* Forbidden characters */
        if ((c == '\0') || (c == '<'))
            return NULL;

        /* Entity or Character Reference */
        if (c == '&') {
            self->cursor++;
            self->column++;
            if (*(self->cursor) == '#') {
                self->cursor++;
                self->column++;
                ref = xml_char_reference(self);
                if (ref == NULL)
                    return NULL;
            } else {
                ref = xml_entity_reference(self);
                if (ref == NULL)
                    return NULL;
            }
            /* result = result + buffer */
            if (size > 0) {
                aux = Py_BuildValue("s#", base, size);
                if (result == NULL) {
                    result = aux;
                } else {
                    PyString_ConcatAndDel(&result, aux);
                }
            }
            /* result = result + reference */
            if (result == NULL) {
                result = ref;
            } else {
                PyString_ConcatAndDel(&result, ref);
            }
            /* Reset */
            base = self->cursor;
            size = 0;
        } else {
            size++;
            move_cursor(self);
        }
    }

    /* Read delimiter */
    self->cursor++;
    self->column++;

    /* Post-process */
    if (result == NULL)
        return Py_BuildValue("s#", base, size);

    aux = Py_BuildValue("s#", base, size);
    PyString_ConcatAndDel(&result, aux);

    return result;
}



/* Document Type
 *
 * Return a new reference. */
PyObject* parse_document_type(Parser* self) {
    PyObject* public_id;
    PyObject* system_id;
    PyObject* has_internal_subset;
    char c;
    PyObject* name;

    if (read_string(self, "DOCTYPE"))
        return NULL;
    xml_space(self);

    /* Name */
    name = xml_name(self);
    if (name == NULL)
        return NULL;
    xml_space(self);
    /* External ID */
    c = *(self->cursor);
    if (c == 'S') {
        if (read_string(self, "SYSTEM")) {
            Py_DECREF(name);
            return NULL;
        }
        xml_space(self);
        /* PUBLIC ID */
        public_id = Py_None;
        /* SYSTEM ID */
        system_id = xml_attr_value(self);
        if (system_id == NULL) {
            Py_DECREF(name);
            return NULL;
        }
        Py_INCREF(public_id);
    } else if (c == 'P') {
        if (read_string(self, "PUBLIC")) {
            Py_DECREF(name);
            return NULL;
        }
        xml_space(self);
        /* PUBLIC ID */
        public_id = xml_attr_value(self);
        if (public_id == NULL) {
            Py_DECREF(name);
            return NULL;
        }
        xml_space(self);
        /* SYSTEM ID */
        system_id = xml_attr_value(self);
        if (system_id == NULL) {
            Py_DECREF(name);
            Py_DECREF(public_id);
            return NULL;
        }
    } else {
        Py_DECREF(name);
        return NULL;
    }
    /* White Space */
    xml_space(self);
    /* Internal subset */
    c = *(self->cursor);
    if (c == '[') {
        /* XXX NOT IMPLEMENTED*/
        Py_DECREF(name);
        Py_DECREF(public_id);
        Py_DECREF(system_id);
        PyErr_SetString(PyExc_NotImplementedError,
                        "internal subset not yet supported");
        return NULL;
    } else
        has_internal_subset = Py_None;
    /* End doctype declaration */
    if (c != '>') {
        Py_DECREF(name);
        Py_DECREF(public_id);
        Py_DECREF(system_id);
        return NULL;
    }

    self->cursor++;
    self->column++;

    return Py_BuildValue("(NNNO)", name, system_id, public_id,
                         has_internal_subset);
}


/* Returns a new reference */
static PyObject* Parser_iternext(Parser* self) {
    int size;
    char* base;
    PyObject* value;
    PyObject* tag;
    PyObject* tag_prefix;
    PyObject* tag_uri;
    PyObject* tag_name;
    int end_tag;
    PyObject* result;
    /* Attributes */
    PyObject* attr;
    PyObject* attr_name;
    PyObject* attr_prefix;
    PyObject* attr_uri;
    PyObject* attr_value;
    PyObject* attributes_list;
    PyObject* namespace_decls;
    PyObject* namespaces;
    /* XML declaration */
    PyObject* version;
    PyObject* encoding;
    PyObject* standalone;
    char c;
    int line;
    int column;
    PyObject* attributes;
    int attributes_n;
    int idx;

    /* There are tokens waiting */
    if (self->left_token) {
        value = self->left_token;
        self->left_token = NULL;
        return value;
    }

    /* Check for EOF */
    /* FIXME, there are many places else we must check for EOF */
    c = *(self->cursor);
    if (c == '\0')
        return NULL;

    line = self->line_no;
    column = self->column;

    if (c == '<') {
        self->cursor++;
        self->column++;
        c = *(self->cursor);
        if (c == '/') {
            /* End Element (http://www.w3.org/TR/REC-xml/#NT-ETag) */
            self->cursor++;
            self->column++;
            /* Name */
            value = xml_prefix_name(self);
            if (value == NULL)
                return ERROR(INVALID_TOKEN, line, column);
            /* White Space */
            xml_space(self);
            /* Close */
            if (*(self->cursor) != '>') {
                Py_DECREF(value);
                return ERROR(INVALID_TOKEN, line, column);
            }
            self->cursor++;
            self->column++;
            /* Remove from the stack */
            value = pop_tag(self, value);
            if (value == NULL)
                return ERROR(MISMATCH, line, column);
 
            return Py_BuildValue("(iNi)", END_ELEMENT, value, line);
        } else if (c == '!') {
            /* "<!" */
            self->cursor++;
            self->column++;
            c = *(self->cursor);
            if (c == '-') {
                /* "<!-" */
                self->cursor++;
                self->column++;
                c = *(self->cursor);
                if (c != '-')
                    return ERROR(INVALID_TOKEN, line, column);

                /* Comment (http://www.w3.org/TR/REC-xml/#dt-comment) */
                self->cursor++;
                self->column++;
                base = self->cursor;
                for (size=0; 1; size++, move_cursor(self)) {
                    if (self->cursor[0] != '-')
                        continue;
                    if (self->cursor[1] != '-')
                        continue;

                    if (self->cursor[2] != '>')
                        return ERROR(INVALID_TOKEN, line, column);

                    self->cursor += 3;
                    self->column += 3;
                    return Py_BuildValue("(is#i)", COMMENT, base, size, line);
                }
            } else if (c == 'D') {
                /* Document Type */
                value = parse_document_type(self);
                if (value == NULL)
                    return ERROR(INVALID_TOKEN, line, column);
                return Py_BuildValue("(iNi)", DOCUMENT_TYPE, value, line);
            } else if (c == '[') {
                /* CData section */
                if (read_string(self, "[CDATA["))
                    return ERROR(INVALID_TOKEN, line, column);
                base = self->cursor;
                for (size=0; strncmp(self->cursor, "]]>", 3); size++, move_cursor(self));
                self->cursor += 3;
                self->column += 3;
                return Py_BuildValue("is#i", CDATA, base, size, line);
            } else
                return ERROR(INVALID_TOKEN, line, column);
        } else if (c == '?') {
            /* Processing Instruction (http://www.w3.org/TR/REC-xml/#dt-pi) */
            self->cursor++;
            self->column++;
            /* Target */
            if (!(strncmp(self->cursor, "xml", 3)) && isspace(self->cursor[3])) {
                /* XML decl (http://www.w3.org/TR/REC-xml/#NT-XMLDecl) */
                self->cursor += 3;
                self->column += 3;
                xml_space(self);
                /* The version */
                if (read_string(self, "version") == -1)
                    return ERROR(BAD_XML_DECL, line, column);
                if (xml_equal(self) == -1)
                    return ERROR(BAD_XML_DECL, line, column);
                version = xml_attr_value(self);
                if (version == NULL)
                    return ERROR(BAD_XML_DECL, line, column);
                xml_space(self);
                /* Encoding & Standalone */
                encoding = Py_BuildValue("s", "utf-8");
                standalone = Py_BuildValue("");
                if (strncmp(self->cursor, "?>", 2)) {
                    Py_DECREF(encoding);
                    /* Encoding */
                    if (read_string(self, "encoding") == -1) {
                        Py_DECREF(version);
                        Py_DECREF(standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    if (xml_equal(self) == -1) {
                        Py_DECREF(version);
                        Py_DECREF(standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    encoding = xml_attr_value(self);
                    if (encoding == NULL) {
                        Py_DECREF(version);
                        Py_DECREF(standalone);
                        return ERROR(BAD_XML_DECL, line, column);
                    }
                    xml_space(self);
                    if (strncmp(self->cursor, "?>", 2)) {
                        Py_DECREF(standalone);
                        /* Standalone */
                        if (read_string(self, "standalone") == -1) {
                            Py_DECREF(version);
                            Py_DECREF(encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        if (xml_equal(self) == -1) {
                            Py_DECREF(version);
                            Py_DECREF(encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        standalone = xml_attr_value(self);
                        if (standalone == NULL) {
                            Py_DECREF(version);
                            Py_DECREF(encoding);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                        xml_space(self);
                        if (strncmp(self->cursor, "?>", 2)) {
                            Py_DECREF(version);
                            Py_DECREF(encoding);
                            Py_DECREF(standalone);
                            return ERROR(BAD_XML_DECL, line, column);
                        }
                    }
                }
                self->cursor += 2;
                self->column += 2;
                return Py_BuildValue("(i(NNN)i)", XML_DECL, version, encoding,
                                     standalone, line);
            } else {
                value = xml_name(self);
                if (value == NULL)
                    return ERROR(INVALID_TOKEN, line, column);
                /* White Space */
                xml_space(self);
                /* Value */
                base = self->cursor;
                for (size=0; 1; size++, move_cursor(self))
                    if ((self->cursor[0] == '?') && (self->cursor[1] == '>'))
                        break;
                self->cursor += 2;
                return Py_BuildValue("(i(Ns#)i)", PI, value, base, size, line);
            }
        } else {
            /* Start Element */
            /* Name */
            tag = xml_prefix_name(self);
            if (tag == NULL)
                return ERROR(INVALID_TOKEN, line, column);
            tag_prefix = PyTuple_GetItem(tag, 0);
            /* Attributes */
            attributes_list = PyList_New(0);
            namespace_decls = PyDict_New();
            while (1) {
                xml_space(self);
                c = *(self->cursor);
                if (c == '>') {
                    self->cursor++;
                    self->column++;
                    /* Add to the stack */
                    if (push_tag(self, tag, namespace_decls) == -1) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return PyErr_Format(PyExc_RuntimeError,
                                            "internal error");
                    }

                    end_tag = 0;
                    namespaces = self->namespaces;
                    Py_XINCREF(namespaces);
                    break;
                } else if (c == '/') {
                    self->cursor++;
                    self->column++;
                    if (*(self->cursor) != '>') {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    self->cursor++;
                    self->column++;

                    end_tag = 1;
                    if (PyDict_Size(namespace_decls))
                        namespaces = merge_dicts(self->namespaces, namespace_decls);
                    else {
                        namespaces = self->namespaces;
                        Py_XINCREF(namespaces);
                    }

                    break;
                }
                /* Attributes */
                if (!(strncmp(self->cursor, "xmlns:", 6))) {
                    /* Namespace declaration */
                    self->cursor += 6;
                    self->column += 6;
                    /* The prefix */
                    attr_name = xml_name(self);
                    if (attr_name == NULL) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* The URI */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Check for duplicates */
                    if (PyDict_Contains(namespace_decls, attr_name)) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        Py_DECREF(attr_value);
                        return ERROR(DUP_ATTR, line, column);
                    }
                    /* Set the namespace */
                    PyDict_SetItem(namespace_decls, attr_name, attr_value);
                    /* Set the attribute */
                    attr = Py_BuildValue("((OO)N)", xmlns_prefix, attr_name,
                                         attr_value);
                    PyList_Append(attributes_list, attr);
                    /* Decref */
                    Py_DECREF(attr);
                } else if ((!(strncmp(self->cursor, "xmlns", 5)))
                           && ((self->cursor[5] == '=')
                               || (isspace(self->cursor[5])))) {
                    /* Default namespace declaration */
                    self->cursor += 5;
                    self->column += 5;
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* The URI */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Check for duplicates */
                    if (PyDict_Contains(namespace_decls, Py_None)) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_value);
                        return ERROR(DUP_ATTR, line, column);
                    }
                    /* Set the default namespace */
                    PyDict_SetItem(namespace_decls, Py_None, attr_value);
                    /* Set the attribute */
                    attr = Py_BuildValue("((OO)N)", xmlns_prefix, Py_None,
                                         attr_value);
                    PyList_Append(attributes_list, attr);
                    /* Decref */
                    Py_DECREF(attr);
                } else {
                    /* Attribute */
                    attr_name = xml_prefix_name(self);
                    if (attr_name == NULL) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Eq */
                    if (xml_equal(self) == -1) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Value */
                    attr_value = xml_attr_value(self);
                    if (attr_value == NULL) {
                        Py_DECREF(tag);
                        Py_DECREF(attributes_list);
                        Py_DECREF(namespace_decls);
                        Py_DECREF(attr_name);
                        return ERROR(INVALID_TOKEN, line, column);
                    }
                    /* Set the attribute */
                    attr_prefix = PyTuple_GetItem(attr_name, 0);
                    if (PyObject_Compare(attr_prefix, Py_None) == 0) {
                        Py_INCREF(tag_prefix);
                        PyTuple_SetItem(attr_name, 0, tag_prefix);
                    }
                    attr = Py_BuildValue("(NN)", attr_name, attr_value);
                    PyList_Append(attributes_list, attr);
                    Py_DECREF(attr);
                }
            }

            /* Tag */
            if (namespaces == NULL)
                tag_uri = Py_None;
            else {
                tag_uri = PyDict_GetItem(namespaces, tag_prefix);
                if (tag_uri == NULL)
                    tag_uri = Py_None;
            }
            tag_name = PyTuple_GetItem(tag, 1);

            /* The END_ELEMENT token will be sent later */
            if (end_tag)
                self->left_token = Py_BuildValue("(i(OO)i)", END_ELEMENT,
                                                 tag_uri, tag_name, line);

            /* Attributes */
            attributes = PyDict_New();
            attributes_n = PyList_Size(attributes_list);
            for (idx=0; idx < attributes_n; idx++) {
                attr = PyList_GetItem(attributes_list, idx);
                /* Find out the attribute URI */
                attr_name = PyTuple_GetItem(attr, 0);
                attr_prefix = PyTuple_GetItem(attr_name, 0);
                if (PyObject_Compare(attr_prefix, xml_prefix) == 0)
                    attr_uri = xml_ns;
                else if (PyObject_Compare(attr_prefix, xmlns_prefix) == 0)
                    attr_uri = xmlns_uri;
                else if (namespaces == NULL)
                    attr_uri = Py_None;
                else {
                    attr_uri = PyDict_GetItem(namespaces, attr_prefix);
                    if (attr_uri == NULL)
                        attr_uri = Py_None;
                }
                /* Find out the attribute name */
                attr_name = PyTuple_GetItem(attr_name, 1);
                /* Find out the attribute value */
                attr_value = PyTuple_GetItem(attr, 1);
                /* Check for duplicates */
                attr_name = Py_BuildValue("(OO)", attr_uri, attr_name);
                if (PyDict_Contains(attributes, attr_name)) {
                    Py_DECREF(attr_name);
                    Py_DECREF(tag);
                    Py_DECREF(attributes_list);
                    Py_DECREF(namespace_decls);
                    Py_DECREF(attributes);
                    Py_XDECREF(namespaces);
                    return ERROR(DUP_ATTR, line, column);
                }
                /* Update the dict */
                PyDict_SetItem(attributes, attr_name, attr_value);
                Py_DECREF(attr_name);
            }

            result = Py_BuildValue("(i(OON)i)", START_ELEMENT, tag_uri,
                                   tag_name, attributes, line);
            Py_DECREF(tag);
            Py_DECREF(attributes_list);
            Py_DECREF(namespace_decls);
            return result;
        }
    } else if (c == '&') {
        self->cursor++;
        self->column++;
        if (*(self->cursor) == '#') {
            /* Character reference */
            self->cursor++;
            self->column++;
            value = xml_char_reference(self);
            if (value == NULL)
                return ERROR(BAD_CHAR_REF, line, column);
            return Py_BuildValue("(iNi)", TEXT, value, line);
        } else {
            /* Entity reference */
            value = xml_entity_reference(self);
            if (value == NULL)
                return ERROR(BAD_ENTITY_REF, line, column);
            return Py_BuildValue("(iNi)", TEXT, value, line);
        }
    } else {
        /* Text */
        base = self->cursor;
        for (size = 0; 1; size++, move_cursor(self)) {
            c = *(self->cursor);
            if ((c == '<') || (c == '&') || (c == '\0'))
                break;
        }
        return Py_BuildValue("(is#i)", TEXT, base, size, line);
    }

    /* Return None (just to avoid the compiler to complain) */
    return NULL;
}


/**************************************************************************
 * The Parser Type
 * ***********************************************************************/
static PyMemberDef Parser_members[] = {
    {"line_no", T_INT, offsetof(Parser, line_no), 0, "Line number"},
    {"column", T_INT, offsetof(Parser, column), 0, "Column"},
    {NULL}
};


static PyMethodDef Parser_methods[] = {
    {NULL, NULL, 0, NULL}
};


static PyTypeObject ParserType = {
    PyObject_HEAD_INIT(NULL)
    0,                              /* ob_size */
    "itools.xml.parser.Parser",     /* tp_name */
    sizeof(Parser),                 /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor)Parser_dealloc,     /* tp_dealloc */
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
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    "XML Parser",                   /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    0,                              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0, /* XXX set later: PyObject_SelfIter, */     /*tp_iter*/
    (iternextfunc)Parser_iternext,  /* tp_iternext */
    Parser_methods,                 /* tp_methods */
    Parser_members,                 /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    (initproc)Parser_init,          /* tp_init */
    0,                              /* tp_alloc */
    Parser_new,                     /* tp_new */
};


/**************************************************************************
 * Initialize the module
 * ***********************************************************************/

static PyMethodDef module_methods[] = {
    /* {"method name", method, METH_VARARGS | METH_KEYWORDS | METH_NOARGS,
        "doc string"} */
    {NULL}
};

  
#ifndef PyMODINIT_FUNC    /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
initparser(void) {
    PyObject* module;

    /* XXX Fix tp_Iter for cygwin */
    ParserType.tp_iter = PyObject_SelfIter;

    if (PyType_Ready(&ParserType) < 0)
        return;

    /* Import from Python */
    /* from htmlentitydefs import name2codepoint */
    p_htmlentitydefs = PyImport_ImportModule("htmlentitydefs");
    p_name2codepoint = PyObject_GetAttrString(p_htmlentitydefs, "name2codepoint");

    /* Constants */
    xml_prefix = PyString_FromString("xml");
    xml_ns = PyString_FromString("http://www.w3.org/XML/1998/namespace");
    xmlns_prefix = PyString_FromString("xmlns");
    xmlns_uri = PyString_FromString("http://www.w3.org/2000/xmlns/");

    /* Initialize the module */
    module = Py_InitModule3("parser", module_methods, "Low-level XML parser");
    if (module == NULL)
        return;

    /* Register types */
    Py_INCREF(&ParserType);
    PyModule_AddObject(module, "Parser", (PyObject *)&ParserType);

    /* Register exceptions */
    XMLError = PyErr_NewException("itools.xml.parser.XMLError", NULL, NULL);
    Py_INCREF(XMLError);
    PyModule_AddObject(module, "XMLError", XMLError);

    /* Register constants */
    PyModule_AddIntConstant(module, "XML_DECL", XML_DECL);
    PyModule_AddIntConstant(module, "DOCUMENT_TYPE", DOCUMENT_TYPE);
    PyModule_AddIntConstant(module, "START_ELEMENT", START_ELEMENT);
    PyModule_AddIntConstant(module, "END_ELEMENT", END_ELEMENT);
    PyModule_AddIntConstant(module, "TEXT", TEXT);
    PyModule_AddIntConstant(module, "COMMENT", COMMENT);
    PyModule_AddIntConstant(module, "PI", PI);
    PyModule_AddIntConstant(module, "CDATA", CDATA);
}

