
#ifndef __KEY_BINDER_H__
#define __KEY_BINDER_H__

#include <glib.h>

G_BEGIN_DECLS

typedef void (* BindkeyHandler) (char *keystring, gpointer user_data);

void keybinder_init   (void);

gboolean keybinder_bind   (const char           *keystring,
			      BindkeyHandler  handler,
			      gpointer              user_data);

void keybinder_unbind (const char           *keystring,
			      BindkeyHandler  handler);

gboolean keybinder_is_modifier (guint keycode);

guint32 keybinder_get_current_event_time (void);

G_END_DECLS

#endif /* __KEY_BINDER_H__ */

