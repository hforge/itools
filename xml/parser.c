/*
 * Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

/* The GLib */
#include <glib.h>
/* Python */
#include <Python.h>
#include "structmember.h"

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
#define MISSING "expected end tag is missing: line %d, column %d"
#define BAD_ENTITY_REF "error parsing entity reference: line %d, column %d"
#define BAD_CHAR_REF "error parsing character reference: line %d, column %d"
#define DUP_ATTR "duplicate attribute: line %d, column %d"

#define ERROR(msg, line, column) PyErr_Format(XMLError, msg, line, column)

/* Other Constants and Macros */
#define BUFFER_SIZE 512
#define IS_NC_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_'))
#define IS_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_') || (c == ':'))


/* For compatibility with Python 2.4 */
#if PY_MINOR_VERSION == 4
typedef int Py_ssize_t;
#endif


/* Errors */
static PyObject* XMLError;


/**************************************************************************
 * Data Types
 *************************************************************************/

/* This type defines an start tag by its prefix and name, plus a boolean value
 * that says whether the tag includes XML namespace declarations (true) or not
 * (false). */
typedef struct {
    gchar* prefix;       /* Stored in "self->ns_prefixes". */
    gchar* name;         /* Stored apart (malloc/free). */
    gboolean has_xmlns;
} StartTag;


/* This type represents an attribute. */
typedef struct {
    gchar* prefix;  /* The prefix is stored in "self->ns_prefixes". */
    GString* name;  /* The name is kept apart. */
    GString* value; /* The value is kept apart. */
} Attribute;


/* The data structure below defines the parser state. */
typedef struct {
    PyObject_HEAD
    /* The Source. */
    PyObject* py_source;         /* The source, a Python string or file. */
    char* cursor;                /* If src is str: points to the next char. */
    FILE* file;                  /* If src is file: the C file */
    char file_buffer[BUFFER_SIZE];
    int file_buffer_index;
    char (*read_char)(gpointer); /* Function to read the next char. */
    char next_char;
    /* Where we are. */
    guint line_no;
    guint column;
    /* The stack and namespaces. */
    GArray* tag_stack;           /* The stack of open tags not yet closed. */
    GArray* ns_stack;            /* The stack of XML namespaces. */
    GHashTable* ns_default;      /* The default namespace (from Python). */
    GHashTable* ns_current;      /* A pointer to the current namespace. */
    GHashTable* ns_buffer;
    /* Interned strings. */
    GStringChunk* ns_prefixes;   /* Keep the namespace prefixes. */
    GStringChunk* ns_uris;       /* Keep the namespace URIs. */
    /* Other variables. */
    PyObject* py_left_token;     /* The end tag of an empty element. */
    GPtrArray* attributes;       /* Keep the attributes of an element. */
    GString* buffer;
} Parser;


/**************************************************************************
 * The C base.
 *************************************************************************/

char read_char_from_file(gpointer parser) {
    Parser* self;
    char c;
    int n;

    self = (Parser*)parser;
    /* Read if needed. */
    if (self->file_buffer_index == BUFFER_SIZE) {
        n = fread(self->file_buffer, sizeof(char), BUFFER_SIZE, self->file);
        if (n < BUFFER_SIZE)
            self->file_buffer[n] = '\0';
        self->file_buffer_index = 0;
    }

    c = self->file_buffer[self->file_buffer_index];
    self->file_buffer_index++;
    self->next_char = c;
    return c;
}


char read_char_from_string(gpointer parser) {
    Parser* self;
    char c;

    self = (Parser*)parser;
    c = *(self->cursor);
    self->cursor++;

    self->next_char = c;
    return c;
}


char move_cursor(Parser* self) {
    char c;

    c = (*(self->read_char))(self);

    /* Check newline. */
    if (c == '\n') {
        self->line_no++;
        self->column = 1;
    } else
        self->column++;

    return c;
}


Attribute* new_attribute(void) {
    Attribute* attribute;

    attribute = malloc(sizeof(Attribute));
    attribute->name = g_string_sized_new(10);
    attribute->value = g_string_sized_new(64);

    return attribute;
}


void free_attribute(Attribute* attribute) {
    g_string_free(attribute->name, TRUE);
    g_string_free(attribute->value, TRUE);
    free(attribute);
}


void reset_attributes(GPtrArray* attributes) {
    Attribute* attribute;
    guint index;

    for (index=0; index < attributes->len; index++) {
        attribute = g_ptr_array_index(attributes, index);
        free_attribute(attribute);
    }
    g_ptr_array_set_size(attributes, 0);
}


/* Built-in entity references */
GHashTable* builtin_entities;

#define SET_ENTITY(str, codepoint) \
    g_hash_table_insert(builtin_entities, str, GUINT_TO_POINTER(codepoint))


/*
http://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references
*/
void init_builtin_entities(void) {
    int index;
    char* html_entities[] = {
        "nbsp", "iexcl", "cent", "pound", "curren", "yen", "brvbar", "sect",
        "uml", "copy", "ordf", "laquo", "not", "shy", "reg", "macr", "deg",
        "plusmn", "sup2", "sup3", "acute", "micro", "para", "middot", "cedil",
        "sup1", "ordm", "raquo", "frac14", "frac12", "frac34", "iquest",
        "Agrave", "Aacute", "Acirc", "Atilde", "Auml", "Aring", "AElig",
        "Ccedil", "Egrave", "Eacute", "Ecirc", "Euml", "Igrave", "Iacute",
        "Icirc", "Iuml", "ETH", "Ntilde", "Ograve", "Oacute", "Ocirc",
        "Otilde", "Ouml", "times", "Oslash", "Ugrave", "Uacute", "Ucirc",
        "Uuml", "Yacute", "THORN", "szlig", "agrave", "aacute", "acirc",
        "atilde", "auml", "aring", "aelig", "ccedil", "egrave", "eacute",
        "ecirc", "euml", "igrave", "iacute", "icirc", "iuml", "eth", "ntilde",
        "ograve", "oacute", "ocirc", "otilde", "ouml", "divide", "oslash",
        "ugrave", "uacute", "ucirc", "uuml", "yacute", "thorn", "yuml"};

    builtin_entities = g_hash_table_new(g_str_hash, g_str_equal);
    /* XML */
    SET_ENTITY("quot", 34);
    SET_ENTITY("amp", 38);
    SET_ENTITY("apos", 39);
    SET_ENTITY("lt", 60);
    SET_ENTITY("gt", 62);
    /* HTML 2.0 & 3.2 */
    for (index=160; index <= 255; index++)
        SET_ENTITY(html_entities[index-160], index);
    /* HTML 4.0 (TODO Finish) */
    SET_ENTITY("rArr", 8658);
}



/* Updates a given hash table with the contents of another hash table.
 * The second hash table may be NULL, then the first hash table remains
 * untouched.
 */
void update_dict(GHashTable* a, GHashTable* b) {
    GList* keys;
    GList* item;
    gchar* key;
    gchar* value;

    if (b == NULL)
        return;

    keys = g_hash_table_get_keys(b);
    item = keys;
    while (item != NULL) {
        key = (gchar*)item->data;
        value = g_hash_table_lookup(b, key);
        g_hash_table_insert(a, key, value);
        item = g_list_next(item);
    }
    g_list_free(keys);
}


/* Merges two hash tables into a new one, when conflict happens the second
 * hash table has priority.  Any of the given hash tables may be NULL.
 */
GHashTable* merge_dicts(GHashTable* a, GHashTable* b) {
    GHashTable* c;

    /* Create a new dict. */
    c = g_hash_table_new(g_str_hash, g_str_equal);

    /* Update with the content of "a". */
    if (a != NULL)
        update_dict(c, a);

    /* Update with the content of "b". */
    if (b != NULL)
        update_dict(c, b);

    /* Return */
    return c;
}


/* Adds a new tag to the tag stack, where a tag is defined by a couple of
 * sub-strings (tag prefix and name).  Updates the namespaces structure.
 *
 * Returns a new Python value, a tuple of the prefix and name. */
void push_tag(Parser* self, gchar* prefix, gchar* name) {
    GHashTable* new_namespaces;
    StartTag tag;

    /* Check whether this element has or not namespace declarations. */
    if (g_hash_table_size(self->ns_buffer)) {
        tag.has_xmlns = TRUE;
        /* Push into the stack. */
        new_namespaces = merge_dicts(self->ns_current, self->ns_buffer);
        g_array_append_val(self->ns_stack, new_namespaces);
        /* Update the current namespaces. */
        self->ns_current = new_namespaces;
    } else
        tag.has_xmlns = FALSE;

    /* Push the new item into the stack. */
    tag.prefix = prefix;
    tag.name = g_strdup(name);
    g_array_append_val(self->tag_stack, tag);
}


/* Tests wether the following data matches the "expected" string, and moves
 * the cursor forward if that is the case (updates the "column" index). The
 * variable "expected" must not contain new lines, the "line_no" index is
 * not updated. */
int read_string(Parser* self, char* expected) {
    char* cursor;
    char c;

    for (cursor=expected; 1; cursor++) {
        c = *cursor;
        if (c == '\0')
            return 0;
        if (c != self->next_char)
            return -1;
        move_cursor(self);
    }
}


/* Name (http://www.w3.org/TR/REC-xml/#NT-Name) */
void xml_name(Parser* self, GString* name) {
    /* Read as much as possible */
    while (IS_NAME_CHAR(self->next_char)) {
        g_string_append_c(name, self->next_char);
        move_cursor(self);
    }
}


/* Prefix + Name (http://www.w3.org/TR/REC-xml-names/#ns-decl)
 *
 * On success, returns a pointer to the prefix string stored in the
 * "self->ns_prefixes" variable.  On error returns NULL.
 */
gchar* xml_prefix_name(Parser* self, GString* name) {
    GString* prefix;
    gchar* result;

    /* Initialize the prefix */
    prefix = g_string_sized_new(10);

    /* Read as much as possible */
    while (IS_NC_NAME_CHAR(self->next_char)) {
        g_string_append_c(prefix, self->next_char);
        move_cursor(self);
    }

    /* Test the prefix is not missing. */
    if (prefix->len == 0) {
        g_string_free(prefix, TRUE);
        return NULL;
    }

    if (self->next_char == ':') {
        /* With prefix */
        move_cursor(self);
        /* Read the name */
        xml_name(self, name);
        if (name->len == 0) {
            g_string_free(prefix, TRUE);
            return NULL;
        }
    } else {
        /* No Prefix */
        g_string_assign(name, prefix->str);
        g_string_set_size(prefix, 0); /* The empty string. */
    }

    /* Keep the prefix. */
    result = g_string_chunk_insert_const(self->ns_prefixes, prefix->str);
    g_string_free(prefix, TRUE);

    return result;
}


/* White Space (http://www.w3.org/TR/REC-xml/#NT-S) */
void xml_space(Parser* self) {
    while (isspace(self->next_char))
        move_cursor(self);
}


/* Equal (http://www.w3.org/TR/REC-xml/#NT-Eq) */
int xml_equal(Parser* self) {
    xml_space(self);
    if (self->next_char != '=')
        return -1;
    move_cursor(self);
    xml_space(self);

    return 0;
}

/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-EntityRef)
 *
 * Returns 0 on success, 1 on error. */
int xml_entity_reference(Parser* self, GString* buffer) {
    GString* name;
    gunichar codepoint;
    gpointer aux;

    /* Read the name */
    name = g_string_sized_new(10);
    xml_name(self, name);
    if (name->len == 0) {
        g_string_free(name, TRUE);
        return 1;
    }

    /* Read ";" */
    if (self->next_char != ';') {
        g_string_free(name, TRUE);
        return 1;
    }
    move_cursor(self);

    /* From entity name to codepoint. */
    aux = g_hash_table_lookup(builtin_entities, name->str);
    g_string_free(name, TRUE);
    if (aux == NULL)
        return 1;
    codepoint = (gunichar)GPOINTER_TO_UINT(aux);

    /* From codepoint to str (UTF-8). */
    g_string_append_unichar(buffer, codepoint);
    return 0;
}


/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-CharRef)
 *
 * Returns a new reference. */
int xml_char_reference(Parser* self, GString* buffer) {
    char c;
    gunichar cp;

    cp = 0;
    c = self->next_char;
    /* Hexadecimal */
    if (c == 'x') {
        c = move_cursor(self);
        /* Check there is at least one digit */
        if (!isxdigit(c))
            return 1;
        /* Hex */
        while (isxdigit(c)) {
            /* Decode char */
            cp = cp * 16;
            if (c >= '0' && c <= '9') {
                cp = cp + (c - '0');
            } else if (c >= 'A' && c <= 'F') {
                cp = cp + (c - 'A') + 10;
            } else if (c >= 'a' && c <= 'f')
                cp = cp + (c - 'a') + 10;
            /* Next. */
            c = move_cursor(self);
        }
    /* Decimal */
    } else if (isdigit(c)) {
        while (isdigit(c)) {
            cp = (10 * cp) + (c - '0');
            c = move_cursor(self);
        }
    /* Error. */
    } else
        return 1;

    /* Read ";" */
    if (self->next_char != ';')
        return 1;
    move_cursor(self);

    /* From codepoint to str (UTF-8). */
    g_string_append_unichar(buffer, cp);
    return 0;
}



/* Quoted string, without character or entity references.  Used to parse a
 * variety of elements, like the prolog and the document type declaration.
 *
 * Returns a sub-string. */
int read_quoted_string(Parser* self, GString* str) {
    char delimiter;
    char c;

    /* Read the opening quote. */
    delimiter = self->next_char;
    if ((delimiter != '"') && (delimiter != '\''))
        return 1;
    move_cursor(self);

    /* Read until the closing quote, or a forbidden character is found. */
    c = self->next_char;
    while (c != delimiter) {
        /* Test for forbidden characters: return on error. */
        if ((c == '\0') || (c == '<'))
            return 1;

        g_string_append_c(str, c);
        c = move_cursor(self);
    }
    move_cursor(self);

    return 0;
}


/* Attribute Value (http://www.w3.org/TR/REC-xml/#NT-AttValue)
 *
 * Returns 0 on success, 1 on error. */
int xml_attr_value(Parser* self, GString* buffer) {
    char delimiter;
    int error;

    /* The heading quote */
    delimiter = self->next_char;
    if ((delimiter != '"') && (delimiter != '\''))
        return 1;
    move_cursor(self);

    /* The value */
    while (self->next_char != delimiter) {
        switch (self->next_char) {
            case '\0':
                return 1;
            case '<':
                return 1;
            case '&':
                /* Entity or Character Reference */
                move_cursor(self);
                /* Parse and append the reference. */
                if (self->next_char == '#') {
                    move_cursor(self);
                    error = xml_char_reference(self, buffer);
                    if (error)
                        return 1;
                } else {
                    error = xml_entity_reference(self, buffer);
                    if (error)
                        return 1;
                }
                break;
            default:
                g_string_append_c(buffer, self->next_char);
                move_cursor(self);
        }
    }
    move_cursor(self);

    return 0;
}


/**************************************************************************
 * Mix Python/C: TODO separate.
 *************************************************************************/

/* Called when a parser object is created. */
static PyObject* Parser_new(PyTypeObject* type, PyObject* args, PyObject* kw) {
    Parser* self;

    /* Python's boilerplate. */
    self = (Parser*)type->tp_alloc(type, 0);
    if (self == NULL)
        return NULL;

    /* Specifics. */
    self->py_source = NULL;
    self->cursor = NULL;
    self->file = NULL;
    self->read_char = NULL;
    self->next_char = '\0';
    self->line_no = 0;
    self->column = 0;
    self->tag_stack = g_array_sized_new(FALSE, FALSE, sizeof(StartTag), 20);
    self->ns_stack = g_array_sized_new(FALSE, FALSE, sizeof(GHashTable*), 5);
    self->ns_default = g_hash_table_new(g_str_hash, g_str_equal);
    self->ns_current = NULL;
    self->ns_buffer = g_hash_table_new(g_str_hash, g_str_equal);
    self->ns_prefixes = g_string_chunk_new(64);
    self->ns_uris = g_string_chunk_new(256);
    self->py_left_token = NULL;
    self->attributes = g_ptr_array_sized_new(10);
    self->buffer = g_string_sized_new(256);
    return (PyObject*)self;
}


/* Resets the Parser state.  Code shared by "Parser_dealloc" and
 * "Parser_init".
 */
void Parser_reset(Parser* self) {
    guint index;
    StartTag* tag;
    GHashTable* xmlns;

    /* Release the Python objects. */
    Py_XDECREF(self->py_source);
    self->py_source = NULL;
    Py_XDECREF(self->py_left_token);
    self->py_left_token = NULL;

    /* Free the tag stack. */
    for (index=0; index < self->tag_stack->len; index++) {
        tag = &g_array_index(self->tag_stack, StartTag, index);
        free(tag->name);
    }
    g_array_set_size(self->tag_stack, 0);

    /* Free the namespace stack. */
    for (index=0; index < self->ns_stack->len; index++) {
        xmlns = g_array_index(self->ns_stack, GHashTable*, index);
        g_hash_table_destroy(xmlns);
    }
    g_array_set_size(self->ns_stack, 0);

    /* The dafault namespace and the stored strings. */
    g_hash_table_steal_all(self->ns_default);
    g_hash_table_steal_all(self->ns_buffer);
    g_string_chunk_clear(self->ns_prefixes);
    g_string_chunk_clear(self->ns_uris);
    /* Attributes. */
    reset_attributes(self->attributes);
}


/* Called when a parser object is destroyed. */
static void Parser_dealloc(Parser* self) {
    Parser_reset(self);

    /* Free the stack and XML namespaces. */
    g_array_free(self->tag_stack, TRUE);
    g_array_free(self->ns_stack, TRUE);
    g_hash_table_destroy(self->ns_default);
    g_hash_table_destroy(self->ns_buffer);
    g_string_chunk_free(self->ns_prefixes);
    g_string_chunk_free(self->ns_uris);
    g_ptr_array_free(self->attributes, TRUE);
    g_string_free(self->buffer, TRUE);

    /* Python's boilerplate. */
    self->ob_type->tp_free((PyObject*)self);
}


/* Called to initialize the parser object (the "__init__" method). */
static int Parser_init(Parser* self, PyObject* args, PyObject* kw) {
    PyObject* py_source;
    PyObject* py_namespaces;
    PyObject* py_key;
    PyObject* py_value;
    Py_ssize_t py_pos;
    gchar* key;
    gchar* value;

    /* Reset the parser's state. */
    Parser_reset(self);

    /* Parse the input parameters. */
    py_namespaces = NULL;
    if (!PyArg_ParseTuple(args, "O|O!", &py_source, &PyDict_Type,
                          &py_namespaces))
        return -1;

    if (PyString_CheckExact(py_source)) {
        Py_INCREF(py_source);
        self->py_source = py_source;
        self->cursor = PyString_AsString(py_source);
        self->read_char = &(read_char_from_string);
    } else if (PyFile_Check(py_source)) {
        /* TODO Finish. */
        Py_INCREF(py_source);
        self->py_source = py_source;
        self->file = PyFile_AsFile(py_source);
        self->file_buffer_index = BUFFER_SIZE;
        self->read_char = &(read_char_from_file);
    } else {
        PyErr_SetString(PyExc_TypeError, "argument 1 must be string or file");
        return -1;
    }

    /* Keep the Python string to parse. */
    self->line_no = 1;
    self->column = 1;

    /* Set built-in namespace: xml */
    key = g_string_chunk_insert_const(self->ns_prefixes, "xml");
    value = g_string_chunk_insert_const(self->ns_uris,
            "http://www.w3.org/XML/1998/namespace");
    g_hash_table_insert(self->ns_default, (gpointer*)key, (gpointer*)value);
    /* Set built-in namespace: xmlns */
    key = g_string_chunk_insert_const(self->ns_prefixes, "xmlns");
    value = g_string_chunk_insert_const(self->ns_uris,
            "http://www.w3.org/2000/xmlns/");
    g_hash_table_insert(self->ns_default, (gpointer*)key, (gpointer*)value);

    /* Initialize the default namespaces. */
    self->ns_current = self->ns_default;
    if (py_namespaces != NULL) {
        py_pos = 0;
        while (PyDict_Next(py_namespaces, &py_pos, &py_key, &py_value)) {
            if (py_key == Py_None)
                key = (gchar*)"";
            else
                key = (gchar*)PyString_AsString(py_key);
            value = (gchar*)PyString_AsString(py_value);
            g_string_chunk_insert_const(self->ns_prefixes, key);
            g_string_chunk_insert_const(self->ns_uris, value);
            g_hash_table_insert(self->ns_default, (gpointer*)key,
                                (gpointer*)value);
        }
    }

    /* Read the first char. */
    move_cursor(self);

    return 0;
}


/* Checks that the given tag, defined by a couple of sub-strings (tag prefix
 * and name), matches the last start tag in the stack.
 *
 * Updates (pops) the tag and namespace stacks.
 *
 * On error returns a NULL pointer.  On success returns a new Python value,
 * with the tag expressed as a tuple of two elements, the tag uri and name.
 */
PyObject* pop_tag(Parser* self, gchar* prefix, GString* name) {
    guint index;
    StartTag* tag;
    int cmp;
    gchar* uri;
    GHashTable* xmlns;

    /* Check the stack is not empty */
    if (self->tag_stack->len == 0)
        return NULL;

    /* Check the given (end) tag matches the last start tag */
    index = (self->tag_stack->len) - 1;
    tag = &g_array_index(self->tag_stack, StartTag, index);
    if (prefix != tag->prefix)
        return NULL;
    cmp = strcmp(tag->name, name->str);
    if (cmp != 0)
        return NULL;

    /* Find out the URI from the prefix */
    uri = g_hash_table_lookup(self->ns_current, prefix);

    /* Pop from the tag stack. */
    free(tag->name);
    g_array_set_size(self->tag_stack, index);

    /* Pop from the namespace stack, if needed. */
    if (tag->has_xmlns) {
        index = (self->ns_stack->len) - 1;
        xmlns = g_array_index(self->ns_stack, GHashTable*, index);
        g_hash_table_destroy(xmlns);
        g_array_set_size(self->ns_stack, index);

        /* Update the current namespace. */
        if (index == 0)
            self->ns_current = self->ns_default;
        else {
            index--;
            xmlns = g_array_index(self->ns_stack, GHashTable*, index);
            self->ns_current = xmlns;
        }
    }

    /* Build the return value */
    return Py_BuildValue("(ss)", uri, name->str);
}


/* Processing Instruction or XML Declaration.
 *
 * Input State: "<?" * "...?>"
 */
PyObject* read_pi(Parser* self) {
    PyObject* py_version;
    PyObject* py_encoding;
    PyObject* py_standalone;
    PyObject* py_value;
    char c;
    int error;
    guint line, column;

    line = self->line_no;
    column = self->column;

    /* Target */
    xml_name(self, self->buffer);
    if (self->buffer->len == 0)
        return ERROR(INVALID_TOKEN, line, column);
    /* White Space */
    xml_space(self);

    /* Processing Instruction (http://www.w3.org/TR/REC-xml/#dt-pi) */
    if (strcmp(self->buffer->str, "xml")) {
        py_value = PyString_FromString(self->buffer->str);
        g_string_set_size(self->buffer, 0);
        /* Value */
        c = self->next_char;
        while (c != '\0') {
            /* Stop condition: "?>" */
            if (c == '?') {
                c = move_cursor(self);
                if (c == '>')
                    return Py_BuildValue("(i(Ns)i)", PI, py_value,
                           self->buffer->str, line);
                g_string_append_c(self->buffer, '?');
            }
            g_string_append_c(self->buffer, c);
            c = move_cursor(self);
        }
        Py_DECREF(py_value);
        return ERROR(INVALID_TOKEN, line, column);
    }
    /* XML decl (http://www.w3.org/TR/REC-xml/#NT-XMLDecl) */
    /* Read the version. */
    g_string_set_size(self->buffer, 0);
    if (read_string(self, "version") == -1)
        return ERROR(BAD_XML_DECL, line, column);
    if (xml_equal(self) == -1)
        return ERROR(BAD_XML_DECL, line, column);
    error = read_quoted_string(self, self->buffer);
    if (error)
        return ERROR(BAD_XML_DECL, line, column);
    py_version = PyString_FromString(self->buffer->str);
    xml_space(self);
    /* Read the encoding. */
    g_string_set_size(self->buffer, 0);
    c = self->next_char;
    if (c == 'e') {
        if (read_string(self, "encoding") == -1) {
            Py_DECREF(py_version);
            return ERROR(BAD_XML_DECL, line, column);
        }
        if (xml_equal(self) == -1) {
            Py_DECREF(py_version);
            return ERROR(BAD_XML_DECL, line, column);
        }
        error = read_quoted_string(self, self->buffer);
        if (error) {
            Py_DECREF(py_version);
            return ERROR(BAD_XML_DECL, line, column);
        }
        py_encoding = PyString_FromString(self->buffer->str);
        xml_space(self);
    } else
        py_encoding = PyString_FromString("utf-8");
    /* Read "standalone". */
    g_string_set_size(self->buffer, 0);
    c = self->next_char;
    if (c == 's') {
        if (read_string(self, "standalone") == -1) {
            Py_DECREF(py_version);
            Py_DECREF(py_encoding);
            return ERROR(BAD_XML_DECL, line, column);
        }
        if (xml_equal(self) == -1) {
            Py_DECREF(py_version);
            Py_DECREF(py_encoding);
            return ERROR(BAD_XML_DECL, line, column);
        }
        error = read_quoted_string(self, self->buffer);
        if (error) {
            Py_DECREF(py_version);
            Py_DECREF(py_encoding);
            return ERROR(BAD_XML_DECL, line, column);
        }
        py_standalone = PyString_FromString(self->buffer->str);
        xml_space(self);
    } else {
        py_standalone = Py_None;
        Py_INCREF(py_standalone);
    }
    /* Stop condition: "?>". */
    c = self->next_char;
    if (c == '?') {
        c = move_cursor(self);
        if (c == '>') {
            move_cursor(self);
            return Py_BuildValue("(i(NNN)i)", XML_DECL, py_version,
                   py_encoding, py_standalone, line);
        }
    }
    return ERROR(BAD_XML_DECL, line, column);
}


/* Document Type (http://www.w3.org/TR/REC-xml/#sec-prolog-dtd)
 *
 * Input State: "<!D" * "OCTYPE..."
 */
PyObject* read_document_type(Parser* self) {
    PyObject* py_public_id;
    PyObject* py_system_id;
    PyObject* py_value;
    GString* name;
    GString* public_id;
    GString* system_id;
    int error;
    guint line, column;

    line = self->line_no;
    column = self->column;

    if (read_string(self, "OCTYPE"))
        return ERROR(INVALID_TOKEN, line, column);
    xml_space(self);

    /* Name */
    name = g_string_sized_new(10);
    xml_name(self, name);
    if (name->len == 0) {
        g_string_free(name, TRUE);
        return ERROR(INVALID_TOKEN, line, column);
    }
    xml_space(self);

    /* External ID */
    switch (self->next_char) {
        case 'S':
            if (read_string(self, "SYSTEM")) {
                g_string_free(name, TRUE);
                return ERROR(INVALID_TOKEN, line, column);
            }
            /* PUBLIC ID */
            py_public_id = Py_None;
            Py_INCREF(py_public_id);
            break;
        case 'P':
            if (read_string(self, "PUBLIC")) {
                g_string_free(name, TRUE);
                return ERROR(INVALID_TOKEN, line, column);
            }
            /* PUBLIC ID */
            xml_space(self);
            public_id = g_string_sized_new(32);
            error = read_quoted_string(self, public_id);
            if (error) {
                g_string_free(name, TRUE);
                g_string_free(public_id, TRUE);
                return ERROR(INVALID_TOKEN, line, column);
            }
            py_public_id = PyString_FromString(public_id->str);
            g_string_free(public_id, TRUE);
            break;
        default:
            g_string_free(name, TRUE);
            return ERROR(INVALID_TOKEN, line, column);
    }

    /* SYSTEM ID */
    xml_space(self);
    system_id = g_string_sized_new(64);
    error = read_quoted_string(self, system_id);
    if (error) {
        g_string_free(name, TRUE);
        g_string_free(system_id, TRUE);
        Py_DECREF(py_public_id);
        return ERROR(INVALID_TOKEN, line, column);
    }
    py_system_id = PyString_FromString(system_id->str);
    g_string_free(system_id, TRUE);

    /* White Space */
    xml_space(self);

    /* Internal subset */
    if (self->next_char == '[') {
        /* TODO NOT IMPLEMENTED*/
        g_string_free(name, TRUE);
        Py_DECREF(py_public_id);
        Py_DECREF(py_system_id);
        PyErr_SetString(PyExc_NotImplementedError,
                        "internal subset not yet supported");
        return ERROR(INVALID_TOKEN, line, column);
    }

    /* End doctype declaration */
    if (self->next_char != '>') {
        g_string_free(name, TRUE);
        Py_DECREF(py_public_id);
        Py_DECREF(py_system_id);
        return ERROR(INVALID_TOKEN, line, column);
    }
    move_cursor(self);

    /* Build the Python value. */
    py_value = Py_BuildValue("(i(sNNO)i)", DOCUMENT_TYPE, name->str,
               py_system_id, py_public_id, Py_None, line);
    g_string_free(name, TRUE);
    return py_value;
}


/* CData Section
 *
 * Input State: "<![" * "CDATA[...]]>"
 */
PyObject* read_cdata(Parser* self) {
    char c;
    guint line, column;

    line = self->line_no;
    column = self->column;

    if (read_string(self, "CDATA["))
        return ERROR(INVALID_TOKEN, line, column);
    c = self->next_char;
    while (c != '\0') {
        /* Stop condition: "]]>" */
        if (c == ']') {
            c = move_cursor(self);
            if (c == ']') {
                c = move_cursor(self);
                if (c == '>')
                    return Py_BuildValue("isi", CDATA, self->buffer->str,
                                         line);
                g_string_append_c(self->buffer, ']');
            }
            g_string_append_c(self->buffer, ']');
        }
        /* Something else. */
        g_string_append_c(self->buffer, c);
        c = move_cursor(self);
    }
    return ERROR(INVALID_TOKEN, line, column);
}


/* Comment.
 *
 * Input State: "<!-" * "-...-->"
 */
PyObject* read_comment(Parser* self) {
    char c;
    guint line, column;

    line = self->line_no;
    column = self->column;

    c = self->next_char;
    if (c != '-')
        return ERROR(INVALID_TOKEN, line, column);
    c = move_cursor(self);

    /* Comment (http://www.w3.org/TR/REC-xml/#dt-comment) */
    while (1) {
        /* Stop condition: "-->" */
        if (c == '-') {
            c = move_cursor(self);
            if (c == '-') {
                c = move_cursor(self);
                if (c != '>')
                    return ERROR(INVALID_TOKEN, line, column);
                move_cursor(self);
                return Py_BuildValue("(isi)", COMMENT, self->buffer->str,
                                     line);
            } else
                g_string_append_c(self->buffer, '-');
        }
        /* Something else. */
        g_string_append_c(self->buffer, c);
        c = move_cursor(self);
    }
}


/* Start Element. */
PyObject* read_start_tag(Parser* self) {
    PyObject* py_tag_name;
    PyObject* py_attributes;
    PyObject* py_attr_name;
    PyObject* py_attr_value;
    GHashTable* namespaces;
    gchar* tag_prefix;
    gchar* tag_uri;
    gchar* key;
    gchar* value;
    gchar* attr_uri;
    gboolean end_tag;
    Attribute* attribute;
    char c;
    guint line, column;
    int error;
    int idx;

    line = self->line_no;
    column = self->column;

    /* Read tag (prefix & name). */
    tag_prefix = xml_prefix_name(self, self->buffer);
    if (tag_prefix == NULL)
        return ERROR(INVALID_TOKEN, line, column);
    /* Attributes */
    reset_attributes(self->attributes);
    g_hash_table_steal_all(self->ns_buffer);
    while (1) {
        xml_space(self);
        c = self->next_char;
        if (c == '>') {
            move_cursor(self);
            /* Add to the stack */
            push_tag(self, tag_prefix, self->buffer->str);
            end_tag = FALSE;
            namespaces = self->ns_current;
            break;
        } else if (c == '/') {
            c = move_cursor(self);
            if (c != '>')
                return ERROR(INVALID_TOKEN, line, column);
            move_cursor(self);

            end_tag = TRUE;
            if (g_hash_table_size(self->ns_buffer))
                namespaces = merge_dicts(self->ns_current, self->ns_buffer);
            else
                namespaces = self->ns_current;

            break;
        }
        /* Attributes */
        attribute = new_attribute();
        g_ptr_array_add(self->attributes, attribute);
        /* Prefix & Name */
        attribute->prefix = xml_prefix_name(self, attribute->name);
        if (attribute->prefix == NULL)
            return ERROR(INVALID_TOKEN, line, column);
        /* Eq */
        if (xml_equal(self) == -1)
            return ERROR(INVALID_TOKEN, line, column);
        /* Value */
        error = xml_attr_value(self, attribute->value);
        if (error)
            return ERROR(INVALID_TOKEN, line, column);

        if (strcmp(attribute->prefix, "") == 0) {
            /* Default namespace declaration */
            if (strcmp(attribute->name->str, "xmlns") == 0) {
                /* Keep the value (uri). */
                value = g_string_chunk_insert_const(self->ns_uris,
                        attribute->value->str);
                /* Check for duplicates */
                if (g_hash_table_lookup(self->ns_buffer, ""))
                    return ERROR(DUP_ATTR, line, column);
                /* Set the default namespace */
                g_hash_table_insert(self->ns_buffer, "", value);
            /* Attribute without a prefix (use tag's prefix). */
            } else if (strcmp(attribute->prefix, "") == 0) {
                attribute->prefix = tag_prefix;
            }
        /* Namespace declaration */
        } else if (strcmp(attribute->prefix, "xmlns") == 0) {
            /* Keep the namespace prefix (key). */
            key = g_string_chunk_insert_const(self->ns_prefixes,
                  attribute->name->str);
            /* Keep the namespace URI (value). */
            value = g_string_chunk_insert_const(self->ns_uris,
                    attribute->value->str);
            /* Check for duplicates */
            if (g_hash_table_lookup(self->ns_buffer, key))
                return ERROR(DUP_ATTR, line, column);
            /* Set the namespace */
            g_hash_table_insert(self->ns_buffer, key, value);
        }
    }

    /* Tag */
    tag_uri = g_hash_table_lookup(namespaces, tag_prefix);

    /* The END_ELEMENT token will be sent later */
    py_tag_name = PyString_FromString(self->buffer->str);
    if (end_tag)
        self->py_left_token = Py_BuildValue("(i(sO)i)", END_ELEMENT, tag_uri,
                              py_tag_name, line);

    /* Attributes */
    py_attributes = PyDict_New();
    for (idx=0; idx < self->attributes->len; idx++) {
        attribute = g_ptr_array_index(self->attributes, idx);
        /* Find out the attribute URI */
        attr_uri = g_hash_table_lookup(namespaces, attribute->prefix);
        /* Build the attribute name. */
        py_attr_name = Py_BuildValue("(ss)", attr_uri, attribute->name->str);

        /* Check for duplicates */
        if (PyDict_Contains(py_attributes, py_attr_name)) {
            Py_DECREF(py_attr_name);
            Py_DECREF(py_attributes);
            Py_DECREF(py_tag_name);
            return ERROR(DUP_ATTR, line, column);
        }

        /* Find out the attribute value */
        py_attr_value = PyString_FromString(attribute->value->str);
        /* Update the dict */
        PyDict_SetItem(py_attributes, py_attr_name, py_attr_value);
        Py_DECREF(py_attr_name);
    }

    return Py_BuildValue("(i(sNN)i)", START_ELEMENT, tag_uri, py_tag_name,
                         py_attributes, line);
}


/* End Element (http://www.w3.org/TR/REC-xml/#NT-ETag)
 *
 * Input State: "</" * "...>"
 */
PyObject* read_end_tag(Parser* self) {
    PyObject* py_value;
    gchar* tag_prefix;
    guint line, column;

    line = self->line_no;
    column = self->column;

    /* Name */
    tag_prefix = xml_prefix_name(self, self->buffer);
    if (tag_prefix == NULL)
        return ERROR(INVALID_TOKEN, line, column);
    /* White Space */
    xml_space(self);
    /* Close */
    if (self->next_char != '>')
        return ERROR(INVALID_TOKEN, line, column);
    move_cursor(self);
    /* Remove from the stack */
    py_value = pop_tag(self, tag_prefix, self->buffer);
    if (py_value == NULL)
        return ERROR(MISSING, line, column);

    return Py_BuildValue("(iNi)", END_ELEMENT, py_value, line);
}


/* Character or Entity Reference. */
PyObject* read_reference(Parser* self) {
    guint line, column;
    int error;

    line = self->line_no;
    column = self->column;

    /* Character reference */
    if (self->next_char == '#') {
        move_cursor(self);
        error = xml_char_reference(self, self->buffer);
        if (error)
            return ERROR(BAD_CHAR_REF, line, column);
        return Py_BuildValue("(isi)", TEXT, self->buffer->str, line);
    }
    /* Entity reference */
    error = xml_entity_reference(self, self->buffer);
    if (error)
        return ERROR(BAD_ENTITY_REF, line, column);
    return Py_BuildValue("(isi)", TEXT, self->buffer->str, line);
}


/* Returns a new reference */
static PyObject* Parser_iternext(Parser* self) {
    PyObject* py_value;
    guint line, column;
    char c;

    /* There are tokens waiting */
    if (self->py_left_token) {
        py_value = self->py_left_token;
        self->py_left_token = NULL;
        return py_value;
    }

    line = self->line_no;
    column = self->column;

    /* Reset buffer. */
    g_string_set_size(self->buffer, 0);

    switch (self->next_char) {
        case '\0':
            /* End Of File. (FIXME, there're other places to check for EOF) */
            /* The open tags must be closed. */
            if (self->tag_stack->len > 0)
                return ERROR(MISSING, line, column);
            return NULL;
        case '<':
            c = move_cursor(self);
            switch (c) {
                case '/':
                    move_cursor(self);
                    /* "</" */
                    return read_end_tag(self);
                case '!':
                    c = move_cursor(self);
                    /* "<!" */
                    switch (c) {
                        case '-':
                            move_cursor(self);
                            /* "<!-" */
                            return read_comment(self);
                        case 'D':
                            move_cursor(self);
                            /* "<!D" */
                            return read_document_type(self);
                        case '[':
                            move_cursor(self);
                            /* "<![" */
                            return read_cdata(self);
                        default:
                            return ERROR(INVALID_TOKEN, line, column);
                    }
                case '?':
                    move_cursor(self);
                    /* "<?" */
                    return read_pi(self);
                default:
                    /* Start Element */
                    return read_start_tag(self);
            }
        case '&':
            move_cursor(self);
            return read_reference(self);
        default:
            /* Text */
            g_string_append_c(self->buffer, self->next_char);
            c = move_cursor(self);
            while ((c != '<') && (c != '&') && (c != '\0')) {
                g_string_append_c(self->buffer, c);
                c = move_cursor(self);
            }
            return Py_BuildValue("(isi)", TEXT, self->buffer->str, line);
    }

    /* Return None (just to avoid the compiler to complain) */
    return NULL;
}



/**************************************************************************
 * Python Specific
 *************************************************************************/

/* The XMLParser object: members. */
static PyMemberDef Parser_members[] = {
    {"line_no", T_INT, offsetof(Parser, line_no), 0, "Line number"},
    {"column", T_INT, offsetof(Parser, column), 0, "Column"},
    {NULL}
};


/* The XMLParser object: methods. */
static PyMethodDef Parser_methods[] = {
    {NULL, NULL, 0, NULL}
};


/* The XMLParser object: type. */
static PyTypeObject ParserType = {
    PyObject_HEAD_INIT(NULL)
    0,                              /* ob_size */
    "itools.xml.parser.XMLParser",  /* tp_name */
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
    0, /* FIXME set later: PyObject_SelfIter, */     /*tp_iter*/
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



/* Definition of the module functions. */
static PyMethodDef module_methods[] = {
    {NULL}
};


/* declarations for DLL import/export. */
#ifndef PyMODINIT_FUNC
#define PyMODINIT_FUNC void
#endif


/* Function called to initialize the module. */
PyMODINIT_FUNC
initparser(void) {
    PyObject* module;

    /* XXX Fix tp_Iter for cygwin */
    ParserType.tp_iter = PyObject_SelfIter;

    if (PyType_Ready(&ParserType) < 0)
        return;

    /* Initialize the built-in entity references. */
    init_builtin_entities();

    /* Initialize the module */
    module = Py_InitModule3("parser", module_methods, "Low-level XML parser");
    if (module == NULL)
        return;

    /* Register types */
    Py_INCREF(&ParserType);
    PyModule_AddObject(module, "XMLParser", (PyObject *)&ParserType);

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

