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

#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdio.h>

#include "parser.h"

#define IS_NC_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_'))
#define IS_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_') || (c == ':'))


/**************************************************************************
 * The internal functions/objects
 *************************************************************************/

/**********
 * Errors *
 * ********/

#define BAD_XML_DECL      "XML declaration not well-formed"
#define INVALID_TOKEN     "not well-formed (invalid token)"
#define MISSING           "expected end tag is missing"
#define BAD_ENTITY        "error parsing entity reference"
#define BAD_DTD           "error during parsing the DTD"
#define DUP_ATTR          "duplicate attribute"
#define INVALID_NAMESPACE "invalid namespace"


/**********************
 * The internal types *
 **********************/

/***************************
 * An auto realloc pointer *
 ***************************/

typedef struct
{
  gchar *data;
  gint length;

  gsize object_size;
  void (*constructor) (gpointer object);
  void (*destructor) (gpointer object);
} Arp;


Arp *
arp_new (gsize object_size, void (*constructor) (gpointer object),
         void (*destructor) (gpointer object))
{
  Arp *arp;
  gchar *pointer;
  gint idx;

  arp = g_new (Arp, 1);

  arp->object_size = object_size;
  arp->constructor = constructor;
  arp->destructor = destructor;
  arp->length = 16;

  /* Allocation of 16 objects */
  arp->data = (gchar *) g_malloc (16 * object_size);

  if (constructor)
    for (pointer = arp->data, idx = 0; idx < 16;
         pointer += object_size, idx++)
      (*constructor) (pointer);

  return arp;
}


gchar *
arp_get_index (Arp * arp, gint index)
{
  gchar *pointer;
  gint idx;

  if (index >= arp->length)
    {
      arp->data = (gchar *) g_realloc (arp->data,
                                       (arp->length +
                                        16) * (arp->object_size));

      if (arp->constructor != NULL)
        for (pointer = arp->data + arp->length * arp->object_size, idx = 0;
             idx < 16; pointer += arp->object_size, idx++)
          (*(arp->constructor)) (pointer);
      arp->length += 16;
    }

  return arp->data + index * arp->object_size;
}


void
arp_free (Arp * arp)
{
  gchar *pointer;
  gint idx;

  if (arp->destructor != NULL)
    {
      for (pointer = arp->data, idx = 0; idx < arp->length;
           pointer += arp->object_size, idx++)
        (*(arp->destructor)) (pointer);
    }

  g_free (arp->data);
  g_free (arp);
}


/*********************
 * The parser type ! *
 *********************/

struct _Parser
{
  /* Source */
  gint source_type;
  union
  {
    gchar *cursor;
    FILE *file;
  } source;
  gint source_row;
  gint source_col;
  gboolean new_line;

  /* Streams management */
  gchar cursor_char;
  Arp *streams_stack;
  gint streams_stack_size;

  /* Three buffers (to do everything) */
  GString *buffer1;
  GString *buffer2;
  GString *buffer3;

  /* An error buffer */
  GString *err_buffer;

  /* A strings storage place */
  GStringChunk *strings_storage;

  /* Attributes management */
  Arp *attr_storage;

  /* Tag stack */
  Arp *tags_stack;
  gint tags_stack_size;
  gboolean end_tag;
  gchar *end_tag_uri;
  gchar *end_tag_name;

  /* Namespaces management */
  GString *ns_buffer;
  Arp *ns_stack;
  gint ns_stack_size;
  gchar *default_ns;

  /* Entities management */
  GString *ent_buffer;
  GHashTable *GE_table;
};


/*********************
 * Cursor management *
 *********************/

typedef gchar *Stream;

gchar
move_cursor (Parser * parser)
{
  gint output;
  Stream *stream;
  gchar next_char;
  gint size;

  /* Not currently in the source ? */
  if (parser->streams_stack_size > 0)
    {
      for (;;)
        {
          stream = (Stream *) arp_get_index (parser->streams_stack,
                                             parser->streams_stack_size - 1);
          next_char = *((*stream)++);

          /* This stream is not empty */
          if (next_char != '\0')
            return parser->cursor_char = next_char;

          /* It is empty, pop the stream */
          size = --(parser->streams_stack_size);

          /* No more stream ? */
          if (!size)
            break;
        }
    }

  /* In the source ! */
  if (parser->new_line)
    {
      parser->source_row++;
      parser->source_col = 1;
      parser->new_line = FALSE;
    }
  else
    parser->source_col++;

  /* Read the next character */
  if (parser->source_type)
    {
      /* data */
      next_char = *(parser->source.cursor++);
    }
  else
    {
      /* file */
      output = fgetc (parser->source.file);
      next_char = (gchar) (output == EOF ? '\0' : output);
    }

  if (next_char == '\n')
    parser->new_line = TRUE;

  return parser->cursor_char = next_char;
}

void
parser_stream_push (Parser * parser, gchar * data)
{
  Stream *stream;

  /* A place */
  stream = (Stream *) arp_get_index (parser->streams_stack,
                                     (parser->streams_stack_size)++);

  /* Prepare the stream */
  *stream = data;

  /* And prepare the first caracter */
  move_cursor (parser);
}


/************
 * HStrTree *
 ************/

/* The String Tree is a data structure that allows to store compactly a set
 * of strings.  The lookup or insertion of a string is O(n) where "n" is the
 * length of the string.
 */

typedef struct _HStrTree HStrTree;
struct _HStrTree
{
  gchar *data;
  HStrTree *children[256];

  /* Needed to rebuild the string. */
  HStrTree *parent;
  gchar chr;
};


HStrTree *
h_str_tree_new (void)
{
  return g_new0 (HStrTree, 1);
}


void
h_str_tree_free (HStrTree * tree)
{
  HStrTree *child;
  int idx;

  for (idx = 0; idx < 256; idx++)
    {
      child = tree->children[idx];
      if (child)
        h_str_tree_free (child);
    }
  g_free (tree);
}


HStrTree *
h_str_tree_traverse (HStrTree * tree, gchar chr)
{
  HStrTree *child;
  guint idx;

  idx = (guint) chr;

  child = tree->children[idx];

  /* New ? */
  if (!child)
    {
      child = h_str_tree_new ();

      child->parent = tree;
      child->chr = chr;
      tree->children[idx] = child;
    }

  return child;
}


/*************
 * Attribute *
 *************/

void
parser_attr_constructor (gpointer pointer)
{
  ((Attribute *) pointer)->value = g_string_sized_new (32);
}


void
parser_attr_destructor (gpointer pointer)
{
  g_string_free (((Attribute *) pointer)->value, TRUE);
}


/*******
 * Tag *
 *******/

typedef struct
{
  gchar *uri;
  gchar *name;
  gint ns_number;
} Tag;


/*************
 * Namespace *
 *************/

typedef struct
{
  gchar *prefix;
  gchar *uri;
} Namespace;


/****************
 * Parser error *
 ****************/

gboolean
_parser_error (Parser * parser, ErrorEvent * event, gchar * msg)
{
  event->description = (gchar *) msg;
  event->error_row = parser->source_row;
  event->error_column = parser->source_col;
  event->type = XML_ERROR;
  return ERROR;
}

#define PARSER_ERROR(msg) _parser_error(parser, (ErrorEvent *)(event), msg)


/********************
 * Global variables *
 ********************/

/* Initialised ? */
gboolean parser_initialized = FALSE;

/* A global strings storage place */
G_LOCK_DEFINE_STATIC (parser_global_strings);
GStringChunk *parser_global_strings = NULL;

/* Interned string */
HStrTree *intern_strings_tree = NULL;
gchar *intern_empty;
gchar *intern_xmlns;

/* URN => file names table */
GHashTable *parser_URN_table;


/**********************
 * Internal functions *
 **********************/

gchar *
intern_string (gchar * str)
{
  HStrTree *node;
  gchar *cursor;

  node = intern_strings_tree;

  /* Get the node */
  for (cursor = str; *cursor != '\0'; cursor++)
    node = h_str_tree_traverse (node, *cursor);

  /* New string? */
  if (!(node->data))
    node->data = g_string_chunk_insert (parser_global_strings, str);

  return node->data;
}


void
parser_initialize (void)
{
  if (!parser_initialized)
    {
      /* Initialize interned strings (prefix & name). */
      G_LOCK (parser_global_strings);
      intern_strings_tree = h_str_tree_new ();
      parser_global_strings = g_string_chunk_new (64);
      intern_empty = intern_string ("");
      intern_xmlns = intern_string ("xmlns");
      intern_string ("xml");
      G_UNLOCK (parser_global_strings);

      /* Initialize the URN => file names table */
      parser_URN_table = g_hash_table_new (g_str_hash, g_str_equal);

      parser_initialized = TRUE;
    }
}


gchar *
parser_search_namespace (Parser * parser, gchar * prefix)
{
  gint idx;
  Namespace *namespace;

  for (idx = parser->ns_stack_size - 1,
       namespace = (Namespace *) arp_get_index (parser->ns_stack, idx);
       idx >= 0; idx--, namespace--)
    {
      if (namespace->prefix == prefix)
        return namespace->uri;
    }

  return NULL;
}


void
parser_push_namespace (Parser * parser, gchar * prefix, gchar * uri)
{
  Namespace *namespace;

  namespace = (Namespace *) arp_get_index (parser->ns_stack,
                                           parser->ns_stack_size);

  namespace->prefix = prefix;
  namespace->uri = g_string_chunk_insert_const (parser->strings_storage, uri);

  parser->ns_stack_size++;

  /* Default ? */
  if (prefix == intern_empty)
    parser->default_ns = namespace->uri;
}


void
parser_set_default_entities (Parser * parser)
{
  g_hash_table_insert (parser->GE_table, "lt", "&#60;");
  g_hash_table_insert (parser->GE_table, "gt", ">");
  g_hash_table_insert (parser->GE_table, "amp", "&#38;");
  g_hash_table_insert (parser->GE_table, "apos", "'");
  g_hash_table_insert (parser->GE_table, "quot", "\"");
}


void
parser_compute_urn (gchar * source, GString * target)
{
  g_string_assign (target, "urn:publicid:");
  for (; *source != '\0'; source++)
    {
      switch (*source)
        {
        case ' ':
        case '\t':
          if (*(source + 1) != ' ' && *(source + 1) != '\t')
            g_string_append_c (target, '+');
          break;
        case '/':
          if (*(source + 1) == '/')
            {
              g_string_append_c (target, ':');
              source++;
            }
          else
            g_string_append (target, "%2F");
          break;
        case ':':
          if (*(source + 1) == ':')
            {
              g_string_append_c (target, ';');
              source++;
            }
          else
            g_string_append (target, "%3A");
          break;
        case ';':
          g_string_append (target, "%3B");
          break;
        case '\'':
          g_string_append (target, "%27");
          break;
        case '?':
          g_string_append (target, "%3F");
          break;
        case '#':
          g_string_append (target, "%23");
          break;
        case '%':
          g_string_append (target, "%25");
          break;
        default:
          g_string_append_c (target, *source);
          break;
        }
    }
}


gboolean
parser_read_urn (gchar * urn, GString * target)
{
  gchar *urn_filename;
  gchar buffer[256];
  gint size;
  FILE *file;

  /* Search for the good file */
  urn_filename = (gchar *) g_hash_table_lookup (parser_URN_table, urn);

  if (!urn_filename)
    return ERROR;

  /* Open the file */
  file = fopen (urn_filename, "r");
  if (!file)
    return ERROR;

  /* And read it */
  g_string_set_size (target, 0);
  while ((size = fread (buffer, 1, 255, file)) != 0)
    {
      buffer[size] = '\0';
      g_string_append (target, buffer);
    }

  return ALL_OK;
}


/***************************************
 * DTD Declaration / parsing functions *
 ***************************************/

typedef struct
{
  /* Source */
  gint source_type;
  union
  {
    gchar *cursor;
    FILE *file;
  } source;

  /* Streams management */
  gchar cursor_char;
  Arp *streams_stack;
  gint streams_stack_size;

  /* Two buffers (to do everything) */
  GString *buffer1;
  GString *buffer2;

  /* External dtd ? */
  gboolean is_external;

  /* Entities management */
  GString *ent_buffer1;
  GString *ent_buffer2;
  GHashTable *PE_table;
  GStringChunk *PE_storage;

} DTD;


gchar
dtd_move_cursor (DTD * dtd)
{
  gint output;
  Stream *stream;
  gchar next_char;
  gint size;

  /* Not currently in the source ? */
  if (dtd->streams_stack_size > 0)
    {
      for (;;)
        {
          stream = (Stream *) arp_get_index (dtd->streams_stack,
                                             dtd->streams_stack_size - 1);
          next_char = *((*stream)++);

          /* This stream is not empty */
          if (next_char != '\0')
            return dtd->cursor_char = next_char;

          /* It is empty, pop the stream */
          size = --(dtd->streams_stack_size);

          /* No more stream ? */
          if (!size)
            break;
        }
    }

  /* Read the next character */
  if (dtd->source_type)
    {
      /* data */
      next_char = *(dtd->source.cursor++);
    }
  else
    {
      /* file */
      output = fgetc (dtd->source.file);
      next_char = (gchar) (output == EOF ? '\0' : output);
    }

  return dtd->cursor_char = next_char;
}


DTD *
dtd_new (gchar * data, FILE * file, gboolean is_external)
{
  DTD *dtd;

  /* Memory allocation */
  dtd = g_new (DTD, 1);

  /* Is external ? */
  dtd->is_external = is_external;

  /* The Glib objects */
  dtd->buffer1 = g_string_sized_new (256);
  dtd->buffer2 = g_string_sized_new (256);
  dtd->ent_buffer1 = g_string_sized_new (256);
  dtd->ent_buffer2 = g_string_sized_new (256);
  dtd->PE_table = g_hash_table_new (g_str_hash, g_str_equal);
  dtd->PE_storage = g_string_chunk_new (64);

  /* Streams management */
  dtd->streams_stack = arp_new (sizeof (Stream), NULL, NULL);
  dtd->streams_stack_size = 0;

  /* Source management */
  if (data)
    {
      dtd->source.cursor = data;
      dtd->source_type = 1;
    }
  else
    {
      dtd->source.file = file;
      dtd->source_type = 0;
    }
  dtd_move_cursor (dtd);

  return dtd;
}


void
dtd_free (DTD * dtd)
{
  /* Delete the Glib objects */
  g_string_free (dtd->buffer1, TRUE);
  g_string_free (dtd->buffer2, TRUE);
  g_string_free (dtd->ent_buffer1, TRUE);
  g_string_free (dtd->ent_buffer2, TRUE);
  g_hash_table_destroy (dtd->PE_table);
  g_string_chunk_free (dtd->PE_storage);

  /* Delete the arp objects */
  arp_free (dtd->streams_stack);

  /* And delete the dtd object */
  g_free (dtd);
}


void
dtd_stream_push (DTD * dtd, gchar * data)
{
  Stream *stream;

  /* A place */
  stream = (Stream *) arp_get_index (dtd->streams_stack,
                                     (dtd->streams_stack_size)++);

  /* Prepare the stream */
  *stream = data;

  /* And prepare the first caracter */
  dtd_move_cursor (dtd);
}


#define dtd_read_S(dtd) while(isspace((dtd)->cursor_char))\
                              {dtd_move_cursor(dtd);}

gboolean
dtd_read_string (DTD * dtd, gchar * expected)
{
  gchar *cursor;

  for (cursor = expected; *cursor != '\0'; cursor++)
    if (*cursor != dtd_move_cursor (dtd))
      return ERROR;

  return ALL_OK;
}


void
dtd_read_Name (DTD * dtd, GString * name)
{
  g_string_set_size (name, 0);

  /* Read as much as possible */
  while (IS_NAME_CHAR (dtd->cursor_char))
    {
      g_string_append_c (name, dtd->cursor_char);
      dtd_move_cursor (dtd);
    }
}


gboolean
dtd_read_parameter_entity (DTD * dtd)
{
  gpointer value;

  /* Read the '%' */
  dtd_move_cursor (dtd);

  /* Read the entity name */
  g_string_set_size (dtd->ent_buffer1, 0);
  for (;;)
    {
      switch (dtd->cursor_char)
        {
        case ';':
          goto for_end;
        case '\0':
          return ERROR;
        default:
          g_string_append_c (dtd->ent_buffer1, dtd->cursor_char);
        }
      dtd_move_cursor (dtd);
    }
for_end:

  /* We must find it in the PE_table ! */
  value = g_hash_table_lookup (dtd->PE_table, dtd->ent_buffer1->str);
  if (value)
    {
      dtd_stream_push (dtd, (gchar *) value);
      return ALL_OK;
    }

  return ERROR;
}


gboolean
dtd_read_value_entity (DTD * dtd, GString * buffer)
{
  gunichar code = 0;

  /* Hexadecimal ? */
  if (dtd_move_cursor (dtd) == 'x')
    {
      /* Yes */

      /* At least one character! */
      if (dtd_move_cursor (dtd) == ';')
        return ERROR;

      for (;; dtd_move_cursor (dtd))
        {
          /* 0 -> 9 */
          if (isdigit (dtd->cursor_char))
            {
              code = code * 16 + dtd->cursor_char - '0';
              continue;
            }
          /* a -> f */
          if ('a' <= dtd->cursor_char && dtd->cursor_char <= 'f')
            {
              code = code * 16 + dtd->cursor_char - 'a' + 10;
              continue;
            }
          /* A -> F */
          if ('A' <= dtd->cursor_char && dtd->cursor_char <= 'F')
            {
              code = code * 16 + dtd->cursor_char - 'A' + 10;
              continue;
            }
          break;
        }
    }
  else
    {
      /* No => decimal */

      /* At least one character! */
      if (dtd->cursor_char == ';')
        return ERROR;

      for (; isdigit (dtd->cursor_char); dtd_move_cursor (dtd))
        {
          code = code * 10 + dtd->cursor_char - '0';
          continue;
        }
    }

  /* Read the ';' */
  if (dtd->cursor_char != ';')
    return ERROR;
  dtd_move_cursor (dtd);

  /* From codepoint to str (UTF-8). */
  g_string_append_unichar (buffer, code);

  return ALL_OK;
}


gboolean
dtd_read_entity (DTD * dtd, GString * buffer)
{
  /* By value ? */
  if (dtd_move_cursor (dtd) == '#')
    return dtd_read_value_entity (dtd, buffer);

  /* No, so read the entity name */
  g_string_set_size (dtd->ent_buffer1, 0);
  for (;;)
    {
      switch (dtd->cursor_char)
        {
        case ';':
          goto for_end;
        case '\0':
          return ERROR;
        default:
          g_string_append_c (dtd->ent_buffer1, dtd->cursor_char);
        }
      dtd_move_cursor (dtd);
    }
for_end:

  /* In doctype, we only copy the name */
  g_string_append_c (buffer, '&');
  g_string_append (buffer, dtd->ent_buffer1->str);
  g_string_append_c (buffer, ';');

  /* Read the ';' */
  dtd_move_cursor (dtd);
  return ALL_OK;
}


gboolean
dtd_read_value (DTD * dtd, GString * value)
{
  gchar delimiter;

  switch (dtd->cursor_char)
    {
    case '"':
    case '\'':
      delimiter = dtd->cursor_char;
      /* And read it */
      dtd_move_cursor (dtd);
      break;
    default:
      return ERROR;
    }

  g_string_set_size (value, 0);

  for (;;)
    {
      if (dtd->cursor_char == delimiter)
        {
          /* Read the delimiter */
          dtd_move_cursor (dtd);
          return ALL_OK;
        }

      switch (dtd->cursor_char)
        {
        case '\0':
          return ERROR;
        case '&':
          if (dtd_read_entity (dtd, value))
            return ERROR;
          continue;
        case '%':
          if (dtd_read_parameter_entity (dtd))
            return ERROR;
          continue;
        default:
          g_string_append_c (value, dtd->cursor_char);
          dtd_move_cursor (dtd);
          break;
        }
    }
}


gboolean
dtd_ignore_element (DTD * dtd)
{
  /* TODO: handle the string ! */

  /* Search for '>' */
  while (dtd->cursor_char != '>' && dtd->cursor_char != '\0')
    dtd_move_cursor (dtd);

  if (dtd->cursor_char == '\0')
    return ERROR;

  /* Read '>' */
  dtd_move_cursor (dtd);

  return ALL_OK;
}


gboolean
dtd_ignore_comment (DTD * dtd)
{
  if (dtd_move_cursor (dtd) != '-')
    return ERROR;

  for (;;)
    {
      /* Stop condition: "-->" */
      if (dtd_move_cursor (dtd) == '-')
        {
          if (dtd_move_cursor (dtd) == '-')
            {
              if (dtd_move_cursor (dtd) != '>')
                return ERROR;

              /* Read '>' */
              dtd_move_cursor (dtd);

              return ALL_OK;
            }
        }

      /* Something else. */
      if (dtd->cursor_char == '\0')
        return ERROR;
    }
}


gboolean
dtd_read_SYSTEM (DTD * dtd, GString * SystemLiteral)
{
  if (dtd_read_string (dtd, "YSTEM"))
    return ERROR;
  dtd_move_cursor (dtd);

  dtd_read_S (dtd);

  /* Read SystemLiteral */
  if (dtd_read_value (dtd, SystemLiteral))
    return ERROR;

  return ALL_OK;
}


gboolean
dtd_read_PUBLIC (DTD * dtd, GString * PubidLiteral, GString * SystemLiteral)
{
  if (dtd_read_string (dtd, "UBLIC"))
    return ERROR;
  dtd_move_cursor (dtd);

  dtd_read_S (dtd);

  /* Read PubidLiteral */
  if (dtd_read_value (dtd, PubidLiteral))
    return ERROR;

  dtd_read_S (dtd);

  /* Read SystemLiteral */
  if (dtd_read_value (dtd, SystemLiteral))
    return ERROR;

  return ALL_OK;
}


gboolean
dtd_read_EntityDecl (Parser * parser, DTD * dtd)
{
  gboolean PE = FALSE;
  gchar *name, *value;

  /* Read 'ENTITY' */
  if (dtd_read_string (dtd, "TITY"))
    return ERROR;
  dtd_move_cursor (dtd);

  dtd_read_S (dtd);

  /* PE? */
  if (dtd->cursor_char == '%')
    {
      dtd_move_cursor (dtd);
      dtd_read_S (dtd);
      PE = TRUE;
    }

  /* Name */
  dtd_read_Name (dtd, dtd->ent_buffer2);

  dtd_read_S (dtd);

  /* Read the value */
  switch (dtd->cursor_char)
    {
    case '\'':
    case '"':
      /* Read value (in buffer1) */
      if (dtd_read_value (dtd, dtd->buffer1))
        return ERROR;

      dtd_read_S (dtd);

      break;
    case 'S':
      /* SYSTEM => We ignore it */
      if (dtd_read_SYSTEM (dtd, dtd->buffer1))
        return ERROR;

      if (dtd_ignore_element (dtd))
        return ERROR;
      return ALL_OK;
    case 'P':
      /* PUBLIC => read it */
      if (dtd_read_PUBLIC (dtd, dtd->buffer1, dtd->buffer2))
        return ERROR;

      dtd_read_S (dtd);

      /* NDATA (only with GE) ? */
      /* We must ignore it ! */
      if (!PE && dtd->cursor_char == 'N')
        {
          if (dtd_ignore_element (dtd))
            return ERROR;
          return ALL_OK;
        }

      /* Compute the URN */
      parser_compute_urn (dtd->buffer1->str, dtd->buffer2);

      /* And we load the entity */
      if (parser_read_urn (dtd->buffer2->str, dtd->buffer1))
        return ERROR;
      break;
    default:
      return ERROR;
    }

  /* Without NDATA, we must finish to read the '>' */
  if (dtd->cursor_char != '>')
    return ERROR;
  dtd_move_cursor (dtd);

  /* Save */
  if (PE)
    {
      name = g_string_chunk_insert (dtd->PE_storage, dtd->ent_buffer2->str);
      value = g_string_chunk_insert (dtd->PE_storage, dtd->buffer1->str);
      g_hash_table_insert (dtd->PE_table, (gpointer) name, (gpointer) value);
    }
  else
    {
      name = g_string_chunk_insert (parser->strings_storage,
                                    dtd->ent_buffer2->str);
      value = g_string_chunk_insert (parser->strings_storage,
                                     dtd->buffer1->str);
      g_hash_table_insert (parser->GE_table, (gpointer) name,
                           (gpointer) value);
    }
  return ALL_OK;
}


gboolean
parser_read_dtd (Parser * parser, DTD * dtd)
{
  for (;;)
    {
      /* Specific switch */
      if (dtd->is_external)
        switch (dtd->cursor_char)
          {
          case ']':
            return ERROR;
          case '\0':
            return ALL_OK;
          }
      else
        switch (dtd->cursor_char)
          {
          case ']':
            return ALL_OK;
          case '\0':
            return ERROR;
          }

      /* Common switch */
      switch (dtd->cursor_char)
        {
        case '\n':
        case '\r':
        case ' ':
        case '\t':
          /* Read S */
          dtd_move_cursor (dtd);
          continue;
        case '%':
          if (dtd_read_parameter_entity (dtd))
            return ERROR;
          continue;
        case '<':
          if (dtd_move_cursor (dtd) == '!')
            /* '<!' */
            switch (dtd_move_cursor (dtd))
              {
              case '-':
                /* '<!-' */
                if (dtd_ignore_comment (dtd))
                  return ERROR;
                continue;
              case 'E':
                /* '<!E' */
                if (dtd_move_cursor (dtd) == 'N')
                  {
                    /* '<!EN' */
                    if (dtd_read_EntityDecl (parser, dtd))
                      return ERROR;
                    continue;
                  }
              }
          /* The other cases => ignore it */
          if (dtd_ignore_element (dtd))
            return ERROR;
          continue;
        default:
          return ERROR;
        }
    }
}


gboolean
parser_read_external_dtd (Parser * parser, Event * event, gchar * urn)
{
  gchar *dtd_name;
  FILE *file;
  DTD *dtd;

  /* Search for the good file */
  dtd_name = (gchar *) g_hash_table_lookup (parser_URN_table, urn);

  if (!dtd_name)
    {
      g_string_set_size (parser->err_buffer, 0);
      g_string_append (parser->err_buffer, "'");
      g_string_append (parser->err_buffer, urn);
      g_string_append (parser->err_buffer, "' not found");
      return PARSER_ERROR (parser->err_buffer->str);
    }

  /* Open the file */
  file = fopen (dtd_name, "r");
  if (!file)
    {
      g_string_set_size (parser->err_buffer, 0);
      g_string_append (parser->err_buffer, "'");
      g_string_append (parser->err_buffer, dtd_name);
      g_string_append (parser->err_buffer, "' no such file");
      return PARSER_ERROR (parser->err_buffer->str);
    }

  /* Create an appropriated DTD object */
  dtd = dtd_new (NULL, file, TRUE);

  /* And parse it ! */
  if (parser_read_dtd (parser, dtd))
    {
      dtd_free (dtd);
      fclose (file);
      return PARSER_ERROR (BAD_DTD);
    }

  /* ALL OK */
  dtd_free (dtd);
  fclose (file);
  return ALL_OK;
}


gboolean
parser_read_internal_dtd (Parser * parser, Event * event, gchar * data)
{
  DTD *dtd;

  /* Create an appropriated DTD object */
  dtd = dtd_new (data, NULL, FALSE);

  /* Read '<!DOCTYPE S' */
  if (dtd->cursor_char != '<')
    {
      dtd_free (dtd);
      return PARSER_ERROR (BAD_DTD);
    }
  if (dtd_read_string (dtd, "!DOCTYPE"))
    {
      dtd_free (dtd);
      return PARSER_ERROR (BAD_DTD);
    }
  dtd_move_cursor (dtd);
  dtd_read_S (dtd);

  /* Read Name and ignore it */
  dtd_read_Name (dtd, dtd->buffer1);
  dtd_read_S (dtd);

  /* ('SYSTEM' S  SystemLiteral) ? */
  if (dtd->cursor_char == 'S')
    {
      if (dtd_read_SYSTEM (dtd, dtd->buffer1))
        {
          dtd_free (dtd);
          return PARSER_ERROR (BAD_DTD);
        }
      /* And we ignore it! */

      dtd_read_S (dtd);
    }
  else
    /* ('PUBLIC' S PubidLiteral S SystemLiteral) ? */
  if (dtd->cursor_char == 'P')
    {
      if (dtd_read_PUBLIC (dtd, dtd->buffer1, dtd->buffer2))
        {
          dtd_free (dtd);
          return PARSER_ERROR (BAD_DTD);
        }
      /* Read the public doctype thanks its URN */
      /* we ignore its SystemLiteral */

      /* Compute the URN */
      parser_compute_urn (dtd->buffer1->str, dtd->buffer2);

      if (parser_read_external_dtd (parser, event, dtd->buffer2->str))
        {
          dtd_free (dtd);
          return ERROR;
        }

      dtd_read_S (dtd);
    }

  /* intSubset ? */
  if (dtd->cursor_char == '[')
    {
      /* Read the '[' */
      dtd_move_cursor (dtd);

      /* Read the doctype */
      if (parser_read_dtd (parser, dtd))
        return PARSER_ERROR (BAD_DTD);

      /* Read the ']' */
      dtd_move_cursor (dtd);

      dtd_read_S (dtd);
    }

  /* Read '>' */
  if (dtd->cursor_char != '>')
    {
      dtd_free (dtd);
      return PARSER_ERROR (BAD_DTD);
    }
  dtd_move_cursor (dtd);

  /* TODO  now only spaces!!!! */

  /* All OK */
  dtd_free (dtd);
  return ALL_OK;
}


/*****************************
 * General parsing functions *
 *****************************/

gboolean
parser_read_value_entity (Parser * parser, GString * buffer)
{
  gunichar code = 0;

  /* Hexadecimal ? */
  if (move_cursor (parser) == 'x')
    {
      /* Yes */

      /* At least one character! */
      if (move_cursor (parser) == ';')
        return ERROR;

      for (;; move_cursor (parser))
        {
          /* 0 -> 9 */
          if (isdigit (parser->cursor_char))
            {
              code = code * 16 + parser->cursor_char - '0';
              continue;
            }
          /* a -> f */
          if ('a' <= parser->cursor_char && parser->cursor_char <= 'f')
            {
              code = code * 16 + parser->cursor_char - 'a' + 10;
              continue;
            }
          /* A -> F */
          if ('A' <= parser->cursor_char && parser->cursor_char <= 'F')
            {
              code = code * 16 + parser->cursor_char - 'A' + 10;
              continue;
            }
          break;
        }
    }
  else
    {
      /* No => decimal */

      /* At least one character! */
      if (parser->cursor_char == ';')
        return ERROR;

      for (; isdigit (parser->cursor_char); move_cursor (parser))
        {
          code = code * 10 + parser->cursor_char - '0';
          continue;
        }
    }

  /* Read the ';' */
  if (parser->cursor_char != ';')
    return ERROR;
  move_cursor (parser);

  /* From codepoint to str (UTF-8). */
  g_string_append_unichar (buffer, code);

  return ALL_OK;
}


gboolean
parser_read_entity (Parser * parser, GString * buffer)
{
  gpointer value;

  /* By value ? */
  if (move_cursor (parser) == '#')
    return parser_read_value_entity (parser, buffer);

  /* No, so read the entity name */
  g_string_set_size (parser->ent_buffer, 0);
  for (;;)
    {
      switch (parser->cursor_char)
        {
        case ';':
          goto for_end;
        case '\0':
          return ERROR;
        default:
          g_string_append_c (parser->ent_buffer, parser->cursor_char);
        }
      move_cursor (parser);
    }
for_end:

  /* We must find it in the GE_table ! */
  value = g_hash_table_lookup (parser->GE_table, parser->ent_buffer->str);
  if (value)
    {
      parser_stream_push (parser, (gchar *) value);
      return ALL_OK;
    }

  return ERROR;
}


/* After this function,
 * cursor_char = the last character of the expected string
 */
gboolean
parser_read_string (Parser * parser, gchar * expected)
{
  gchar *cursor;
  for (cursor = expected; *cursor != '\0'; cursor++)
    {
      if (*cursor != move_cursor (parser))
        return ERROR;
    }
  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-S
 * Warning, we parse here "S?"
 */
#define parser_read_S(parser) while(isspace((parser)->cursor_char))\
                                {move_cursor(parser);}


/* http://www.w3.org/TR/REC-xml/#dt-comment */
gboolean
parser_read_Comment (Parser * parser, TextEvent * event)
{
  if (move_cursor (parser) != '-')
    return PARSER_ERROR (INVALID_TOKEN);

  g_string_set_size (parser->buffer1, 0);
  for (;;)
    {
      /* Stop condition: "-->" */
      if (move_cursor (parser) == '-')
        {
          if (move_cursor (parser) == '-')
            {
              if (move_cursor (parser) != '>')
                return PARSER_ERROR (INVALID_TOKEN);

              /* Read '>' */
              move_cursor (parser);

              /* All OK */
              event->text = parser->buffer1->str;
              event->type = COMMENT;
              return ALL_OK;
            }
          else
            g_string_append_c (parser->buffer1, '-');
        }

      /* Something else. */
      if (parser->cursor_char == '\0')
        return PARSER_ERROR (INVALID_TOKEN);
      g_string_append_c (parser->buffer1, parser->cursor_char);
    }
}


/* http://www.w3.org/TR/REC-xml/#NT-CDSect */
gboolean
parser_read_CDSect (Parser * parser, TextEvent * event)
{
  if (parser_read_string (parser, "CDATA["))
    return PARSER_ERROR (INVALID_TOKEN);

  g_string_set_size (parser->buffer1, 0);

  for (;;)
    {
      /* Stop condition: "]]>" */
      if (move_cursor (parser) == ']')
        {
          if (move_cursor (parser) == ']')
            {
              if (move_cursor (parser) == '>')
                {
                  /* Read '>' */
                  move_cursor (parser);

                  /* All OK */
                  event->text = parser->buffer1->str;
                  event->type = CDATA;
                  return ALL_OK;
                }
              g_string_append_c (parser->buffer1, ']');
            }
          g_string_append_c (parser->buffer1, ']');
        }

      /* Something else. */
      if (parser->cursor_char == '\0')
        return PARSER_ERROR (INVALID_TOKEN);
      g_string_append_c (parser->buffer1, parser->cursor_char);
    }
}


/* The first character is under cursor_char
 */
void
parser_read_Name (Parser * parser, GString * name)
{
  g_string_set_size (name, 0);

  /* Read as much as possible */
  while (IS_NAME_CHAR (parser->cursor_char))
    {
      g_string_append_c (name, parser->cursor_char);
      move_cursor (parser);
    }
}


gboolean
parser_read_value (Parser * parser, GString * value)
{
  gchar delimiter;

  switch (parser->cursor_char)
    {
    case '"':
    case '\'':
      delimiter = parser->cursor_char;
      /* And read it */
      move_cursor (parser);
      break;
    default:
      return ERROR;
    }

  g_string_set_size (value, 0);

  for (;;)
    {
      if (parser->cursor_char == delimiter)
        {
          /* Read the delimiter */
          move_cursor (parser);
          return ALL_OK;
        }

      switch (parser->cursor_char)
        {
        case '\0':
          return ERROR;
        case '&':
          if (parser_read_entity (parser, value))
            return ERROR;
          continue;
        default:
          g_string_append_c (value, parser->cursor_char);
          move_cursor (parser);
          break;
        }
    }
}


gboolean
parser_read_QName (Parser * parser, gchar ** prefix, gchar ** name)
{
  HStrTree *tree;
  HStrTree *parent;
  gchar *str;

  G_LOCK (parser_global_strings);

  /* Read the prefix. */
  tree = intern_strings_tree;
  while (IS_NC_NAME_CHAR (parser->cursor_char))
    {
      tree = h_str_tree_traverse (tree, parser->cursor_char);
      move_cursor (parser);
    }

  /* Test the string is not missing. */
  if (tree == intern_strings_tree)
    {
      G_UNLOCK (parser_global_strings);
      return ERROR;
    }

  /* Get the value. */
  if (!(tree->data))
    {
      g_string_set_size (parser->ns_buffer, 0);
      parent = tree;
      while (parent->parent)
        {
          g_string_prepend_c (parser->ns_buffer, parent->chr);
          parent = parent->parent;
        }
      str =
        g_string_chunk_insert (parser_global_strings, parser->ns_buffer->str);
      tree->data = str;
    }
  else
    {
      str = tree->data;
    }

  /* Just the name ? */
  if (parser->cursor_char != ':')
    {
      *prefix = intern_empty;
      *name = str;
      G_UNLOCK (parser_global_strings);
      return ALL_OK;
    }

  /* => Prefix = str */
  *prefix = str;

  /* Read the ':' */
  move_cursor (parser);

  /* Read the name */
  tree = intern_strings_tree;
  while (IS_NAME_CHAR (parser->cursor_char))
    {
      tree = h_str_tree_traverse (tree, parser->cursor_char);
      move_cursor (parser);
    }

  /* Test the string is not missing. */
  if (tree == intern_strings_tree)
    {
      G_UNLOCK (parser_global_strings);
      return ERROR;
    }

  /* Get the value. */
  if (!(tree->data))
    {
      g_string_set_size (parser->ns_buffer, 0);
      parent = tree;
      while (parent->parent)
        {
          g_string_prepend_c (parser->ns_buffer, parent->chr);
          parent = parent->parent;
        }
      str =
        g_string_chunk_insert (parser_global_strings, parser->ns_buffer->str);
      tree->data = str;
    }
  else
    {
      str = tree->data;
    }

  /* Store the result */
  *name = str;

  G_UNLOCK (parser_global_strings);
  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-Eq */
gboolean
parser_read_Eq (Parser * parser)
{
  parser_read_S (parser);

  if (parser->cursor_char != '=')
    return ERROR;
  move_cursor (parser);

  parser_read_S (parser);

  return ALL_OK;
}


gboolean
parser_read_STag (Parser * parser, StartTagEvent * event)
{
  Attribute *attribute;
  gint attributes_number = 0;
  gboolean end_tag;
  gint idx;
  gint ns_number = 0;
  Tag *tag;
  gchar *tag_uri, *tag_name;

  /* prefix and name */
  if (parser_read_QName (parser, &tag_uri, &tag_name))
    return PARSER_ERROR (INVALID_TOKEN);

  /* Read the attributes */
  for (;;)
    {
      parser_read_S (parser);

      switch (parser->cursor_char)
        {
        case '/':
          if (move_cursor (parser) != '>')
            return PARSER_ERROR (INVALID_TOKEN);
          move_cursor (parser);
          end_tag = TRUE;
          goto for_end;
        case '>':
          move_cursor (parser);
          end_tag = FALSE;
          goto for_end;
        case '\0':
          return PARSER_ERROR (INVALID_TOKEN);
        default:
          /* New attribute */
          attribute = (Attribute *) arp_get_index (parser->attr_storage,
                                                   attributes_number);

          /* prefix and name */
          if (parser_read_QName (parser, &(attribute->uri),
                                 &(attribute->name)))
            return PARSER_ERROR (INVALID_TOKEN);

          /* Eq */
          if (parser_read_Eq (parser))
            return PARSER_ERROR (INVALID_TOKEN);

          /* Value */
          if (parser_read_value (parser, attribute->value))
            return PARSER_ERROR (INVALID_TOKEN);

          /* Namespaces management */
          /* xmlns="..." => default namespace */
          if (attribute->uri == intern_empty &&
              attribute->name == intern_xmlns)
            {
              ns_number++;
              parser_push_namespace (parser, intern_empty,
                                     attribute->value->str);
              /* XXX: with the continue, this "attribute" is not sent */
              /* continue; */
            }
          /* xmlns:prefix="..." => define a new prefix */
          if (attribute->uri == intern_xmlns)
            {
              ns_number++;
              parser_push_namespace (parser, attribute->name,
                                     attribute->value->str);
              /* XXX: with the continue, this "attribute" is not sent */
              /* continue; */
            }
        }
      attributes_number++;
    }
for_end:

  /* Tag URI/NAME */
  if (tag_uri == intern_empty)
    tag_uri = parser->default_ns;
  else
    {
      tag_uri = parser_search_namespace (parser, tag_uri);
      if (!(tag_uri))
        return PARSER_ERROR (INVALID_NAMESPACE);
    }
  event->uri = tag_uri;
  event->name = tag_name;

  /* Attributes URI */
  for (attribute = (Attribute *) parser->attr_storage->data, idx = 0;
       idx < attributes_number; attribute++, idx++)
    if (attribute->uri != intern_empty)
      {
        attribute->uri = parser_search_namespace (parser, attribute->uri);
        if (!(attribute->uri))
          return PARSER_ERROR (INVALID_NAMESPACE);
      }

  /* Prepare the EndTagEvent */
  if (end_tag)
    {
      /* Delete the namespaces */
      if (ns_number > 0)
        {
          parser->ns_stack_size -= ns_number;
          parser->default_ns = parser_search_namespace (parser, intern_empty);
          if (!(parser->default_ns))
            parser->default_ns = intern_empty;
        }

      /* Make the next event */
      parser->end_tag = TRUE;
      parser->end_tag_uri = tag_uri;
      parser->end_tag_name = tag_name;
    }
  else
    {
      tag =
        (Tag *) arp_get_index (parser->tags_stack, parser->tags_stack_size);

      /* Push the current tag */
      tag->uri = tag_uri;
      tag->name = tag_name;
      tag->ns_number = ns_number;

      (parser->tags_stack_size)++;
    }

  /* All OK */
  event->type = START_ELEMENT;
  event->attributes = (Attribute *) parser->attr_storage->data;
  event->attributes_number = attributes_number;

  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-ETag */
gboolean
parser_read_ETag (Parser * parser, EndTagEvent * event)
{
  Tag *tag;
  gchar *tag_uri, *tag_name;

  /* Read '/' */
  move_cursor (parser);

  /* prefix and name */
  if (parser_read_QName (parser, &tag_uri, &tag_name))
    return PARSER_ERROR (INVALID_TOKEN);

  /* prefix -> URI */
  if (tag_uri == intern_empty)
    tag_uri = parser->default_ns;
  else
    {
      tag_uri = parser_search_namespace (parser, tag_uri);
      if (!(tag_uri))
        return PARSER_ERROR (INVALID_NAMESPACE);
    }

  parser_read_S (parser);

  /* Read '>' */
  if (parser->cursor_char != '>')
    return PARSER_ERROR (INVALID_TOKEN);
  move_cursor (parser);

  /* Pop the tag */
  if (parser->tags_stack_size <= 0)
    return PARSER_ERROR (INVALID_TOKEN);
  (parser->tags_stack_size)--;
  tag = (Tag *) arp_get_index (parser->tags_stack, parser->tags_stack_size);

  /* Verification */
  if (tag_uri != tag->uri || tag_name != tag->name)
    return PARSER_ERROR (INVALID_TOKEN);

  /* Delete the namespaces */
  if (tag->ns_number > 0)
    {
      parser->ns_stack_size -= tag->ns_number;
      parser->default_ns = parser_search_namespace (parser, intern_empty);
      if (!(parser->default_ns))
        parser->default_ns = intern_empty;
    }

  /* All OK */
  event->uri = tag_uri;
  event->name = tag_name;
  event->type = END_ELEMENT;
  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-content */
gboolean
parser_read_content (Parser * parser, TextEvent * event)
{
  g_string_set_size (parser->buffer1, 0);

  for (;;)
    {
      switch (parser->cursor_char)
        {
        case '\0':
        case '<':
          goto for_end;
        case '&':
          if (parser_read_entity (parser, parser->buffer1))
            return PARSER_ERROR (BAD_ENTITY);
          continue;
        default:
          g_string_append_c (parser->buffer1, parser->cursor_char);
          move_cursor (parser);
          break;
        }
    }
for_end:

  /* All OK */
  event->text = parser->buffer1->str;
  event->type = TEXT;
  return ALL_OK;
}


/* http://www.w3.org/TR/REC-xml/#NT-XMLDecl */
gboolean
parser_read_XMLDecl (Parser * parser, DeclEvent * event)
{
  parser_read_S (parser);

  /* Version (in buffer1) */
  if (parser->cursor_char != 'v')
    return PARSER_ERROR (INVALID_TOKEN);
  if (parser_read_string (parser, "ersion"))
    return PARSER_ERROR (INVALID_TOKEN);
  move_cursor (parser);

  if (parser_read_Eq (parser))
    return PARSER_ERROR (INVALID_TOKEN);

  if (parser_read_value (parser, parser->buffer1))
    return PARSER_ERROR (INVALID_TOKEN);

  parser_read_S (parser);

  /* Encoding? (in buffer2) */
  g_string_assign (parser->buffer2, "utf-8");
  if (parser->cursor_char == 'e')
    {
      if (parser_read_string (parser, "ncoding"))
        return PARSER_ERROR (INVALID_TOKEN);
      move_cursor (parser);

      if (parser_read_Eq (parser))
        return PARSER_ERROR (INVALID_TOKEN);

      if (parser_read_value (parser, parser->buffer2))
        return PARSER_ERROR (INVALID_TOKEN);

      parser_read_S (parser);
    }

  /* SDDecl? */
  g_string_set_size (parser->buffer3, 0);
  if (parser->cursor_char == 's')
    {
      if (parser_read_string (parser, "tandalone"))
        return PARSER_ERROR (INVALID_TOKEN);
      move_cursor (parser);

      if (parser_read_Eq (parser))
        return PARSER_ERROR (INVALID_TOKEN);

      if (parser_read_value (parser, parser->buffer3))
        return PARSER_ERROR (INVALID_TOKEN);

      parser_read_S (parser);
    }

  /* Read '?>' */
  if (parser->cursor_char != '?')
    return PARSER_ERROR (INVALID_TOKEN);
  if (move_cursor (parser) != '>')
    return PARSER_ERROR (INVALID_TOKEN);
  move_cursor (parser);

  /* All OK */
  event->version = parser->buffer1->str;
  event->encoding = parser->buffer2->str;
  event->standalone = parser->buffer3->str;
  event->type = XML_DECL;
  return ALL_OK;
}


gboolean
parser_read_PI_or_XMLDecl (Parser * parser, Event * event)
{
  /* Read the '?' */
  move_cursor (parser);

  /* Read the Name */
  parser_read_Name (parser, parser->buffer1);

  if (!strcmp (parser->buffer1->str, "xml"))
    {
      /* XMLDecl */
      return parser_read_XMLDecl (parser, (DeclEvent *) event);
    }

  /* PI */
  parser_read_S (parser);

  /* Read content */
  g_string_set_size (parser->buffer2, 0);
  for (;;)
    {
      /* Stop condition: "?>" */
      if (parser->cursor_char == '?')
        {
          if (move_cursor (parser) == '>')
            {
              /* Read '>' */
              move_cursor (parser);

              /* All OK */
              ((PIEvent *) event)->pi_target = parser->buffer1->str;
              ((PIEvent *) event)->content = parser->buffer2->str;
              event->type = PI;
              return ALL_OK;
            }
          else
            g_string_append_c (parser->buffer2, '?');
        }

      /* Something else. */
      if (parser->cursor_char == '\0')
        return PARSER_ERROR (INVALID_TOKEN);
      g_string_append_c (parser->buffer2, parser->cursor_char);
      move_cursor (parser);
    }
}


/* http://www.w3.org/TR/REC-xml/#NT-doctypedecl */
gboolean
parser_read_doctypedecl (Parser * parser, TextEvent * event)
{
  gint cb_level = 1;
  gchar delimiter;

  /* Make the string */
  g_string_assign (parser->buffer1, "<!D");
  for (;;)
    {
      switch (move_cursor (parser))
        {
        case '\'':
        case '"':
          delimiter = parser->cursor_char;
          g_string_append_c (parser->buffer1, delimiter);
          do
            {
              g_string_append_c (parser->buffer1, move_cursor (parser));
            }
          while (parser->cursor_char != delimiter &&
                 parser->cursor_char != '\0');
          if (parser->cursor_char == '\0')
            return PARSER_ERROR (BAD_DTD);
          break;
        case '>':
          g_string_append_c (parser->buffer1, '>');
          if (--cb_level == 0)
            {
              /* Read the last '>' */
              move_cursor (parser);
              goto for_end;
            }
          break;
        case '<':
          g_string_append_c (parser->buffer1, '<');
          cb_level++;
          break;
        default:
          g_string_append_c (parser->buffer1, parser->cursor_char);
          break;
        }
    }
for_end:

  if (parser_read_internal_dtd
      (parser, (Event *) event, parser->buffer1->str))
    return ERROR;

  /* ALL OK */
  event->text = parser->buffer1->str;
  event->type = DOCUMENT_TYPE;
  return ALL_OK;
}


void
parser_read_BOM (Parser * parser)
{
  /* XXX: We detect only the UTF-8 Byte Order Mark */
  /* If an error occurs the bytes are not replaced in the stream */
  if ((unsigned char) parser->cursor_char == 0xEF)
    if ((unsigned char) move_cursor (parser) == 0xBB)
      if ((unsigned char) move_cursor (parser) == 0xBF)
        move_cursor (parser);
}


/**************************************************************************
 * The API
 *************************************************************************/

Parser *
parser_new (gchar * data, FILE * file)
{
  Parser *parser;

  /* Arguments verification */
  if ((data == NULL && file == NULL) || (data != NULL && file != NULL))
    return NULL;

  /* Initialized ? */
  if (!parser_initialized)
    parser_initialize ();

  /* Memory allocation */
  parser = g_new (Parser, 1);

  /* The Glib objects */
  parser->buffer1 = g_string_sized_new (256);
  parser->buffer2 = g_string_sized_new (256);
  parser->buffer3 = g_string_sized_new (256);
  parser->err_buffer = g_string_sized_new (256);
  parser->strings_storage = g_string_chunk_new (64);
  parser->ns_buffer = g_string_sized_new (256);
  parser->ent_buffer = g_string_sized_new (256);
  parser->GE_table = g_hash_table_new (g_str_hash, g_str_equal);

  /* Streams management */
  parser->streams_stack = arp_new (sizeof (Stream), NULL, NULL);
  parser->streams_stack_size = 0;

  /* Attributes */
  parser->attr_storage = arp_new (sizeof (Attribute), parser_attr_constructor,
                                  parser_attr_destructor);

  /* Tags */
  parser->tags_stack = arp_new (sizeof (Tag), NULL, NULL);
  parser->tags_stack_size = 0;
  parser->end_tag = FALSE;

  /* Namespaces */
  parser->ns_stack = arp_new (sizeof (Namespace), NULL, NULL);
  parser->ns_stack_size = 0;
  parser->default_ns = intern_empty;

  /* Set the default namespaces */
  parser_add_namespace (parser, "xml",
                        "http://www.w3.org/XML/1998/namespace");
  parser_add_namespace (parser, "xmlns", "http://www.w3.org/2000/xmlns/");

  /* Source management */
  parser->source_row = 1;
  parser->source_col = 1;
  parser->new_line = FALSE;
  if (data)
    {
      parser->source.cursor = data;
      parser->source_type = 1;
    }
  else
    {
      parser->source.file = file;
      parser->source_type = 0;
    }
  move_cursor (parser);

  /* Set the default entities */
  parser_set_default_entities (parser);

  /* And read the BOM */
  parser_read_BOM (parser);

  return parser;
}


void
parser_free (Parser * parser)
{
  /* Delete the Glib objects */
  g_string_free (parser->buffer1, TRUE);
  g_string_free (parser->buffer2, TRUE);
  g_string_free (parser->buffer3, TRUE);
  g_string_free (parser->err_buffer, TRUE);
  g_string_chunk_free (parser->strings_storage);
  g_string_free (parser->ns_buffer, TRUE);
  g_string_free (parser->ent_buffer, TRUE);
  g_hash_table_destroy (parser->GE_table);

  /* Delete the arp objects */
  arp_free (parser->streams_stack);
  arp_free (parser->attr_storage);
  arp_free (parser->tags_stack);
  arp_free (parser->ns_stack);

  /* And delete the parser object */
  g_free (parser);
}


void
parser_add_namespace (Parser * parser, gchar * prefix, gchar * uri)
{
  parser_push_namespace (parser, intern_string (prefix), uri);
}


gboolean
parser_add_doctype (Parser * parser, gchar * doctype)
{
  Event event;

  if (parser_read_internal_dtd (parser, &event, doctype))
    return ERROR;

  return ALL_OK;
}


void
parser_register_dtd (gchar * urn, gchar * filename)
{
  /* Initialized ? */
  if (!parser_initialized)
    parser_initialize ();

  /* Append */
  urn = g_string_chunk_insert (parser_global_strings, urn);
  filename = g_string_chunk_insert (parser_global_strings, filename);
  g_hash_table_insert (parser_URN_table, (gpointer) urn, (gpointer) filename);
}


gboolean
parser_next (Parser * parser, Event * event)
{
  /* Event position = starting point of the event in the source */
  event->common_event.row = parser->source_row;
  event->common_event.column = parser->source_col;

  /* End tag ? */
  if (parser->end_tag)
    {
      parser->end_tag = FALSE;

      ((EndTagEvent *) event)->uri = parser->end_tag_uri;
      ((EndTagEvent *) event)->name = parser->end_tag_name;
      event->type = END_ELEMENT;
      return ALL_OK;
    }

  /* Main switch */
  switch (parser->cursor_char)
    {
    case '\0':
      /* The end ? The open tags must be closed. */
      if (parser->tags_stack_size > 0)
        return PARSER_ERROR (MISSING);
      /* All OK */
      event->type = END_DOCUMENT;
      return ALL_OK;
    case '<':
      /* "<" */
      switch (move_cursor (parser))
        {
        case '!':
          /* "<!" */
          switch (move_cursor (parser))
            {
            case '-':
              /* "<!-" */
              return parser_read_Comment (parser, (TextEvent *) event);
            case 'D':
              /* "<!D" => DOCTYPE */
              return parser_read_doctypedecl (parser, (TextEvent *) event);
            case '[':
              /* "<![" */
              return parser_read_CDSect (parser, (TextEvent *) event);
            default:
              return PARSER_ERROR (INVALID_TOKEN);
            }
        case '?':
          return parser_read_PI_or_XMLDecl (parser, event);
        case '/':
          /* "</" */
          return parser_read_ETag (parser, (EndTagEvent *) event);
        default:
          /* "<..." */
          return parser_read_STag (parser, (StartTagEvent *) event);
        }
    default:
      return parser_read_content (parser, (TextEvent *) event);
    }
}


void
parser_global_reset (void)
{
  if (parser_initialized)
    {
      parser_initialized = FALSE;

      g_string_chunk_free (parser_global_strings);
      h_str_tree_free (intern_strings_tree);
      g_hash_table_destroy (parser_URN_table);
    }
}

