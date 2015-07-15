import os

from datetime import datetime
import sqlite3 as sqlite

from photoshell.photo import Photo
from photoshell.selection import Selection
from photoshell.hash import hash_file
from photoshell.progress import Progress
from rawkit import util


class Library(object):

    def __init__(self, config):
        super(Library, self).__init__()

        self.library_path = config['library']
        self.import_string = os.path.join(self.library_path,
                                          config['import_path'])
        self.cache_path = os.path.join(self.library_path, '.cache')
        if not os.path.exists(self.library_path):
            os.makedirs(self.library_path)
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
            os.makedirs(os.path.join(self.cache_path, 'ppm'))
            os.makedirs(os.path.join(self.cache_path, 'raw'))

        self.db_path = os.path.join(self.library_path, '.library.db')
        if not os.path.exists(self.db_path):
            connection = sqlite.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(
                'CREATE TABLE Photos(Hash TEXT, Raw TEXT, Developed TXT)'
            )
        else:
            connection = sqlite.connect(self.db_path)
            cursor = connection.cursor()

        self.sidecars = []

        photo_rows = cursor.execute('SELECT * FROM Photos').fetchall()
        for file_hash, raw_path, developed_path in photo_rows:
            self.sidecars.append(Photo.create(
                raw_path=raw_path,
                developed_path=developed_path,
                file_hash=file_hash,
            ))

        connection.close()

    def all(self):
        return self.query(lambda image: True)

    def query(self, match):
        selection = Selection(self.library_path, match)

        for sidecar in self.sidecars:
            if match(sidecar):
                selection.append(sidecar)

        # TODO: in place mutation is terrible
        selection.sort(key=lambda photo: photo.raw_path)
        return selection

    def update(self, selection):
        current = selection.current_photo()
        if current:
            image_path = current.image_path
        new_selection = self.query(selection.query)
        if current:
            new_selection.jump(image_path)
        return new_selection

    def exists(self, photo):
        for sidecar in self.sidecars:
            if photo == sidecar:
                return True
        return False

    def add(self, photo):
        self.sidecars.append(photo)

    def remove(self, photo):
        self.sidecars.remove(photo)

    def import_path(self, photo):
        file_name, file_ext = os.path.splitext(
            os.path.basename(photo.raw_path))

        import_path = datetime.fromtimestamp(photo.metadata.timestamp).strftime(
            self.import_string.format(
                original_filename=file_name,
                file_hash=photo.file_hash,
            )
        ) + file_ext

        # TODO: directory creation should live elsewhere
        import_dir = os.path.dirname(import_path)
        if not os.path.exists(import_dir):
            os.makedirs(import_dir)

        return import_path

    def remove_photo(self, photo):
        connection = sqlite.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute(
            'DELETE FROM Photos WHERE Hash="{h}"'.format(
                h=photo.file_hash
            )
        )

        self.remove(photo)

        connection.commit()
        connection.close()

    def import_photos(self, path, notify_callback=None, imported_callback=None,
                      copy_photos=True, delete_originals=False):

        progress, photo_iterator = self.discover(path)

        connection = sqlite.connect(self.db_path)
        cursor = connection.cursor()

        for photo in photo_iterator():
            if notify_callback:
                notify_callback(os.path.basename(photo.raw_path))

            # Maybe copy the photo
            if copy_photos:
                photo = photo.copy(
                    self.import_path(photo), delete_originals=delete_originals)

            # Develop the photo
            photo = photo.develop(
                write_sidecar=False,
                cache_path=self.cache_path,
            )

            cursor.execute(
                'INSERT INTO Photos VALUES("{h}", "{r}", "{d}")'.format(
                    h=photo.file_hash,
                    r=photo.raw_path,
                    d=photo.developed_path,
                )
            )

            # Add photo to library
            self.add(photo)

            if imported_callback:
                imported_callback(photo.file_hash, progress.percent())

        connection.commit()
        connection.close()

    def discover(self, path):
        photo_list = [file_name.decode('ascii')
                      for file_name in util.discover(path)]
        progress = Progress(len(photo_list))

        def photo_iterator():
            for photo_path in photo_list:
                progress.advance()
                photo = Photo.create(
                    raw_path=photo_path,
                    developed_path=None,
                    file_hash=hash_file(photo_path),
                )

                if not self.exists(photo):
                    yield photo

        return progress, photo_iterator
