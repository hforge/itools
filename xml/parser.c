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

#include <stdarg.h>
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

/* Other Constants and Macros */
#define BUFFER_SIZE 512
#define GUNICHAR_TO_POINTER(u) ((gpointer) (gulong) (u))
#define GPOINTER_TO_UNICHAR(u) ((gunichar) (gulong) (u))
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
 * Abstract Data Types and their API
 *************************************************************************/

/* The String Tree is a data structure that allows to store compactly a set
 * of strings.  The lookup or insertion of a string is O(n) where "n" is the
 * lenght of the string.
 */


typedef struct _HStrTree HStrTree;

struct _HStrTree {
    gpointer data;
    HStrTree* children[256];
    /* Needed to rebuild the string. */
    HStrTree* parent;
    gchar chr;
};


HStrTree* h_str_tree_new(gpointer data) {
    HStrTree* tree;
    gushort idx;

    tree = malloc(sizeof(HStrTree));
    tree->data = data;
    tree->parent = NULL;
    for (idx=0; idx < 256; idx++) {
        tree->children[idx] = NULL;
    }

    return tree;
}


void h_str_tree_free(HStrTree* tree) {
    HStrTree* child;
    gushort idx;

    for (idx=0; idx < 256; idx++) {
        child = tree->children[idx];
        if (child != NULL)
            h_str_tree_free(child);
    }
    free(tree);
}


HStrTree* h_str_tree_traverse(HStrTree* tree, gchar chr) {
    HStrTree* child;
    gushort idx;

    idx = (gushort)chr;
    child = tree->children[idx];
    if (child == NULL) {
        child = h_str_tree_new(NULL);
        child->parent = tree;
        child->chr = chr;
        tree->children[idx] = child;
    }

    return child;
}


/**************************************************************************
 * Interned strings. */

G_LOCK_DEFINE_STATIC(interned_strings);
HStrTree* interned_strings_tree = NULL;
GStringChunk* interned_strings = NULL;


gchar* intern_string(gchar* str) {
    HStrTree* node;
    gchar* cursor;
    gchar chr;

    node = interned_strings_tree;

    /* Get the node. */
    cursor = str;
    chr = *cursor;
    while (chr != '\0') {
        node = h_str_tree_traverse(node, chr);
        cursor++;
        chr = *cursor;
    }

    /* New string. */
    if (node->data == NULL) {
        str = g_string_chunk_insert_const(interned_strings, str);
        node->data = str;
    }

    return node->data;
}



/**************************************************************************
 * Data Types
 *************************************************************************/

/* This type defines an start tag by its prefix and name, plus a boolean value
 * that says whether the tag includes XML namespace declarations (true) or not
 * (false). */
typedef struct {
    gchar* prefix;       /* Stored in "interned_strings". */
    gchar* name;         /* Stored in "interned_strings". */
    gboolean has_xmlns;
} StartTag;


/* This type represents an attribute. */
typedef struct {
    gchar* prefix;  /* Stored in "interned_strings". */
    gchar* name;    /* Stored in "interned_strings". */
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
    guint cursor_row;
    guint cursor_col;
    guint event_row;
    guint event_col;
    /* The stack and namespaces. */
    GArray* tag_stack;           /* The stack of open tags not yet closed. */
    GArray* ns_stack;            /* The stack of XML namespaces. */
    GHashTable* ns_default;      /* The default namespace (from Python). */
    GHashTable* ns_current;      /* A pointer to the current namespace. */
    GHashTable* ns_buffer;
    /* Cache the namespace URIs. */
    GPtrArray* ns_uris;
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
    /* Consume the last char. */
    if (self->next_char == '\n') {
        self->cursor_row++;
        self->cursor_col = 1;
    } else
        self->cursor_col++;

    /* Read the next char. */
    return (*(self->read_char))(self);;
}


Attribute* new_attribute(void) {
    Attribute* attribute;

    attribute = malloc(sizeof(Attribute));
    attribute->value = g_string_sized_new(64);
    return attribute;
}


void free_attribute(Attribute* attribute) {
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
    g_hash_table_insert(builtin_entities, str, GUNICHAR_TO_POINTER(codepoint))


/*
http://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references
*/
void init_builtin_entities(void) {
    gunichar index;
    gchar* str;
    gchar* html_20_32[] = {
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
    gchar* greek_letters[] = {
        "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
        "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
        NULL, "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega", NULL,
        NULL, NULL, NULL, NULL, NULL, NULL, "alpha", "beta", "gamma", "delta",
        "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu",
        "nu", "xi", "omicron", "pi", "rho", "sigmaf", "sigma", "tau",
        "upsilon", "phi", "chi", "psi", "omega", NULL, NULL, NULL, NULL, NULL,
        NULL, NULL, "thetasym", "upsih", NULL, NULL, NULL, "piv"};
    gchar* range_8194_8260[] = {
        "ensp", "emsp", NULL, NULL, NULL, NULL, NULL, "thinsp", NULL, NULL,
        "zwnj", "zwj", "lrm", "rlm", NULL, NULL, NULL, "ndash", "mdash", NULL,
        NULL, NULL, "lsquo", "rsquo", "sbquo", NULL, "ldquo", "rdquo",
        "bdquo", NULL, "dagger", "Dagger", "bull", NULL, NULL, NULL, "hellip",
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, "permil", NULL,
        "prime", "Prime", NULL, NULL, NULL, NULL, NULL, "lsaquo", "rsaquo",
        NULL, NULL, NULL, "oline", NULL, NULL, NULL, NULL, NULL, "frasl"};
    gchar* math_symbols[] = {
        "forall", NULL, "part", "exist", NULL, "empty", NULL, "nabla", "isin",
        "notin", NULL, "ni", NULL, NULL, NULL, "prod", NULL, "sum", "minus",
        NULL, NULL, NULL, NULL, "lowast", NULL, NULL, "radic", NULL, NULL,
        "prop", "infin", NULL, "ang", NULL, NULL, NULL, NULL, NULL, NULL,
        "and", "or", "cap", "cup", "int", NULL, NULL, NULL, NULL, NULL, NULL,
        NULL, NULL, "there4", NULL, NULL, NULL, NULL, NULL, NULL, NULL, "sim",
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, "cong", NULL, NULL,
        "asymp", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
        NULL, NULL, "ne", "equiv", NULL, NULL, "le", "ge", NULL, NULL, NULL,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
        NULL, NULL, NULL, "sub", "sup", "nsub", NULL, "sube", "supe"};

    builtin_entities = g_hash_table_new(g_str_hash, g_str_equal);
    /* XML */
    SET_ENTITY("quot", 34);
    SET_ENTITY("amp", 38);
    SET_ENTITY("apos", 39);
    SET_ENTITY("lt", 60);
    SET_ENTITY("gt", 62);
    /* HTML 2.0 & 3.2 */
    for (index=160; index <= 255; index++)
        SET_ENTITY(html_20_32[index-160], index);
    /* HTML 4.0 */
    SET_ENTITY("OElig", 338);
    SET_ENTITY("oelig", 339);
    SET_ENTITY("Scaron", 352);
    SET_ENTITY("scaron", 353);
    SET_ENTITY("Yuml", 376);
    SET_ENTITY("fnof", 402);
    SET_ENTITY("circ", 710);
    SET_ENTITY("tilde", 732);
    for (index=913; index <= 982; index++) {
        str = greek_letters[index-913];
        if (str != NULL)
            SET_ENTITY(str, index);
    }
    for (index=8194; index <= 8260; index++) {
        str = range_8194_8260[index-8194];
        if (str != NULL)
            SET_ENTITY(str, index);
    }
    SET_ENTITY("euro", 8364);
    SET_ENTITY("image", 8465);
    SET_ENTITY("weierp", 8472);
    SET_ENTITY("real", 8476);
    SET_ENTITY("trade", 8482);
    SET_ENTITY("alefsym", 8501);
    SET_ENTITY("larr", 8592);
    SET_ENTITY("uarr", 8593);
    SET_ENTITY("rarr", 8594);
    SET_ENTITY("darr", 8595);
    SET_ENTITY("harr", 8596);
    SET_ENTITY("crarr", 8629);
    SET_ENTITY("lArr", 8656);
    SET_ENTITY("uArr", 8657);
    SET_ENTITY("rArr", 8658);
    SET_ENTITY("dArr", 8659);
    SET_ENTITY("hArr", 8660);
    for (index=8704; index <= 8839; index++) {
        str = math_symbols[index-8704];
        if (str != NULL)
            SET_ENTITY(str, index);
    }
    SET_ENTITY("oplus", 8853);
    SET_ENTITY("otimes", 8855);
    SET_ENTITY("perp", 8869);
    SET_ENTITY("sdot", 8901);
    SET_ENTITY("lceil", 8968);
    SET_ENTITY("rceil", 8969);
    SET_ENTITY("lfloor", 8970);
    SET_ENTITY("rfloor", 8971);
    SET_ENTITY("lang", 9001);
    SET_ENTITY("rang", 9002);
    SET_ENTITY("loz", 9674);
    SET_ENTITY("spades", 9824);
    SET_ENTITY("clubs", 9827);
    SET_ENTITY("hearts", 9829);
    SET_ENTITY("diams", 9830);
}

void set_value(gpointer key, gpointer value, gpointer user_data) {
    GHashTable* a = (GHashTable*) user_data;
    g_hash_table_insert(a, key, value);
}

/* Updates a given hash table with the contents of another hash table.
 * The second hash table may be NULL, then the first hash table remains
 * untouched.
 */
void update_dict(GHashTable* a, GHashTable* b) {
    if (b == NULL)
        return;

    g_hash_table_foreach(b, set_value, a);
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
    tag.name = name;
    g_array_append_val(self->tag_stack, tag);
}


/* Tests wether the following data matches the "expected" string, and moves
 * the cursor forward if that is the case (updates the "column" index). */
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
 * "interned_strings" variable.  On error returns NULL.
 */
gboolean xml_prefix_name(Parser* self, gchar** prefix, gchar** name) {
    HStrTree* tree;
    HStrTree* parent;
    gchar* str;

    /* Read the prefix. */
    G_LOCK(interned_strings);
    tree = interned_strings_tree;
    while (IS_NC_NAME_CHAR(self->next_char)) {
        tree = h_str_tree_traverse(tree, self->next_char);
        move_cursor(self);
    }
    /* Test the string is not missing. */
    if (tree == interned_strings_tree) {
        G_UNLOCK(interned_strings);
        return TRUE;
    }
    /* Get the value. */
    if (tree->data == NULL) {
        g_string_set_size(self->buffer, 0);
        parent = tree;
        while (parent->parent != NULL) {
            g_string_prepend_c(self->buffer, parent->chr);
            parent = parent->parent;
        }
        str = g_string_chunk_insert(interned_strings, self->buffer->str);
        tree->data = (gpointer)str;
    } else {
        str = (gchar*)tree->data;
    }

    /* Just the name. */
    if (self->next_char != ':') {
        *prefix = interned_strings_tree->data;  /* The empty string. */
        *name = str;
        G_UNLOCK(interned_strings);
        return FALSE;
    }

    /* Prefix & Name. */
    *prefix = str;
    move_cursor(self);
    /* Read the name */
    tree = interned_strings_tree;
    while (IS_NAME_CHAR(self->next_char)) {
        tree = h_str_tree_traverse(tree, self->next_char);
        move_cursor(self);
    }
    /* Test the string is not missing. */
    if (tree == interned_strings_tree) {
        G_UNLOCK(interned_strings);
        return TRUE;
    }
    /* Get the value. */
    if (tree->data == NULL) {
        g_string_set_size(self->buffer, 0);
        parent = tree;
        while (parent->parent != NULL) {
            g_string_prepend_c(self->buffer, parent->chr);
            parent = parent->parent;
        }
        str = g_string_chunk_insert(interned_strings, self->buffer->str);
        tree->data = (gpointer)str;
    } else {
        str = (gchar*)tree->data;
    }

    *name = str;
    G_UNLOCK(interned_strings);
    return FALSE;
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
    codepoint = GPOINTER_TO_UNICHAR(aux);

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

/* This function will first release (decref) the python values passed,
 * and then return an error.
 */
PyObject*
Parser_error(Parser* self, const char* msg, PyObject* v0, ...) {
    va_list vars;
    PyObject* var;

    /* Decref Python values. */
    va_start(vars, v0);
    for (var = v0; var != NULL; var = va_arg(vars, PyObject*))
        Py_DECREF(var);
    va_end(vars);

    /* Set and return error. */
    return PyErr_Format(XMLError, msg, self->event_row, self->event_col);
}


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
    self->tag_stack = g_array_sized_new(FALSE, FALSE, sizeof(StartTag), 20);
    self->ns_stack = g_array_sized_new(FALSE, FALSE, sizeof(GHashTable*), 5);
    self->ns_default = g_hash_table_new(g_str_hash, g_str_equal);
    self->ns_current = NULL;
    self->ns_buffer = g_hash_table_new(g_str_hash, g_str_equal);
    self->ns_uris = g_ptr_array_sized_new(10);
    self->py_left_token = NULL;
    self->attributes = g_ptr_array_sized_new(10);
    self->buffer = g_string_sized_new(256);
    return (PyObject*)self;
}


/* Resets the Parser state.  Code shared by "Parser_dealloc" and
 * "Parser_init".
 */
void Parser_reset(Parser* self) {
    gpointer pointer;
    guint index;
    StartTag* tag;
    GHashTable* xmlns;

    /* Release the Python objects. */
    Py_XDECREF(self->py_source);
    self->py_source = NULL;
    Py_XDECREF(self->py_left_token);
    self->py_left_token = NULL;

    /* Free the tag stack. */
    for (index=0; index < self->tag_stack->len; index++)
        tag = &g_array_index(self->tag_stack, StartTag, index);
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
    /* URIs. */
    for (index=0; index < self->ns_uris->len; index++) {
        pointer = g_ptr_array_index(self->ns_uris, index);
        Py_DECREF((PyObject*)pointer);
    }
    g_ptr_array_set_size(self->ns_uris, 0);
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
    g_ptr_array_free(self->ns_uris, TRUE);
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
    PyObject* py_uri;
    Py_ssize_t py_pos;
    gchar* key;

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
    self->cursor_row = 1;
    self->cursor_col = 1;
    self->event_row = 1;
    self->event_col = 1;

    /* Set built-in namespace: xml */
    G_LOCK(interned_strings);
    py_uri = PyString_InternFromString("http://www.w3.org/XML/1998/namespace");
    g_ptr_array_add(self->ns_uris, (gpointer)py_uri);
    key = intern_string("xml");
    g_hash_table_insert(self->ns_default, key, (gpointer)py_uri);
    /* Set built-in namespace: xmlns */
    py_uri = PyString_InternFromString("http://www.w3.org/2000/xmlns/");
    key = intern_string("xmlns");
    g_hash_table_insert(self->ns_default, (gpointer)key, (gpointer)py_uri);

    /* Initialize the default namespaces. */
    self->ns_current = self->ns_default;
    if (py_namespaces != NULL) {
        py_pos = 0;
        while (PyDict_Next(py_namespaces, &py_pos, &py_key, &py_uri)) {
            /* Keep the prefix. */
            if (py_key == Py_None)
                key = intern_string("");
            else {
                key = (gchar*)PyString_AsString(py_key);
                key = intern_string(key);
            }
            /* Keept the URI. */
            g_ptr_array_add(self->ns_uris, (gpointer)py_uri);
            Py_INCREF(py_uri);
            /* The map from prefix to URI. */
            g_hash_table_insert(self->ns_default, (gpointer*)key,
                                (gpointer*)py_uri);
        }
    }
    G_UNLOCK(interned_strings);

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
PyObject* pop_tag(Parser* self, gchar* prefix, gchar* name) {
    PyObject* py_uri;
    guint index;
    StartTag* tag;
    GHashTable* xmlns;

    /* Check the stack is not empty */
    if (self->tag_stack->len == 0)
        return NULL;

    /* Check the given (end) tag matches the last start tag */
    index = (self->tag_stack->len) - 1;
    tag = &g_array_index(self->tag_stack, StartTag, index);
    if (prefix != tag->prefix)
        return NULL;
    if (name != tag->name)
        return NULL;

    /* Find out the URI from the prefix */
    py_uri = (PyObject*)g_hash_table_lookup(self->ns_current, prefix);
    if (py_uri == NULL)
        py_uri = Py_None;

    /* Pop from the tag stack. */
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
    return Py_BuildValue("(Os)", py_uri, name);
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

    /* Target */
    xml_name(self, self->buffer);
    if (self->buffer->len == 0)
        return Parser_error(self, INVALID_TOKEN, NULL);
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
                           self->buffer->str, self->event_row);
                g_string_append_c(self->buffer, '?');
            }
            g_string_append_c(self->buffer, c);
            c = move_cursor(self);
        }
        return Parser_error(self, INVALID_TOKEN, py_value, NULL);
    }
    /* XML decl (http://www.w3.org/TR/REC-xml/#NT-XMLDecl) */
    /* Read the version. */
    g_string_set_size(self->buffer, 0);
    if (read_string(self, "version") == -1)
        return Parser_error(self, BAD_XML_DECL, NULL);
    if (xml_equal(self) == -1)
        return Parser_error(self, BAD_XML_DECL, NULL);
    error = read_quoted_string(self, self->buffer);
    if (error)
        return Parser_error(self, BAD_XML_DECL, NULL);
    py_version = PyString_FromString(self->buffer->str);
    xml_space(self);
    /* Read the encoding. */
    g_string_set_size(self->buffer, 0);
    c = self->next_char;
    if (c == 'e') {
        if (read_string(self, "encoding") == -1)
            return Parser_error(self, BAD_XML_DECL, py_version, NULL);
        if (xml_equal(self) == -1)
            return Parser_error(self, BAD_XML_DECL, py_version, NULL);
        error = read_quoted_string(self, self->buffer);
        if (error)
            return Parser_error(self, BAD_XML_DECL, py_version, NULL);
        py_encoding = PyString_FromString(self->buffer->str);
        xml_space(self);
    } else
        py_encoding = PyString_FromString("utf-8");
    /* Read "standalone". */
    g_string_set_size(self->buffer, 0);
    c = self->next_char;
    if (c == 's') {
        if (read_string(self, "standalone") == -1)
            return Parser_error(self, BAD_XML_DECL, py_version, py_encoding,
                   NULL);
        if (xml_equal(self) == -1)
            return Parser_error(self, BAD_XML_DECL, py_version, py_encoding,
                   NULL);
        error = read_quoted_string(self, self->buffer);
        if (error)
            return Parser_error(self, BAD_XML_DECL, py_version, py_encoding,
                   NULL);
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
                   py_encoding, py_standalone, self->event_row);
        }
    }
    return Parser_error(self, BAD_XML_DECL, NULL);
}


/* Document Type (http://www.w3.org/TR/REC-xml/#sec-prolog-dtd)
 *
 * Input State: "<!D" * "OCTYPE..."
 */
PyObject* read_document_type(Parser* self) {
    PyObject* py_name;
    PyObject* py_public_id;
    PyObject* py_system_id;
    int error;

    if (read_string(self, "OCTYPE"))
        return Parser_error(self, INVALID_TOKEN, NULL);
    xml_space(self);

    /* Name */
    xml_name(self, self->buffer);
    if (self->buffer->len == 0)
        return Parser_error(self, INVALID_TOKEN, NULL);
    py_name = PyString_FromString(self->buffer->str);
    xml_space(self);

    /* External ID */
    switch (self->next_char) {
        case 'S':
            if (read_string(self, "SYSTEM"))
                return Parser_error(self, INVALID_TOKEN, py_name, NULL);
            /* PUBLIC ID */
            py_public_id = Py_None;
            Py_INCREF(py_public_id);
            break;
        case 'P':
            if (read_string(self, "PUBLIC"))
                return Parser_error(self, INVALID_TOKEN, py_name, NULL);
            /* PUBLIC ID */
            xml_space(self);
            g_string_set_size(self->buffer, 0);
            error = read_quoted_string(self, self->buffer);
            if (error)
                return Parser_error(self, INVALID_TOKEN, py_name, NULL);
            py_public_id = PyString_FromString(self->buffer->str);
            break;
        default:
            return Parser_error(self, INVALID_TOKEN, py_name, NULL);
    }

    /* SYSTEM ID */
    xml_space(self);
    g_string_set_size(self->buffer, 0);
    error = read_quoted_string(self, self->buffer);
    if (error)
        return Parser_error(self, INVALID_TOKEN, py_name, py_public_id, NULL);
    py_system_id = PyString_FromString(self->buffer->str);

    /* White Space */
    xml_space(self);

    /* Internal subset (TODO) */
    if (self->next_char == '[')
        /* FIXME Should raise PyExc_NotImplementedError */
        return Parser_error(self, INVALID_TOKEN, py_name, py_public_id,
               py_system_id, NULL);

    /* End doctype declaration */
    if (self->next_char != '>')
        return Parser_error(self, INVALID_TOKEN, py_name, py_public_id,
               py_system_id, NULL);
    move_cursor(self);

    /* Build the Python value. */
    return Py_BuildValue("(i(NNNO)i)", DOCUMENT_TYPE, py_name, py_system_id,
           py_public_id, Py_None, self->event_row);
}


/* CData Section
 *
 * Input State: "<![" * "CDATA[...]]>"
 */
PyObject* read_cdata(Parser* self) {
    char c;

    if (read_string(self, "CDATA["))
        return Parser_error(self, INVALID_TOKEN, NULL);
    c = self->next_char;
    while (c != '\0') {
        /* Stop condition: "]]>" */
        if (c == ']') {
            c = move_cursor(self);
            if (c == ']') {
                c = move_cursor(self);
                if (c == '>')
                    return Py_BuildValue("isi", CDATA, self->buffer->str,
                           self->event_row);
                g_string_append_c(self->buffer, ']');
            }
            g_string_append_c(self->buffer, ']');
        }
        /* Something else. */
        g_string_append_c(self->buffer, c);
        c = move_cursor(self);
    }
    return Parser_error(self, INVALID_TOKEN, NULL);
}


/* Comment.
 *
 * Input State: "<!-" * "-...-->"
 */
PyObject* read_comment(Parser* self) {
    char c;

    c = self->next_char;
    if (c != '-')
        return Parser_error(self, INVALID_TOKEN, NULL);
    c = move_cursor(self);

    /* Comment (http://www.w3.org/TR/REC-xml/#dt-comment) */
    while (1) {
        /* Stop condition: "-->" */
        if (c == '-') {
            c = move_cursor(self);
            if (c == '-') {
                c = move_cursor(self);
                if (c != '>')
                    return Parser_error(self, INVALID_TOKEN, NULL);
                move_cursor(self);
                return Py_BuildValue("(isi)", COMMENT, self->buffer->str,
                       self->event_row);
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
    PyObject* py_tag_uri;
    PyObject* py_attributes;
    PyObject* py_attr_name;
    PyObject* py_attr_value;
    PyObject* py_uri;
    PyObject* py_attr_uri;
    GHashTable* namespaces;
    gchar* tag_prefix;
    gchar* tag_name;
    gchar* attr_prefix;
    gchar* attr_name;
    gboolean end_tag;
    Attribute* attribute;
    char c;
    gboolean error;
    int idx;

    /* Read tag (prefix & name). */
    error = xml_prefix_name(self, &tag_prefix, &tag_name);
    if (error)
        return Parser_error(self, INVALID_TOKEN, NULL);
    /* Attributes */
    reset_attributes(self->attributes);
    g_hash_table_steal_all(self->ns_buffer);
    while (1) {
        xml_space(self);
        c = self->next_char;
        if (c == '>') {
            /* Add to the stack */
            push_tag(self, tag_prefix, tag_name);
            end_tag = FALSE;
            namespaces = self->ns_current;
            break;
        } else if (c == '/') {
            c = move_cursor(self);
            if (c != '>')
                return Parser_error(self, INVALID_TOKEN, NULL);

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
        error = xml_prefix_name(self, &attr_prefix, &attr_name);
        if (error)
            return Parser_error(self, INVALID_TOKEN, NULL);
        attribute->prefix = attr_prefix;
        attribute->name = attr_name;
        /* Eq */
        if (xml_equal(self) == -1)
            return Parser_error(self, INVALID_TOKEN, NULL);
        /* Value */
        error = xml_attr_value(self, attribute->value);
        if (error)
            return Parser_error(self, INVALID_TOKEN, NULL);

        if (strcmp(attribute->prefix, "") == 0) {
            /* Default namespace declaration */
            if (strcmp(attribute->name, "xmlns") == 0) {
                /* Check for duplicates */
                if (g_hash_table_lookup(self->ns_buffer, ""))
                    return Parser_error(self, DUP_ATTR, NULL);
                /* Keep the value (uri). */
                py_uri = PyString_InternFromString(attribute->value->str);
                g_ptr_array_add(self->ns_uris, (gpointer)py_uri);
                /* Set the default namespace */
                g_hash_table_insert(self->ns_buffer, "", (gpointer)py_uri);
            /* Attribute without a prefix (use tag's prefix). */
            } else {
                attribute->prefix = tag_prefix;
            }
        /* Namespace declaration */
        } else if (strcmp(attribute->prefix, "xmlns") == 0) {
            /* Check for duplicates */
            if (g_hash_table_lookup(self->ns_buffer, attribute->name))
                return Parser_error(self, DUP_ATTR, NULL);
            /* Keep the value (uri). */
            py_uri = PyString_InternFromString(attribute->value->str);
            g_ptr_array_add(self->ns_uris, (gpointer)py_uri);
            /* Set the namespace */
            g_hash_table_insert(self->ns_buffer, attribute->name,
                                (gpointer)py_uri);
        }
    }

    /* Read the ">". */
    move_cursor(self);

    /* Tag */
    py_tag_uri = (PyObject*)g_hash_table_lookup(namespaces, tag_prefix);
    if (py_tag_uri == NULL)
        py_tag_uri = Py_None;

    /* The END_ELEMENT token will be sent later */
    py_tag_name = PyString_FromString(tag_name);
    if (end_tag)
        self->py_left_token = Py_BuildValue("(i(OO)i)", END_ELEMENT,
                              py_tag_uri, py_tag_name, self->event_row);

    /* Attributes */
    py_attributes = PyDict_New();
    for (idx=0; idx < self->attributes->len; idx++) {
        attribute = g_ptr_array_index(self->attributes, idx);
        /* Find out the attribute URI */
        py_attr_uri = (PyObject*)g_hash_table_lookup(namespaces,
                      attribute->prefix);
        if (py_attr_uri == NULL)
            py_attr_uri = Py_None;
        /* Build the attribute name. */
        py_attr_name = Py_BuildValue("(Os)", py_attr_uri, attribute->name);

        /* Check for duplicates */
        if (PyDict_Contains(py_attributes, py_attr_name))
            return Parser_error(self, DUP_ATTR, py_attr_name, py_attributes,
                   py_tag_name, NULL);

        /* Find out the attribute value */
        py_attr_value = PyString_FromString(attribute->value->str);
        /* Update the dict */
        PyDict_SetItem(py_attributes, py_attr_name, py_attr_value);
        Py_DECREF(py_attr_name);
    }

    return Py_BuildValue("(i(ONN)i)", START_ELEMENT, py_tag_uri, py_tag_name,
           py_attributes, self->event_row);
}


/* End Element (http://www.w3.org/TR/REC-xml/#NT-ETag)
 *
 * Input State: "</" * "...>"
 */
PyObject* read_end_tag(Parser* self) {
    PyObject* py_value;
    gchar* tag_prefix;
    gchar* tag_name;
    gboolean error;

    /* Name */
    error = xml_prefix_name(self, &tag_prefix, &tag_name);
    if (error)
        return Parser_error(self, INVALID_TOKEN, NULL);
    /* White Space */
    xml_space(self);
    /* Close */
    if (self->next_char != '>')
        return Parser_error(self, INVALID_TOKEN, NULL);
    move_cursor(self);
    /* Remove from the stack */
    py_value = pop_tag(self, tag_prefix, tag_name);
    if (py_value == NULL)
        return Parser_error(self, INVALID_TOKEN, NULL);

    return Py_BuildValue("(iNi)", END_ELEMENT, py_value, self->event_row);
}


/* Character or Entity Reference. */
PyObject* read_reference(Parser* self) {
    int error;

    /* Character reference */
    if (self->next_char == '#') {
        move_cursor(self);
        error = xml_char_reference(self, self->buffer);
        if (error)
            return Parser_error(self, BAD_CHAR_REF, NULL);
        return Py_BuildValue("(isi)", TEXT, self->buffer->str,
               self->event_row);
    }
    /* Entity reference */
    error = xml_entity_reference(self, self->buffer);
    if (error)
        return Parser_error(self, BAD_ENTITY_REF, NULL);
    return Py_BuildValue("(isi)", TEXT, self->buffer->str, self->event_row);
}


/* Returns a new reference */
static PyObject* Parser_iternext(Parser* self) {
    PyObject* py_value;
    char c;

    /* There are tokens waiting */
    if (self->py_left_token) {
        py_value = self->py_left_token;
        self->py_left_token = NULL;
        return py_value;
    }

    /* Reset buffer. */
    g_string_set_size(self->buffer, 0);

    switch (self->next_char) {
        case '\0':
            /* End Of File. (FIXME, there're other places to check for EOF) */
            /* The open tags must be closed. */
            if (self->tag_stack->len > 0)
                return Parser_error(self, MISSING, NULL);
            return NULL;
        case '<':
            c = move_cursor(self);
            switch (c) {
                case '/':
                    move_cursor(self);
                    /* "</" */
                    py_value = read_end_tag(self);
                    break;
                case '!':
                    c = move_cursor(self);
                    /* "<!" */
                    switch (c) {
                        case '-':
                            move_cursor(self);
                            /* "<!-" */
                            py_value = read_comment(self);
                            break;
                        case 'D':
                            move_cursor(self);
                            /* "<!D" */
                            py_value = read_document_type(self);
                            break;
                        case '[':
                            move_cursor(self);
                            /* "<![" */
                            py_value = read_cdata(self);
                            break;
                        default:
                            return Parser_error(self, INVALID_TOKEN, NULL);
                    }
                    break;
                case '?':
                    move_cursor(self);
                    /* "<?" */
                    py_value = read_pi(self);
                    break;
                default:
                    /* Start Element */
                    py_value = read_start_tag(self);
                    break;
            }
            break;
        case '&':
            move_cursor(self);
            py_value = read_reference(self);
            break;
        default:
            /* Text */
            g_string_append_c(self->buffer, self->next_char);
            c = move_cursor(self);
            while ((c != '<') && (c != '&') && (c != '\0')) {
                g_string_append_c(self->buffer, c);
                c = move_cursor(self);
            }
            py_value = Py_BuildValue("(isi)", TEXT, self->buffer->str,
                       self->event_row);
            break;
    }

    self->event_row = self->cursor_row;
    self->event_col = self->cursor_col;
    return py_value;
}



/**************************************************************************
 * Python Specific
 *************************************************************************/

/* The XMLParser object: members. */
static PyMemberDef Parser_members[] = {
    {"line_no", T_INT, offsetof(Parser, event_row), 0, "Line number"},
    {"column", T_INT, offsetof(Parser, event_col), 0, "Column"},
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

    /* Initialize interned strings (prefix & name). */
    G_LOCK(interned_strings);
    interned_strings_tree = h_str_tree_new(NULL);
    interned_strings = g_string_chunk_new(64);
    intern_string("");
    intern_string("xml");
    intern_string("xmlns");
    G_UNLOCK(interned_strings);

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

