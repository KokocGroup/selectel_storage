#! coging: utf-8
from __future__ import unicode_literals
from selectel_storage import settings, selectel_connection, SelectelStorageException
from requests.exceptions import HTTPError
import gzip
from StringIO import StringIO


class SelectelCloudObject(object):

    def __init__(self, path=None):
        self.path = path
        self._content = None

    def read(self):
        if not self._content:
            try:
                compressed_content = selectel_connection.get(settings.CONTAINER, self.path)
                self._content = gzip.GzipFile(fileobj=StringIO(compressed_content), mode='rb').read()
            except HTTPError, e:
                error = None
                if e.response.status_code == 404:
                    error = 'File "{}" not found in cloud storage'.format(self.path)
                if error:
                    raise SelectelStorageException(error)
        return self._content

    def seek(*args, **kwargs):
        pass

    def delete(self):
        selectel_connection.remove(settings.CONTAINER, self.path)
        self.path = None
