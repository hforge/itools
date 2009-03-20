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

#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdio.h>

#include "parser.h"
#include "arp.h"

#define IS_NAME_CHAR(c) \
    (isalnum(c) || (c == '.') || (c == '-') || (c == '_') || (c == ':'))


/**************************************************************************
 *  Error messages
 *************************************************************************/

#define INVALID_TOKEN     "not well-formed (invalid token)"
#define ONLY_PUBLIC       "SYSTEM is not implemented"
#define BAD_ENTITY        "error parsing entity reference"


/**************************************************************************
 *  Global variables
 *************************************************************************/

/* Initialised ? */
gboolean doctype_initialized = FALSE;

/* Error message */
gchar *doctype_error_msg = NULL;

/* To store the URN  and URI => file names table */
GStringChunk *doctype_global_strings;
GHashTable *doctype_URN_table;
GHashTable *doctype_URI_table;


/**************************************************************************
 * Some functions/objects
 *************************************************************************/

/******************
 * DocType object *
 ******************/
struct _DocType
{
  /* General informations */
  gchar *PubidLiteral;
  gchar *SystemLiteral;
  gchar *intSubset;

  /* A buffer to do everything */
  GString *buffer;

  /* To store all the strings */
  GStringChunk *strings_storage;

  /* The general entities */
  GHashTable *GE_table;
};


/******************
 * Some utilities *
 ******************/
#define DOCTYPE_ERROR(msg) doctype_error_msg=msg, ERROR


void
doctype_compute_urn (gchar * source, GString * target)
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
doctype_load_urn (gchar * urn, GString * target)
{
  gchar *urn_filename;
  gchar buffer[256];
  gint size;
  FILE *file;

  /* Search for the good file */
  urn_filename = (gchar *) g_hash_table_lookup (doctype_URN_table, urn);

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

  /* And close the file */
  fclose(file);

  return ALL_OK;
}


/***************************************
 * DTD Declaration / parsing functions *
 ***************************************/
typedef gchar *Stream;
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
            return DOCTYPE_ERROR (BAD_ENTITY);
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
dtd_read_EntityDecl (DocType * doctype, DTD * dtd)
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
      doctype_compute_urn (dtd->buffer1->str, dtd->buffer2);

      /* And we load the entity */
      if (doctype_load_urn (dtd->buffer2->str, dtd->buffer1))
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
      name = g_string_chunk_insert (doctype->strings_storage,
                                    dtd->ent_buffer2->str);
      value = g_string_chunk_insert (doctype->strings_storage,
                                     dtd->buffer1->str);
      g_hash_table_insert (doctype->GE_table, (gpointer) name,
                           (gpointer) value);
    }
  return ALL_OK;
}


gboolean
dtd_parse (DocType * doctype, DTD * dtd)
{
  for (;;)
    switch (dtd->cursor_char)
      {
      case '\n':
      case '\r':
      case ' ':
      case '\t':
        /* Read S */
        dtd_move_cursor (dtd);
        continue;
      case '\0':
        /* The end */
        return ALL_OK;
      case '%':
        if (dtd_read_parameter_entity (dtd))
          return DOCTYPE_ERROR ("DTD Error: expected parameter entity");
        continue;
      case '<':
        if (dtd_move_cursor (dtd) == '!')
          /* '<!' */
          switch (dtd_move_cursor (dtd))
            {
            case '-':
              /* '<!-' */
              if (dtd_ignore_comment (dtd))
                return DOCTYPE_ERROR ("DTD Error: ignoring comment failed");
              continue;
            case 'E':
              /* '<!E' */
              if (dtd_move_cursor (dtd) == 'N')
                {
                  /* '<!EN' */
                  if (dtd_read_EntityDecl (doctype, dtd))
                    return DOCTYPE_ERROR ("DTD Error: expected entity decl");
                  continue;
                }
            }
        /* The other cases => ignore it */
        if (dtd_ignore_element (dtd))
          return DOCTYPE_ERROR ("DTD Error: ignoring element failed");
        continue;
      default:
        return DOCTYPE_ERROR ("DTD Error: unexpected char");
      }
}


/**************************************************************************
 * DocType private API
 *************************************************************************/

void
doctype_initialize (void)
{
  if (!doctype_initialized)
    {
      doctype_global_strings = g_string_chunk_new (64);
      doctype_URN_table = g_hash_table_new (g_str_hash, g_str_equal);
      doctype_URI_table = g_hash_table_new (g_str_hash, g_str_equal);

      doctype_initialized = TRUE;
    }
}


gboolean
doctype_read_external_dtd (DocType * doctype, gchar * PubidLiteral,
                           gchar * SystemLiteral)
{
  gchar *filename=NULL;
  FILE *file;
  GString *err_buffer;
  gchar *error_msg;
  DTD *dtd;
  gboolean status;

  /* Store the values */
  if (PubidLiteral)
      doctype->PubidLiteral = g_string_chunk_insert (doctype->strings_storage,
                                                     PubidLiteral);
  if (SystemLiteral)
    doctype->SystemLiteral = g_string_chunk_insert (doctype->strings_storage,
                                                    SystemLiteral);

  /* Search for the good file */

  /* With PubidLiteral */
  if (PubidLiteral)
    {
      /* Compute the URN */
      doctype_compute_urn (PubidLiteral, doctype->buffer);

      filename = (gchar *) g_hash_table_lookup (doctype_URN_table,
                                                doctype->buffer->str);
    }

  /* With SystemLiteral */
  if (!filename && SystemLiteral)
  {
      /* Search for the good file */
      filename = (gchar *) g_hash_table_lookup (doctype_URI_table,
                                                SystemLiteral);
  }

  /* Not found ! */
  if (!filename)
    {
      err_buffer = g_string_sized_new (256);
      g_string_set_size (err_buffer, 0);
      g_string_append (err_buffer, "'");
      if (PubidLiteral)
        {
          g_string_append (err_buffer, PubidLiteral);
          g_string_append (err_buffer, " (");
          g_string_append (err_buffer, doctype->buffer->str);
          g_string_append_c (err_buffer, ')');
        }
      else
        g_string_append (err_buffer, "None");
      g_string_append_c (err_buffer, '|');
      if (SystemLiteral)
        g_string_append (err_buffer, SystemLiteral);
      else
        g_string_append (err_buffer, "None");
      g_string_append (err_buffer, "' not found");

      error_msg = g_string_chunk_insert (doctype_global_strings,
                                         err_buffer->str);

      g_string_free (err_buffer, TRUE);

      return DOCTYPE_ERROR (error_msg);
    }

  /* Open the file */
  file = fopen (filename, "r");
  if (!file)
    {
      err_buffer = g_string_sized_new (256);
      g_string_set_size (err_buffer, 0);
      g_string_append (err_buffer, "Error opening file (");
      g_string_append (err_buffer, filename);
      g_string_append (err_buffer, "): ");
      g_string_append (err_buffer, strerror (errno));

      error_msg = g_string_chunk_insert (doctype_global_strings,
                                         err_buffer->str);

      g_string_free (err_buffer, TRUE);

      return DOCTYPE_ERROR (error_msg);
    }

  /* Create an appropriated DTD object */
  dtd = dtd_new (NULL, file, TRUE);

  /* And parse it ! */
  status = dtd_parse (doctype, dtd);
  dtd_free (dtd);
  fclose (file);
  return status;
}


gboolean
doctype_read_internal_dtd (DocType * doctype, gchar * intSubset)
{
  DTD *dtd;
  gboolean status;

  /* Store the value */
  doctype->intSubset = g_string_chunk_insert (doctype->strings_storage,
                                              intSubset);

  /* Create an appropriated DTD object */
  dtd = dtd_new (intSubset, NULL, FALSE);

  /* And parse it ! */
  status = dtd_parse (doctype, dtd);
  dtd_free (dtd);
  return status;
}


/**************************************************************************
 * DocType public API
 *************************************************************************/

DocType *
doctype_new (gchar * PubidLiteral, gchar * SystemLiteral, gchar * intSubset,
             gchar ** error_msg)
{
  DocType *doctype;

  /* Initialized ? */
  if (!doctype_initialized)
    doctype_initialize ();

  /* Memory allocation */
  doctype = g_new0 (DocType, 1);

  /* The Glib objects */
  doctype->buffer = g_string_sized_new (256);
  doctype->strings_storage = g_string_chunk_new (64);
  doctype->GE_table = g_hash_table_new (g_str_hash, g_str_equal);

  /* PubidLiteral or SystemLiteral ? */
  if (PubidLiteral || SystemLiteral)
    if (doctype_read_external_dtd (doctype, PubidLiteral, SystemLiteral))
      goto error;

  /* An intSubset ? */
  if (intSubset)
    if (doctype_read_internal_dtd (doctype, intSubset))
      goto error;

  /* ALL OK */
  *error_msg = NULL;
  return doctype;

error:
  *error_msg = doctype_error_msg;
  doctype_free (doctype);
  return NULL;
}


void
doctype_free (DocType * doctype)
{
  /* Delete the Glib objects */
  g_string_free (doctype->buffer, TRUE);
  g_string_chunk_free (doctype->strings_storage);
  g_hash_table_destroy (doctype->GE_table);

  /* And delete the DocType object */
  g_free (doctype);
}


gchar *
doctype_to_str (DocType * doctype)
{
  g_string_set_size (doctype->buffer, 0);

  /* PUBLIC or SYSTEM ? */
  if (doctype->PubidLiteral || doctype->SystemLiteral)
    {
      if (doctype->PubidLiteral)
        {
          /* PUBLIC */
          g_string_append (doctype->buffer, "PUBLIC \"");
          g_string_append (doctype->buffer, doctype->PubidLiteral);
          g_string_append (doctype->buffer, "\" \"");
          g_string_append (doctype->buffer, doctype->SystemLiteral);
          g_string_append (doctype->buffer, "\"");
        }
      else
        {
          /* SYSTEM */
          g_string_append (doctype->buffer, "SYSTEM \"");
          g_string_append (doctype->buffer, doctype->SystemLiteral);
          g_string_append (doctype->buffer, "\"");
        }

      /* A space between PUBLIC/SYSTEM and intSubset */
      if (doctype->intSubset)
        g_string_append_c (doctype->buffer, ' ');
    }

  /* intSubset ? */
  if (doctype->intSubset)
    {
      g_string_append_c (doctype->buffer, '[');
      g_string_append (doctype->buffer, doctype->intSubset);
      g_string_append_c (doctype->buffer, ']');
    }

  return doctype->buffer->str;
}


gchar *
doctype_get_entity_value (DocType * doctype, gchar * entity_name)
{
  return (gchar *) g_hash_table_lookup (doctype->GE_table, entity_name);
}


void
doctype_register_dtd (gchar * filename, gchar * urn, gchar * uri)
{
  /* Initialized ? */
  if (!doctype_initialized)
    doctype_initialize ();

  /* Append */
  filename = g_string_chunk_insert (doctype_global_strings, filename);
  if (urn)
  {
    urn = g_string_chunk_insert (doctype_global_strings, urn);
    g_hash_table_insert (doctype_URN_table, (gpointer) urn,
                         (gpointer) filename);
  }
  if (uri)
  {
    uri = g_string_chunk_insert (doctype_global_strings, uri);
    g_hash_table_insert (doctype_URI_table, (gpointer) uri,
                         (gpointer) filename);
  }
}


void
doctype_global_reset (void)
{
  if (doctype_initialized)
    {
      doctype_initialized = FALSE;

      g_string_chunk_free (doctype_global_strings);
      g_hash_table_destroy (doctype_URN_table);
      g_hash_table_destroy (doctype_URI_table);
    }
}
