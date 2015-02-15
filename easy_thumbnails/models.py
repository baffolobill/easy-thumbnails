from __future__ import unicode_literals

#from django.db import models
from django.utils import timezone

from mongoengine import *

from easy_thumbnails import utils, signal_handlers
from easy_thumbnails.conf import settings


class FileManager(models.Manager):

    def get_file(self, storage, name, create=False, update_modified=None,
                 check_cache_miss=False, **kwargs):
        kwargs.update(dict(storage_hash=utils.get_storage_hash(storage),
                           name=name))
        if create:
            if update_modified:
                defaults = kwargs.setdefault('defaults', {})
                defaults['modified'] = update_modified
            obj, created = self.get_or_create(**kwargs)
        else:
            created = False
            kwargs.pop('defaults', None)
            try:
                manager = self._get_thumbnail_manager()
                obj = manager.get(**kwargs)
            except self.model.DoesNotExist:

                if check_cache_miss and storage.exists(name):
                    # File already in storage, update cache
                    obj = self.create(**kwargs)
                    created = True
                else:
                    return

        if update_modified and not created:
            if obj.modified != update_modified:
                self.filter(pk=obj.pk).update(modified=update_modified)

        return obj

    def _get_thumbnail_manager(self):
        return self


class Source(Document):
    storage_hash = StringField(max_length=40, db_index=True)
    name = StringField(max_length=255, unique_with='storage_hash', db_index=True)
    modified = DateTimeField(default=timezone.now)

    objects = FileManager()

    def __unicode__(self):
        return self.name

    def get_thumbnails(self):
        return Thumbnail.objects(source=self)


class Thumbnail(Document):
    source = ReferenceField(Source, reverse_delete_rule=CASCADE)
    storage_hash = StringField(max_length=40, db_index=True)
    name = StringField(max_length=255, unique_with=['source', 'storage_hash'], db_index=True)
    modified = DateTimeField(default=timezone.now)
    width = IntField(null=True)
    height = IntField(null=True)

    objects = FileManager()

    def __unicode__(self):
        return "%sx%s" % (self.width, self.height)

    @property
    def size(self):
        return self.width, self.height


pre_save.connect(signal_handlers.find_uncommitted_filefields)
post_save.connect(signal_handlers.signal_committed_filefields)
