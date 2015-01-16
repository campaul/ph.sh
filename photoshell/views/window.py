from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

from photoshell.views.grid import Grid
from photoshell.views.photo_exporter import PhotoExporter
from photoshell.views.photo_import import PhotoImporter
from photoshell.views.slideshow import Slideshow

SWIPE_THRESHOLD = 500


class Window(Gtk.Window):

    def __init__(self, config, library, primary_view):
        super(Window, self).__init__()

        Gtk.Window.set_default_icon_list((
            GdkPixbuf.Pixbuf.new_from_file("art/logo_xlarge.png"),
            GdkPixbuf.Pixbuf.new_from_file("art/logo_large.png"),
            GdkPixbuf.Pixbuf.new_from_file("art/logo_medium.png"),
            GdkPixbuf.Pixbuf.new_from_file("art/logo_small.png"),
            GdkPixbuf.Pixbuf.new_from_file("art/logo_xsmall.png"),
            GdkPixbuf.Pixbuf.new_from_file("art/logo_gnome.png")
        ))

        self.keyReleaseBindings = {
            Gdk.KEY_Left: lambda self, button: self.prev_photo(button),
            Gdk.KEY_Right: lambda self, button: self.next_photo(button),
            Gdk.KEY_Escape: lambda self, button: self.unfullscreen(),
        }

        self.library = library
        self.primary_view = None
        self.selection = library.all()

        # Setup keyboard bindings
        self.connect("key-release-event", self.on_key_release)

        # Use Dark Theme
        settings = Gtk.Settings.get_default()
        if 'dark_theme' in config and config['dark_theme'] is True:
            settings.set_property('gtk-application-prefer-dark-theme', True)

        # Create Header
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)

        # Create navigation box
        navigation_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(
            navigation_box.get_style_context(), 'linked')

        prev_button = Gtk.Button()
        prev_button.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))
        prev_button.connect('clicked', self.prev_photo)
        prev_button.set_sensitive(False)
        navigation_box.add(prev_button)
        self.prev_button = prev_button

        next_button = Gtk.Button()
        next_button.add(Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE))
        next_button.connect('clicked', self.next_photo)
        next_button.set_sensitive(False)
        navigation_box.add(next_button)
        self.next_button = next_button

        self.header_bar.pack_start(navigation_box)

        # Create import button
        self.import_button = Gtk.Button()
        import_icon = Gio.ThemedIcon(name="insert-image-symbolic")
        import_image = Gtk.Image.new_from_gicon(
            import_icon, Gtk.IconSize.BUTTON)
        self.import_button.connect('clicked', self.import_folder)
        self.import_button.add(import_image)

        self.header_bar.pack_start(self.import_button)

        # Create import button
        self.export_button = Gtk.Button()
        export_icon = Gio.ThemedIcon(name="document-save-symbolic")
        export_image = Gtk.Image.new_from_gicon(
            export_icon, Gtk.IconSize.BUTTON)
        self.export_button.connect('clicked', self.export_photo)
        self.export_button.add(export_image)

        self.header_bar.pack_start(self.export_button)

        self.progress = Gtk.ProgressBar()
        self.progress.set_text('Importing...')
        self.progress.set_show_text(True)

        # Create settings button
        settings_button = Gtk.Button()
        settings_icon = Gio.ThemedIcon(name="emblem-system-symbolic")
        settings_image = Gtk.Image.new_from_gicon(
            settings_icon, Gtk.IconSize.BUTTON)
        settings_button.add(settings_image)
        # TODO: add this back when it works
        # self.header_bar.pack_end(settings_button)

        # Create terminal button
        terminal_button = Gtk.Button()
        terminal_icon = Gio.ThemedIcon(name="utilities-terminal-symbolic")
        terminal_image = Gtk.Image.new_from_gicon(
            terminal_icon, Gtk.IconSize.BUTTON)
        terminal_button.add(terminal_image)
        # TODO: add this back when it works
        # self.header_bar.pack_end(terminal_button)

        # Create fullscreen button
        fullscreen_button = Gtk.Button()
        fullscreen_icon = Gio.ThemedIcon(name="view-fullscreen-symbolic")
        fullscreen_image = Gtk.Image.new_from_gicon(
            fullscreen_icon, Gtk.IconSize.BUTTON)
        fullscreen_button.add(fullscreen_image)
        fullscreen_button.connect('clicked', self.go_fullscreen)
        self.header_bar.pack_end(fullscreen_button)

        # Create view box
        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(
            view_box.get_style_context(), 'linked')

        slideshow_button = Gtk.RadioButton()
        slideshow_button.set_property('draw-indicator', False)
        slideshow_button.add(Gtk.Label('Slideshow'))
        slideshow_button.connect('clicked', self.slideshow_view)

        grid_button = Gtk.RadioButton.new_from_widget(slideshow_button)
        grid_button.set_property('draw-indicator', False)
        grid_button.add(Gtk.Label('Grid'))
        grid_button.connect('clicked', self.grid_view)

        view_box.add(grid_button)
        view_box.add(slideshow_button)
        view_box.set_homogeneous(True)
        self.header_bar.set_custom_title(view_box)

        # Setup Window
        self.set_wmclass("PhotoShell", "PhotoShell")
        self.set_titlebar(self.header_bar)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('delete-event', Gtk.main_quit)
        self.set_default_size(800, 600)
        self.set_primary_view(primary_view)

        self.swipe = Gtk.GestureSwipe.new(self)
        self.swipe.connect('swipe', self.on_swipe)

        self.update_ui()

        # Start the GTK loop
        Gtk.main()

    def render_selection(self, selection):
        self.selection = selection
        self.update_ui()

    def next_photo(self, button=None):
        self.selection.next()
        self.render_selection(self.selection)

    def prev_photo(self, button=None):
        self.selection.prev()
        self.render_selection(self.selection)

    def slideshow_view(self, button):
        if type(self.primary_view) == Slideshow:
            return

        self.set_primary_view(Slideshow())

    def grid_view(self, button):
        if type(self.primary_view) == Grid:
            return

        self.set_primary_view(Grid())

    def set_primary_view(self, view):
        if self.primary_view:
            self.remove(self.primary_view)
        self.primary_view = view

        self.add(self.primary_view)
        self.primary_view.render_selection(self.selection)
        self.show_all()

    def update_ui(self):
        self.primary_view.render_selection(self.selection)

        if len(self.library.sidecars) < 2:
            self.prev_button.set_sensitive(False)
            self.next_button.set_sensitive(False)
        else:
            self.prev_button.set_sensitive(True)
            self.next_button.set_sensitive(True)

        self.show_all()

    def import_folder(self, button):
        PhotoImporter(self).import_photos()

    def export_photo(self, button):
        PhotoExporter(self).export_photo(self.selection.current())

    def on_key_release(self, widget, ev, data=None):
        self.keyReleaseBindings.get(ev.keyval, lambda s, w: None)(self, widget)

    # TODO: Percolate events down to the actual view. May require wrapping the
    # primary layout in an EventBox?
    def on_swipe(self, gesture, x_velocity, y_velocity):
        if abs(x_velocity) > SWIPE_THRESHOLD:
            self.prev_photo() if x_velocity > 0 else self.next_photo()

    def go_fullscreen(self, button):
        self.fullscreen()
