#! coging: utf-8
from __future__ import unicode_literals

import gzip
from StringIO import StringIO

import magic
from requests.exceptions import HTTPError
from selectel.storage import Storage

from selectel_storage.exceptions import SelectelStorageExeption


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SelectelApi(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.config = SelectelConfig()
        self.connection = Storage(self.config.user, self.config.password)

    def add(self, path, content):
        self._make_call('put', self.config.container, path, content)

    def get(self, path):
        self._make_call('get', self.config.container, path)

    def delete(self, path):
        self._make_call('remove', self.config.container, path)

    def _make_call(self, method, *args):
        try:
            getattr(self.connection, method)(*args)
        except HTTPError, e:
            error = str(e)
            if e.response.status_code == 404:
                error = 'File not found in container "{}"'.format(self.config.container)
            elif e.response.status_code == 403:
                error = "No permissions of action '{}' for the container '{}'".format(method, self.config.container)
            raise SelectelStorageExeption(error)


class SelectelConfig(dict):
    __metaclass__ = Singleton

    def __init__(self):
        self.user = None
        self.password = None
        self.container = None

    def set_config(self, user, password, container):
        self.user = user
        self.password = password
        self.container = container


class SelectelCloudObject(object):

    def __init__(self, path):
        self.path = path
        self.api_con = SelectelApi()
        self._content = None

    @property
    def content(self):
        if not self._content:
            compressed_content = self.api_con.get(self.path)
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
        self.api_con.delete(self.path)
        self.path = None
