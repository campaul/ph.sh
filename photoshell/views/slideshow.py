from threading import Lock

from gi.repository import Gtk
from photoshell.widgets.photodisplay import PhotoDisplay


class Slideshow(Gtk.Box):

    def __init__(self):
        super(Slideshow, self).__init__()
        self.canvas = PhotoDisplay()
        self.image_path = None
        self.pack_start(self.canvas, True, True, 0)
        self.mutex = Lock()

    def render_selection(self, selection):
        self.mutex.acquire()

        new_photo = selection.current_photo()

        if new_photo:
            self.canvas.set_photo(new_photo)

        self.mutex.release()
