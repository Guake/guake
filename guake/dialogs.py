import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class RenameDialog(Gtk.Dialog):
    def __init__(self, window, current_name):
        super().__init__(
            _("Rename tab"),
            window,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.REJECT,
                Gtk.STOCK_OK,
                Gtk.ResponseType.ACCEPT,
            ),
        )
        self.entry = Gtk.Entry()
        self.entry.set_text(current_name)
        self.entry.set_property("can-default", True)
        self.entry.show()

        vbox = Gtk.VBox()
        vbox.set_border_width(6)
        vbox.show()

        self.set_size_request(300, -1)
        self.vbox.pack_start(vbox, True, True, 0)
        self.set_border_width(4)
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        self.add_action_widget(self.entry, Gtk.ResponseType.ACCEPT)
        self.entry.reparent(vbox)

    def get_text(self):
        return self.entry.get_text()


class PromptQuitDialog(Gtk.MessageDialog):

    """Prompts the user whether to quit/close a tab."""

    def __init__(self, parent, procs, tabs, notebooks):
        super().__init__(
            parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.YES_NO,
        )

        if tabs == -1:
            primary_msg = _("Do you want to close the tab?")
            tab_str = ""
            notebooks_str = ""
        else:
            primary_msg = _("Do you really want to quit Guake?")
            if tabs == 1:
                tab_str = _(" and one tab open")
            else:
                tab_str = _(" and {0} tabs open").format(tabs)
            if notebooks > 1:
                notebooks_str = _(" on {0} workspaces").format(notebooks)
            else:
                notebooks_str = ""

        if not procs:
            proc_str = _("There are no processes running")
        elif len(procs) == 1:
            proc_str = _("There is a process still running")
        else:
            proc_str = _("There are {0} processes still running").format(len(procs))

        if procs:
            proc_list = "\n\n" + "\n".join(f"{name} ({pid})" for pid, name in procs)
        else:
            proc_list = ""

        self.set_markup(primary_msg)
        self.format_secondary_markup(f"<b>{proc_str}{tab_str}{notebooks_str}.</b>{proc_list}")

    def quit(self):
        """Run the "are you sure" dialog for quitting Guake"""
        # Stop an open "close tab" dialog from obstructing a quit
        response = self.run() == Gtk.ResponseType.YES
        self.destroy()
        # Keep Guake focussed after dismissing tab-close prompt
        # if tab == -1:
        #     self.window.present()
        return response

    def close_tab(self):
        response = self.run() == Gtk.ResponseType.YES
        self.destroy()
        # Keep Guake focussed after dismissing tab-close prompt
        # if tab == -1:
        #     self.window.present()
        return response


class PromptResetColorsDialog(Gtk.MessageDialog):

    """Prompts the user whether to reset tab colors."""

    def __init__(self, parent):
        super().__init__(
            parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.YES_NO,
        )

        primary_msg = _("Do you want to reset custom colors for this tab?")

        self.set_markup(primary_msg)

    def reset_tab_custom_colors(self):
        """Run the "are you sure" dialog for resetting tab colors"""
        # Stop an open "close tab" dialog from obstructing a quit
        response = self.run() == Gtk.ResponseType.YES
        self.destroy()
        # Keep Guake focussed after dismissing tab-close prompt
        # if tab == -1:
        #     self.window.present()
        return response


class SaveTerminalDialog(Gtk.FileChooserDialog):
    def __init__(self, terminal, window):
        super().__init__(
            _("Save to..."),
            window,
            Gtk.FileChooserAction.SAVE,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            ),
        )
        self.set_default_response(Gtk.ResponseType.OK)
        self.terminal = terminal
        self.parent_window = window

    def run(self):
        self.terminal.select_all()
        self.terminal.copy_clipboard()
        self.terminal.unselect_all()
        clipboard = Gtk.Clipboard.get_default(self.parent_window.get_display())
        selection = clipboard.wait_for_text()
        if not selection:
            return
        selection = selection.rstrip()
        filter = Gtk.FileFilter()
        filter.set_name(_("All files"))
        filter.add_pattern("*")
        self.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name(_("Text and Logs"))
        filter.add_pattern("*.log")
        filter.add_pattern("*.txt")
        self.add_filter(filter)

        response = super().run()
        if response == Gtk.ResponseType.OK:
            filename = self.get_filename()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(selection)
        self.destroy()
