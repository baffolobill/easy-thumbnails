from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from mongoengine import *

from easy_thumbnails import utils, signal_handlers
from easy_thumbnails.conf import settings

class FileQuerySet(QuerySet):

    def get_file(self, storage, name, create=False, update_modified=None,
                 check_cache_miss=False, **kwargs):
        kwargs.update(dict(storage_hash=utils.get_storage_hash(storage),
                           name=name))
        if create:
            created = True
            defaults = kwargs.pop('defaults', {})
            if update_modified:
                defaults['modified'] = update_modified

            modify_kwargs = dict([('set__{}'.format(k), v) for k,v in kwargs.items()])
            modify_kwargs.update(
                dict([('set_on_insert__{}'.format(k), v) for k,v in defaults.items()])
            )

            obj = self.filter(**kwargs).modify(upsert=True, new=True, **modify_kwargs)
        else:
            created = False
            kwargs.pop('defaults', None)
            try:
                obj = self.get(**kwargs)
            except DoesNotExist:

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


class Source(Document):
    storage_hash = StringField(max_length=40)
    name = StringField(max_length=255, unique_with='storage_hash')
    modified = DateTimeField(default=timezone.now)

    meta = {'queryset_class': FileQuerySet}

    def __unicode__(self):
        return self.name

    def get_thumbnails(self):
        return Thumbnail.objects(source=self)


class Thumbnail(Document):
    source = ReferenceField(Source, reverse_delete_rule=CASCADE)
    storage_hash = StringField(max_length=40)
    name = StringField(max_length=255, unique_with=['source', 'storage_hash'])
    modified = DateTimeField(default=timezone.now)
    width = IntField(default=0, required=False)
    height = IntField(default=0, required=False)

    meta = {'queryset_class': FileQuerySet}

    def __unicode__(self):
        return "%sx%s" % (self.width, self.height)

    @property
    def size(self):
        return self.width, self.height


pre_save.connect(signal_handlers.find_uncommitted_filefields)
post_save.connect(signal_handlers.signal_committed_filefields)
