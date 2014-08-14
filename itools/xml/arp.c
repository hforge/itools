/*
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

#include "arp.h"


/**************************************************************************
 * The Arp public API
 *************************************************************************/

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

