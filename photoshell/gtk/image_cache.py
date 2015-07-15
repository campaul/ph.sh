from datetime import datetime


class GtkImageCache(object):

    def __init__(self):
        super(GtkImageCache, self).__init__()
        self.cache = {}

    def gtk_image(self, base_path, photo, max_width=1280, max_height=1024):
        from photoshell.image import Image
        photo_key = '{path}|{width}|{height}'.format(
            path=photo.developed_path,
            width=max_width,
            height=max_height,
        )

        if not self.cache.get(photo_key, None):
            self.cache[photo_key] = Image(
                photo.developed_path,
                datetime.fromtimestamp(photo.metadata.timestamp),
            ).load_preview(
                base_path,
                max_width=max_width,
                max_height=max_height,
            )

        return self.cache[photo_key]
