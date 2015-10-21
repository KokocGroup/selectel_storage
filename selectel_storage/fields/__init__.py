#! coging: utf-8
from __future__ import unicode_literals

import gzip
from StringIO import StringIO

import magic
from requests.exceptions import HTTPError
from selectel_storage import (SelectelStorageException, selectel_connection,
                              settings)


class SelectelCloudObject(object):

    def __init__(self, path=None):
        self.path = path
        self._content = None

    @property
    def content(self):
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

    @property
    def mimetype(self):
        return magic.from_buffer(self.content, mime=True)

    def read(self):
        return self.content

    def seek(self, *args, **kwargs):
        pass

    def tell(self):
        return len(self.content)

    def delete(self):
        selectel_connection.remove(settings.CONTAINER, self.path)
        self.path = None
