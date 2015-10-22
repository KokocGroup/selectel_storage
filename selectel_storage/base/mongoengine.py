#! coding: utf-8
from __future__ import absolute_import, unicode_literals

import gzip
import os
import types
from hashlib import md5
from StringIO import StringIO

from mongoengine.fields import BaseField
from selectel_storage.base import SelectelCloudObject, SelectelApi


class SelectelStorageField(BaseField):

    def __init__(self, *args, **kwargs):
        self.root = kwargs.pop('root', "/")
        if not self.root.startswith('/'):
            self.root = "/" + self.root
        super(SelectelStorageField, self).__init__(*args, **kwargs)

    def get_path(self, content):
        filename = md5(content).hexdigest()
        return self.root + os.path.join(filename[:2], filename[2:4], filename + ".gz")

    def to_python(self, value):
        if isinstance(value, types.StringTypes):
            value = SelectelCloudObject(value)
        return value

    def to_mongo(self, value):
            try:
                if hasattr(value, 'read'):
                    if hasattr(value, 'seek'):
                        value.seek(0)
                    content = value.read()
                    if hasattr(value, 'seek'):
                        value.seek(0)

                    path = self.get_path(content)
                    compers_obj = StringIO()
                    compers_obj_gzip = gzip.GzipFile(fileobj=compers_obj, mode='wb')
                    compers_obj_gzip.write(content)
                    compers_obj_gzip.close()
                    self.api_conn.add(path, compers_obj.getvalue())
                    return path
            except Exception, e:
                self.error(unicode(e))

    def prepare_query_value(self, op, value):
        if value:
            return value.path

    def validate(self, value):
        if not hasattr(value, 'read'):
            self.error("type '{}' it does not implement the method 'read'".format(type(value)))

    @property
    def api_conn(self):
        return SelectelApi()
