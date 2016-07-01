#! coging: utf-8
from __future__ import unicode_literals

import gzip
from StringIO import StringIO

import magic
import time
from requests.exceptions import HTTPError, ReadTimeout
from selectel_storage.base.storage import Storage
from functools import wraps


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck:
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SelectelApi(object):
    __metaclass__ = Singleton

    def __init__(self, user=None, password=None, container=None):
        self.user = user
        self.password = password
        self.container = container
        self.connection = Storage(self.user, self.password)

    def add(self, path, file_obj):
        self._make_call('put', self.container, path, file_obj)

    def get(self, path):
        return self._make_call('get_stream', self.container, path)

    def delete(self, path):
        self._make_call('remove', self.container, path)

    @retry((ReadTimeout, HTTPError), delay=1.5)
    def _make_call(self, method, *args):
        try:
            return getattr(self.connection, method)(*args)
        except HTTPError as e:
            if e.response.status_code == 401:
                self.connection.authenticate()
            raise

    @retry((ReadTimeout, HTTPError), delay=1.5)
    def info(self):
        url = "%s/%s" % (self.connection.auth.storage, self.container)
        try:
            r = self.connection.session.head(url, verify=True)
            r.raise_for_status()
        except HTTPError as e:
            if e.response.status_code == 401:
                self.connection.authenticate()
            raise
        result = {
            'used': int(r.headers['X-Container-Bytes-Used']),
            'quota': int(r.headers['X-Container-Meta-Quota-Bytes']),
            'count': int(r.headers['X-Container-Object-Count'])
        }
        return result


class SelectelCloudObject(object):

    def __init__(self, path):
        self.path = path
        self.api_con = SelectelApi()
        self._content = None

    @property
    def content(self):
        if not self._content:
            iostring = StringIO()
            for chunk in self.api_con.get(self.path):
                iostring.write(chunk)
            iostring.seek(0)
            self._content = gzip.GzipFile(fileobj=iostring, mode='rb').read()
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
