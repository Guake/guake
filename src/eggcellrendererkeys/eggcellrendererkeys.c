#include <config.h>
#include <libintl.h>
#include <gtk/gtk.h>
#include <gdk/gdkx.h>
#include <gdk/gdkkeysyms.h>
#include "eggcellrendererkeys.h"
#include "eggaccelerators.h"

#ifndef EGG_COMPILATION
#ifndef _
#define _(x) dgettext (GETTEXT_PACKAGE, x)
#define N_(x) x
#endif
#else
#define _(x) x
#define N_(x) x
#endif

#define EGG_CELL_RENDERER_TEXT_PATH "egg-cell-renderer-text"

#define TOOLTIP_TEXT _("New accelerator...")

static void             egg_cell_renderer_keys_finalize      (GObject             *object);
static void             egg_cell_renderer_keys_init          (EggCellRendererKeys *cell_keys);
static void             egg_cell_renderer_keys_class_init    (EggCellRendererKeysClass *cell_keys_class);
static GtkCellEditable *egg_cell_renderer_keys_start_editing (GtkCellRenderer          *cell,
							      GdkEvent                 *event,
							      GtkWidget                *widget,
							      const gchar              *path,
							      GdkRectangle             *background_area,
							      GdkRectangle             *cell_area,
							      GtkCellRendererState      flags);


static void egg_cell_renderer_keys_get_property (GObject         *object,
						 guint            param_id,
						 GValue          *value,
						 GParamSpec      *pspec);
static void egg_cell_renderer_keys_set_property (GObject         *object,
						 guint            param_id,
						 const GValue    *value,
						 GParamSpec      *pspec);
static void egg_cell_renderer_keys_get_size     (GtkCellRenderer *cell,
						 GtkWidget       *widget,
						 GdkRectangle    *cell_area,
						 gint            *x_offset,
						 gint            *y_offset,
						 gint            *width,
						 gint            *height);


enum {
  PROP_0,

  PROP_ACCEL_KEY,
  PROP_ACCEL_MASK,
  PROP_KEYCODE,
  PROP_ACCEL_MODE
};

static GtkCellRendererTextClass *parent_class = NULL;

GType
egg_cell_renderer_keys_get_type (void)
{
  static GType cell_keys_type = 0;

  if (!cell_keys_type)
    {
      static const GTypeInfo cell_keys_info =
      {
        sizeof (EggCellRendererKeysClass),
	NULL,		/* base_init */
	NULL,		/* base_finalize */
        (GClassInitFunc)egg_cell_renderer_keys_class_init,
	NULL,		/* class_finalize */
	NULL,		/* class_data */
        sizeof (EggCellRendererKeys),
	0,              /* n_preallocs */
        (GInstanceInitFunc) egg_cell_renderer_keys_init
      };

      cell_keys_type = g_type_register_static (GTK_TYPE_CELL_RENDERER_TEXT, "EggCellRendererKeys", &cell_keys_info, 0);
    }

  return cell_keys_type;
}

static void
egg_cell_renderer_keys_init (EggCellRendererKeys *cell_keys)
{
  cell_keys->accel_mode = EGG_CELL_RENDERER_KEYS_MODE_GTK;
}

/* FIXME setup stuff to generate this */
/* VOID:STRING,UINT,FLAGS,UINT */
static void
marshal_VOID__STRING_UINT_FLAGS_UINT (GClosure     *closure,
                                      GValue       *return_value,
				      guint         n_param_values,
				      const GValue *param_values,
				      gpointer      invocation_hint,
				      gpointer      marshal_data)
{
  typedef void (*GMarshalFunc_VOID__STRING_UINT_FLAGS_UINT) (gpointer     data1,
                                                             const char  *arg_1,
							     guint        arg_2,
							     int          arg_3,
							     guint        arg_4,
							     gpointer     data2);
  register GMarshalFunc_VOID__STRING_UINT_FLAGS_UINT callback;
  register GCClosure *cc = (GCClosure*) closure;
  register gpointer data1, data2;

  g_return_if_fail (n_param_values == 5);

  if (G_CCLOSURE_SWAP_DATA (closure))
    {
      data1 = closure->data;
      data2 = g_value_peek_pointer (param_values + 0);
    }
  else
    {
      data1 = g_value_peek_pointer (param_values + 0);
      data2 = closure->data;
    }
  
  callback = (GMarshalFunc_VOID__STRING_UINT_FLAGS_UINT) (marshal_data ? marshal_data : cc->callback);

  callback (data1,
            g_value_get_string (param_values + 1),
            g_value_get_uint (param_values + 2),
            g_value_get_flags (param_values + 3),
	    g_value_get_uint (param_values + 4),
            data2);
}

static void
egg_cell_renderer_keys_class_init (EggCellRendererKeysClass *cell_keys_class)
{
  GObjectClass *object_class;
  GtkCellRendererClass *cell_renderer_class;

  object_class = G_OBJECT_CLASS (cell_keys_class);
  cell_renderer_class = GTK_CELL_RENDERER_CLASS (cell_keys_class);
  parent_class = g_type_class_peek_parent (object_class);
  
  GTK_CELL_RENDERER_CLASS (cell_keys_class)->start_editing = egg_cell_renderer_keys_start_editing;

  object_class->set_property = egg_cell_renderer_keys_set_property;
  object_class->get_property = egg_cell_renderer_keys_get_property;
  cell_renderer_class->get_size = egg_cell_renderer_keys_get_size;

  object_class->finalize = egg_cell_renderer_keys_finalize;
  
  /* FIXME if this gets moved to a real library, rename the properties
   * to match whatever the GTK convention is
   */
  
  g_object_class_install_property (object_class,
                                   PROP_ACCEL_KEY,
                                   g_param_spec_uint ("accel_key",
                                                     _("Accelerator key"),
                                                     _("Accelerator key"),
                                                      0,
                                                      G_MAXINT,
                                                      0,
                                                      G_PARAM_READABLE | G_PARAM_WRITABLE));

  g_object_class_install_property (object_class,
                                   PROP_ACCEL_MASK,
                                   g_param_spec_flags ("accel_mask",
                                                       _("Accelerator modifiers"),
                                                       _("Accelerator modifiers"),
                                                       GDK_TYPE_MODIFIER_TYPE,
                                                       0,
                                                       G_PARAM_READABLE | G_PARAM_WRITABLE));

  g_object_class_install_property (object_class,
		  		   PROP_KEYCODE,
				   g_param_spec_uint ("keycode",
					   	      _("Accelerator keycode"),
						      _("Accelerator keycode"),
						      0,
						      G_MAXINT,
						      0,
						      G_PARAM_READABLE | G_PARAM_WRITABLE));
  
  /* FIXME: Register the enum when moving to GTK+ */
  g_object_class_install_property (object_class,
                                   PROP_ACCEL_MODE,
                                   g_param_spec_int ("accel_mode",
						     _("Accel Mode"),
						     _("The type of accelerator."),
						     0,
						     2,
						     0,
						     G_PARAM_READABLE | G_PARAM_WRITABLE));
  
  g_signal_new ("accel_edited",
                EGG_TYPE_CELL_RENDERER_KEYS,
                G_SIGNAL_RUN_LAST,
                G_STRUCT_OFFSET (EggCellRendererKeysClass, accel_edited),
                NULL, NULL,
                marshal_VOID__STRING_UINT_FLAGS_UINT,
                G_TYPE_NONE, 4,
                G_TYPE_STRING,
                G_TYPE_UINT,
                GDK_TYPE_MODIFIER_TYPE,
		G_TYPE_UINT);

  g_signal_new ("accel_cleared",
                EGG_TYPE_CELL_RENDERER_KEYS,
                G_SIGNAL_RUN_LAST,
                G_STRUCT_OFFSET (EggCellRendererKeysClass, accel_cleared),
                NULL, NULL,
                gtk_marshal_VOID__STRING,
                G_TYPE_NONE, 1,
		G_TYPE_STRING);
}


GtkCellRenderer *
egg_cell_renderer_keys_new (void)
{
  return GTK_CELL_RENDERER (g_object_new (EGG_TYPE_CELL_RENDERER_KEYS, NULL));
}

static void
egg_cell_renderer_keys_finalize (GObject *object)
{
  
  (* G_OBJECT_CLASS (parent_class)->finalize) (object);
}

static gchar *
convert_keysym_state_to_string (guint                  keysym,
				guint		       keycode,
                                EggVirtualModifierType mask)
{
  if (keysym == 0 && keycode == 0)
    return g_strdup (_("Disabled"));
  else
    return egg_virtual_accelerator_label (keysym, keycode, mask);
}

static void
egg_cell_renderer_keys_get_property  (GObject                  *object,
                                      guint                     param_id,
                                      GValue                   *value,
                                      GParamSpec               *pspec)
{
  EggCellRendererKeys *keys;

  g_return_if_fail (EGG_IS_CELL_RENDERER_KEYS (object));

  keys = EGG_CELL_RENDERER_KEYS (object);
  
  switch (param_id)
    {
    case PROP_ACCEL_KEY:
      g_value_set_uint (value, keys->accel_key);
      break;

    case PROP_ACCEL_MASK:
      g_value_set_flags (value, keys->accel_mask);
      break;

    case PROP_ACCEL_MODE:
      g_value_set_int (value, keys->accel_mode);
      break;

    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, param_id, pspec);
    }
}

static void
egg_cell_renderer_keys_set_property  (GObject                  *object,
                                      guint                     param_id,
                                      const GValue             *value,
                                      GParamSpec               *pspec)
{
  EggCellRendererKeys *keys;

  g_return_if_fail (EGG_IS_CELL_RENDERER_KEYS (object));

  keys = EGG_CELL_RENDERER_KEYS (object);
  
  switch (param_id)
    {
    case PROP_ACCEL_KEY:
      egg_cell_renderer_keys_set_accelerator (keys,
                                              g_value_get_uint (value),
					      keys->keycode,
                                              keys->accel_mask);
      break;

    case PROP_ACCEL_MASK:
      egg_cell_renderer_keys_set_accelerator (keys,
                                              keys->accel_key,
					      keys->keycode,
                                              g_value_get_flags (value));
      break;
    case PROP_KEYCODE:
      egg_cell_renderer_keys_set_accelerator (keys,
		      			      keys->accel_key,
					      g_value_get_uint (value),
					      keys->accel_mask);
      break;

    case PROP_ACCEL_MODE:
      egg_cell_renderer_keys_set_accel_mode (keys, g_value_get_int (value));
      break;
      
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, param_id, pspec);
    }
}

static gboolean 
is_modifier (guint keycode)
{
  gint i;
  gint map_size;
  XModifierKeymap *mod_keymap;
  gboolean retval = FALSE;

  mod_keymap = XGetModifierMapping (gdk_display);

  map_size = 8 * mod_keymap->max_keypermod;
  i = 0;
  while (i < map_size)
    {
      if (keycode == mod_keymap->modifiermap[i])
        {
          retval = TRUE;
          break;
        }
      ++i;
    }

  XFreeModifiermap (mod_keymap);

  return retval;
}

static void
egg_cell_renderer_keys_get_size (GtkCellRenderer *cell,
				 GtkWidget       *widget,
				 GdkRectangle    *cell_area,
				 gint            *x_offset,
				 gint            *y_offset,
				 gint            *width,
				 gint            *height)

{
  EggCellRendererKeys *keys = (EggCellRendererKeys *) cell;
  GtkRequisition requisition;

  if (keys->sizing_label == NULL)
    keys->sizing_label = gtk_label_new (TOOLTIP_TEXT);

  gtk_widget_size_request (keys->sizing_label, &requisition);
  (* GTK_CELL_RENDERER_CLASS (parent_class)->get_size) (cell, widget, cell_area, x_offset, y_offset, width, height);
  /* FIXME: need to take the cell_area et al. into account */
  if (width)
    *width = MAX (*width, requisition.width);
  if (height)
    *height = MAX (*height, requisition.height);
}

/* FIXME: Currently we don't differentiate between a 'bogus' key (like tab in
 * GTK mode) and a removed key.
 */
   
static gboolean
grab_key_callback (GtkWidget    *widget,
                   GdkEventKey  *event,
                   void         *data)
{
  GdkModifierType accel_mods = 0;
  guint accel_keyval;
  EggCellRendererKeys *keys;
  char *path;
  gboolean edited;
  gboolean cleared;
  GdkModifierType consumed_modifiers;  
  guint upper;
  GdkModifierType ignored_modifiers;
  
  keys = EGG_CELL_RENDERER_KEYS (data);

  if (is_modifier (event->hardware_keycode))
    return TRUE;

  edited = FALSE;
  cleared = FALSE;

  consumed_modifiers = 0;
  gdk_keymap_translate_keyboard_state (gdk_keymap_get_default (),
				       event->hardware_keycode,
                                       event->state,
                                       event->group,
				       NULL, NULL, NULL, &consumed_modifiers);

  upper = event->keyval;
  accel_keyval = gdk_keyval_to_lower (upper);
  if (accel_keyval == GDK_ISO_Left_Tab) 
    accel_keyval = GDK_Tab;


  
  /* Put shift back if it changed the case of the key, not otherwise.
   */
  if (upper != accel_keyval &&
      (consumed_modifiers & GDK_SHIFT_MASK))
    {
      consumed_modifiers &= ~(GDK_SHIFT_MASK);
    }

  egg_keymap_resolve_virtual_modifiers (gdk_keymap_get_default (),
                                        EGG_VIRTUAL_NUM_LOCK_MASK |
                                        EGG_VIRTUAL_SCROLL_LOCK_MASK |
                                        EGG_VIRTUAL_LOCK_MASK,
                                        &ignored_modifiers);
  
  /* http://bugzilla.gnome.org/show_bug.cgi?id=139605
   * mouse keys should effect keybindings */
  ignored_modifiers |=	GDK_BUTTON1_MASK |
			GDK_BUTTON2_MASK |
			GDK_BUTTON3_MASK |
			GDK_BUTTON4_MASK |
			GDK_BUTTON5_MASK;

  /* filter consumed/ignored modifiers */

  if (keys->accel_mode == EGG_CELL_RENDERER_KEYS_MODE_GTK)
    accel_mods = event->state & GDK_MODIFIER_MASK & ~(consumed_modifiers | ignored_modifiers);
  else if (keys->accel_mode == EGG_CELL_RENDERER_KEYS_MODE_X)
    accel_mods = event->state & GDK_MODIFIER_MASK & ~(ignored_modifiers);
  else
    g_assert_not_reached ();
    
  if (accel_mods == 0 && accel_keyval == GDK_Escape)
    goto out; /* cancel */

  /* clear the accelerator on Backspace */
  if (accel_mods == 0 && accel_keyval == GDK_BackSpace)
    {
      cleared = TRUE;
      goto out;
    }

  if (keys->accel_mode == EGG_CELL_RENDERER_KEYS_MODE_GTK)
    {
      if (!gtk_accelerator_valid (accel_keyval, accel_mods))
	{
	  accel_keyval = 0;
	  accel_mods = 0;
	}
    }
  
  edited = TRUE;
 out:
  gdk_keyboard_ungrab (event->time);
  gdk_pointer_ungrab (event->time);
  
  path = g_strdup (g_object_get_data (G_OBJECT (keys->edit_widget), EGG_CELL_RENDERER_TEXT_PATH));

  gtk_cell_editable_editing_done (GTK_CELL_EDITABLE (keys->edit_widget));
  gtk_cell_editable_remove_widget (GTK_CELL_EDITABLE (keys->edit_widget));
  keys->edit_widget = NULL;
  keys->grab_widget = NULL;
  
  if (edited)
    {
      g_signal_emit_by_name (G_OBJECT (keys), "accel_edited", path,
			     accel_keyval, accel_mods, event->hardware_keycode);
    }
  else if (cleared)
    {
      g_signal_emit_by_name (G_OBJECT (keys), "accel_cleared", path);
    }

  g_free (path);
  return TRUE;
}

static void
ungrab_stuff (GtkWidget *widget, gpointer data)
{
  EggCellRendererKeys *keys = EGG_CELL_RENDERER_KEYS (data);

  gdk_keyboard_ungrab (GDK_CURRENT_TIME);
  gdk_pointer_ungrab (GDK_CURRENT_TIME);

  g_signal_handlers_disconnect_by_func (G_OBJECT (keys->grab_widget),
                                        G_CALLBACK (grab_key_callback), data);
}

static void
pointless_eventbox_start_editing (GtkCellEditable *cell_editable,
                                  GdkEvent        *event)
{
  /* do nothing, because we are pointless */
}

static void
pointless_eventbox_cell_editable_init (GtkCellEditableIface *iface)
{
  iface->start_editing = pointless_eventbox_start_editing;
}

static GType
pointless_eventbox_subclass_get_type (void)
{
  static GType eventbox_type = 0;

  if (!eventbox_type)
    {
      static const GTypeInfo eventbox_info =
      {
        sizeof (GtkEventBoxClass),
	NULL,		/* base_init */
	NULL,		/* base_finalize */
        NULL,
	NULL,		/* class_finalize */
	NULL,		/* class_data */
        sizeof (GtkEventBox),
	0,              /* n_preallocs */
        (GInstanceInitFunc) NULL,
      };

      static const GInterfaceInfo cell_editable_info = {
        (GInterfaceInitFunc) pointless_eventbox_cell_editable_init,
        NULL, NULL };

      eventbox_type = g_type_register_static (GTK_TYPE_EVENT_BOX, "EggCellEditableEventBox", &eventbox_info, 0);
      
      g_type_add_interface_static (eventbox_type,
				   GTK_TYPE_CELL_EDITABLE,
				   &cell_editable_info);
    }

  return eventbox_type;
}

static GtkCellEditable *
egg_cell_renderer_keys_start_editing (GtkCellRenderer      *cell,
				      GdkEvent             *event,
				      GtkWidget            *widget,
				      const gchar          *path,
				      GdkRectangle         *background_area,
				      GdkRectangle         *cell_area,
				      GtkCellRendererState  flags)
{
  GtkCellRendererText *celltext;
  EggCellRendererKeys *keys;
  GtkWidget *label;
  GtkWidget *eventbox;
  
  celltext = GTK_CELL_RENDERER_TEXT (cell);
  keys = EGG_CELL_RENDERER_KEYS (cell);
  
  /* If the cell isn't editable we return NULL. */
  if (celltext->editable == FALSE)
    return NULL;

  g_return_val_if_fail (widget->window != NULL, NULL);
  
  if (gdk_keyboard_grab (widget->window, FALSE,
                         gdk_event_get_time (event)) != GDK_GRAB_SUCCESS)
    return NULL;

  if (gdk_pointer_grab (widget->window, FALSE,
                        GDK_BUTTON_PRESS_MASK,
                        NULL, NULL,
                        gdk_event_get_time (event)) != GDK_GRAB_SUCCESS)
    {
      gdk_keyboard_ungrab (gdk_event_get_time (event));
      return NULL;
    }
  
  keys->grab_widget = widget;

  g_signal_connect (G_OBJECT (widget), "key_press_event",
                    G_CALLBACK (grab_key_callback),
                    keys);

  eventbox = g_object_new (pointless_eventbox_subclass_get_type (),
                           NULL);
  keys->edit_widget = eventbox;
  g_object_add_weak_pointer (G_OBJECT (keys->edit_widget),
                             (void**) &keys->edit_widget);
  
  label = gtk_label_new (NULL);
  gtk_misc_set_alignment (GTK_MISC (label), 0.0, 0.5);
  
  gtk_widget_modify_bg (eventbox, GTK_STATE_NORMAL,
                        &widget->style->bg[GTK_STATE_SELECTED]);

  gtk_widget_modify_fg (label, GTK_STATE_NORMAL,
                        &widget->style->fg[GTK_STATE_SELECTED]);
  
  gtk_label_set_text (GTK_LABEL (label),
		  TOOLTIP_TEXT);

  gtk_container_add (GTK_CONTAINER (eventbox), label);
  
  g_object_set_data_full (G_OBJECT (keys->edit_widget), EGG_CELL_RENDERER_TEXT_PATH,
                          g_strdup (path), g_free);
  
  gtk_widget_show_all (keys->edit_widget);

  g_signal_connect (G_OBJECT (keys->edit_widget), "unrealize",
                    G_CALLBACK (ungrab_stuff), keys);
  
  keys->edit_key = keys->accel_key;
  
  return GTK_CELL_EDITABLE (keys->edit_widget);
}

void
egg_cell_renderer_keys_set_accelerator (EggCellRendererKeys *keys,
                                        guint                keyval,
					guint		     keycode,
					EggVirtualModifierType  mask)
{
  char *text;
  gboolean changed;

  g_return_if_fail (EGG_IS_CELL_RENDERER_KEYS (keys));

  g_object_freeze_notify (G_OBJECT (keys));

  changed = FALSE;
  
  if (keyval != keys->accel_key)
    {
      keys->accel_key = keyval;
      g_object_notify (G_OBJECT (keys), "accel_key");
      changed = TRUE;
    }

  if (mask != keys->accel_mask)
    {
      keys->accel_mask = mask;

      g_object_notify (G_OBJECT (keys), "accel_mask");
      changed = TRUE;
    }  

  if (keycode != keys->keycode)
    {
      keys->keycode = keycode;

      g_object_notify (G_OBJECT (keys), "keycode");
      changed = TRUE;
    }
  g_object_thaw_notify (G_OBJECT (keys));

  if (changed)
    {
      /* sync string to the key values */
      text = convert_keysym_state_to_string (keys->accel_key, keys->keycode, keys->accel_mask);
      g_object_set (keys, "text", text, NULL);
      g_free (text);
    }
}

void
egg_cell_renderer_keys_get_accelerator (EggCellRendererKeys     *keys,
                                        guint                   *keyval,
                                        EggVirtualModifierType  *mask)
{
  g_return_if_fail (EGG_IS_CELL_RENDERER_KEYS (keys));

  if (keyval)
    *keyval = keys->accel_key;

  if (mask)
    *mask = keys->accel_mask;
}

void
egg_cell_renderer_keys_set_accel_mode (EggCellRendererKeys     *keys,
				       EggCellRendererKeysMode  accel_mode)
{
  g_return_if_fail (EGG_IS_CELL_RENDERER_KEYS (keys));
  keys->accel_mode = accel_mode;
  g_object_notify (G_OBJECT (keys), "accel_mode");
}
