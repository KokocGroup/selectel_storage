#! coding: utf-8
from __future__ import absolute_import, unicode_literals

import types
from hashlib import md5
from StringIO import StringIO
import gzip
import os

from mongoengine.fields import BaseField
from selectel_storage import (SelectelStorageException, selectel_connection,
                              settings)
from selectel_storage.fields import SelectelCloudObject


class SelectelStorageField(BaseField):

    def get_path(self, content):
        filename = md5(content).hexdigest()
        return "/" + os.path.join(filename[:2], filename[2:4], filename)

    def to_python(self, value):
        if isinstance(value, types.StringTypes):
            value = SelectelCloudObject(value)
        return value

    def to_mongo(self, value):

            try:
                if isinstance(value, (SelectelCloudObject, StringIO, file)):
                    if value:
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
                        selectel_connection.put(settings.CONTAINER, path, compers_obj.getvalue())
                        return path
                else:
                    raise SelectelStorageException("type '{}' is not SelectelCloudObject, StringIO or file".format(type(value)))
            except Exception, e:
                self.error(unicode(e))

    def prepare_query_value(self, op, value):
        if value:
            return value.path

    def validate(self, value):
        if not isinstance(value, (SelectelCloudObject, StringIO, file)):
            self.error("type '{}' is not SelectelCloudObject, StringIO or file".format(type(value)))
