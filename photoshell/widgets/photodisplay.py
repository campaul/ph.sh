from gi.repository import Gdk
from gi.repository import Gtk

# from photoshell.photo import Photo


class PhotoDisplay(Gtk.DrawingArea):

    def __init__(self, photo=None):
        super(PhotoDisplay, self).__init__()

        self.photo = photo

        self.set_size_request(30, 100)

        self.x_offset = 0
        self.y_offset = 0

        self.drag = Gtk.GestureDrag.new(self)
        self.drag.connect('drag-end', self.on_drag_end)
        self.drag.connect('drag-update', self.on_drag)

        # Setup the draw event
        self.connect('draw', self.draw)

        self.show()

    def set_photo(self, photo):
        self.photo = photo
        # Gdk.Window.invalidate_rect(self.get_allocation(), False)
        self.queue_draw()

    def draw(self, widget, cr):
        if self.photo is not None:
            pb = self.photo.gtk_pixbuf(
                self.photo.developed_path,
                max_width=self.get_allocated_width(),
                max_height=self.get_allocated_height()
            )
            Gdk.cairo_set_source_pixbuf(cr, pb, self.x_offset, self.y_offset)
            cr.paint()

    def on_drag_end(self, event, x_offset, y_offset):
        self.x_offset = 0
        self.queue_draw()

    def on_drag(self, event, x_offset, y_offset):
        self.x_offset = x_offset
        self.queue_draw()
