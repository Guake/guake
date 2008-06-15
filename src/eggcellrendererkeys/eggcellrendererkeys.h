/* gtkcellrendererkeybinding.h
 * Copyright (C) 2000  Red Hat, Inc.,  Jonathan Blandford <jrb@redhat.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifndef __EGG_CELL_RENDERER_KEYS_H__
#define __EGG_CELL_RENDERER_KEYS_H__

#include <gtk/gtkcellrenderertext.h>
#include "eggaccelerators.h"

G_BEGIN_DECLS

#define EGG_TYPE_CELL_RENDERER_KEYS		(egg_cell_renderer_keys_get_type ())
#define EGG_CELL_RENDERER_KEYS(obj)		(GTK_CHECK_CAST ((obj), EGG_TYPE_CELL_RENDERER_KEYS, EggCellRendererKeys))
#define EGG_CELL_RENDERER_KEYS_CLASS(klass)	(GTK_CHECK_CLASS_CAST ((klass), EGG_TYPE_CELL_RENDERER_KEYS, EggCellRendererKeysClass))
#define EGG_IS_CELL_RENDERER_KEYS(obj)		(GTK_CHECK_TYPE ((obj), EGG_TYPE_CELL_RENDERER_KEYS))
#define EGG_IS_CELL_RENDERER_KEYS_CLASS(klass)	(GTK_CHECK_CLASS_TYPE ((klass), EGG_TYPE_CELL_RENDERER_KEYS))
#define EGG_CELL_RENDERER_KEYS_GET_CLASS(obj)   (GTK_CHECK_GET_CLASS ((obj), EGG_TYPE_CELL_RENDERER_KEYS, EggCellRendererKeysClass))

typedef struct _EggCellRendererKeys      EggCellRendererKeys;
typedef struct _EggCellRendererKeysClass EggCellRendererKeysClass;


typedef enum
{
  EGG_CELL_RENDERER_KEYS_MODE_GTK,
  EGG_CELL_RENDERER_KEYS_MODE_X
} EggCellRendererKeysMode;

struct _EggCellRendererKeys
{
  GtkCellRendererText parent;
  guint accel_key;
  guint keycode;
  EggVirtualModifierType accel_mask;
  GtkWidget *edit_widget;
  GtkWidget *grab_widget;
  guint edit_key;
  GtkWidget *sizing_label;
  EggCellRendererKeysMode accel_mode;
};

struct _EggCellRendererKeysClass
{
  GtkCellRendererTextClass parent_class;

  void (* accel_edited) (EggCellRendererKeys    *keys,
			 const char             *path_string,
			 guint                   keyval,
			 EggVirtualModifierType  mask,
			 guint                   hardware_keycode);

  void (* accel_cleared) (EggCellRendererKeys    *keys,
			  const char             *path_string);
};

GType            egg_cell_renderer_keys_get_type        (void);
GtkCellRenderer *egg_cell_renderer_keys_new             (void);

void             egg_cell_renderer_keys_set_accelerator (EggCellRendererKeys     *keys,
							 guint                    keyval,
							 guint                    keycode,
							 EggVirtualModifierType   mask);
void             egg_cell_renderer_keys_get_accelerator (EggCellRendererKeys     *keys,
							 guint                   *keyval,
							 EggVirtualModifierType  *mask);
void             egg_cell_renderer_keys_set_accel_mode  (EggCellRendererKeys     *keys,
							 EggCellRendererKeysMode  accel_mode);


G_END_DECLS


#endif /* __GTK_CELL_RENDERER_KEYS_H__ */
