from collections import namedtuple
import os
import shutil

import yaml

from rawkit.raw import Raw


_Photo = namedtuple('Photo', [
    'raw_path',
    'developed_path',
    'file_hash',
])


class Photo(_Photo):

    @classmethod
    def create(cls, raw_path, developed_path, file_hash):
        return cls(
            raw_path=raw_path,
            developed_path=developed_path,
            file_hash=file_hash,
        )

    @property
    def metadata(self):
        with Raw(filename=self.raw_path) as raw:
            metadata = raw.metadata

        return metadata

    def copy(self, new_path, delete_originals=False):
        # copy photo
        existing_photo_path = self.raw_path
        shutil.copyfile(existing_photo_path, new_path)
        # TODO: Make sure the file copied w/o errors first?
        if delete_originals:
            os.unlink(existing_photo_path)

        # copy metadata
        existing_meta_path = self.raw_path + '.yaml'
        if os.path.exists(existing_meta_path):
            shutil.copyfile(existing_meta_path, new_path + '.yaml')
            # TODO: Make sure the file copied w/o errors first?
            if delete_originals:
                os.unlink(existing_meta_path)

        return Photo.create(
            raw_path=new_path,
            developed_path=self.developed_path,
            file_hash=self.file_hash
        )

    def develop(self, write_sidecar=False, cache_path=None):
        # develop photo
        developed_name = '{file_hash}.{extension}'.format(
            file_hash=self.file_hash,
            extension='ppm',
        )

        developed_path = os.path.join(
            cache_path,
            'ppm',
            developed_name,
        )

        if not os.path.isfile(developed_path):
            with Raw(filename=self.raw_path) as raw:
                raw.options.half_size = True
                raw.save(filename=developed_path)

        photo = Photo.create(
            raw_path=self.raw_path,
            developed_path=developed_path,
            file_hash=self.file_hash
        )

        if write_sidecar:
            meta_path = photo.raw_path + '.yaml'
            # IMPORTANT: until the following TODO about merging metadata is
            # done, trying to call photo.metadata *after* opening the yaml
            # file will cause it to read the empty file and write nothing.
            # To fix this we just cache metadata here before calling open.
            metadata = photo.metadata
            # TODO: merge existing metadata
            # This is an odd edge case where you're importing from "source" to
            # "destination" and "destination" already has a sidecar for some
            # reason. Sidecars from "source" will be loaded in already.
            with open(meta_path, 'w+') as meta_file:
                yaml.dump(
                    metadata, meta_file, default_flow_style=False)

        return photo

    def __eq__(self, other):
        return self.file_hash == other.file_hash
