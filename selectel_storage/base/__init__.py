#! coging: utf-8
from __future__ import unicode_literals

import gzip
from StringIO import StringIO

import magic
from requests.exceptions import HTTPError
from selectel.storage import Storage
from selectel_storage.exceptions import SelectelStorageExeption


class SelectelApi(object):
    def __init__(self, user, password, container):
        self.container = container
        self.connection = Storage(user, password)

    def add(self, path, content):
        self._make_call('put', self.container, path, content)

    def get(self, path):
        self._make_call('get', self.container, path)

    def delete(self, path):
        self._make_call('remove', self.container, path)

    def _make_call(self, method, *args):
        try:
            getattr(self.connection, method)(*args)
        except HTTPError, e:
            error = str(e)
            if e.response.status_code == 404:
                error = 'File "{}" not found in container "{}"'.format(self.path, self.container)
            elif e.response.status_code == 403:
                error = "No permissions of action '{}' for the container '{}'".format(method, self.container)
            raise SelectelStorageExeption(error)


class BaseFieldMixin(object):

    @property
    def api_conn(self):
        raise NotImplemented()


class SelectelCloudObject(object):

    def __init__(self, path, api_connection):
        self.path = path
        self.__api_con = api_connection
        self.__content = None

    @property
    def content(self):
        if not self._content:
            compressed_content = self.__api_con.get(self.path)
            self._content = gzip.GzipFile(fileobj=StringIO(compressed_content), mode='rb').read()
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

    def close(self):
        pass

    def delete(self):
        self.__api_con.delete(self.path)
        self.path = None
