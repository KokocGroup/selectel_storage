# coding=utf-8
import hashlib
from datetime import datetime, timedelta
import requests


class Storage(object):
    SUPPORTED_ARCHIVES = ("tar", "tar.gz", "tar.bz2")

    def update_expired(fn):
        def wrapper(*args, **kwargs):
            auth = args[0].auth
            if auth.expired():
                args[0].authenticate()
            return fn(*args, **kwargs)
        return wrapper

    class Auth(object):
        THRESHOLD = 3600

        def __init__(self, token, storage, expires):
            self.token = token
            self.storage = storage[:-1]
            self.expires = datetime.now() + timedelta(seconds=int(expires))

        def expired(self):
            left = self.expires - datetime.now()
            return (left.total_seconds() < self.THRESHOLD)

    def __init__(self, user, key, timeout=3):
        self.url = "https://auth.selcdn.ru/"
        self.user = user
        self.timeout = timeout
        self.key = key
        self.authenticate()

    def authenticate(self):
        headers = {"X-Auth-User": self.user, "X-Auth-Key": self.key}
        r = requests.get(self.url, headers=headers, verify=True, timeout=self.timeout)
        if r.status_code != 204:
            raise Exception("Selectel: Unexpected status code: %s" %
                            r.status_code)
        auth = self.Auth(r.headers["X-Auth-Token"],
                         r.headers["X-Storage-Url"],
                         r.headers["X-Expire-Auth-Token"])
        self.auth = auth
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": self.auth.token})

    @update_expired
    def list(self, container, path=None):
        url = "%s/%s" % (self.auth.storage, container)
        params = {"format": "json"}
        if path is not None:
            if path.startswith("/"):
                path = path[1:]
            params["path"] = path
        r = self.session.get(url, params=params, verify=True, timeout=self.timeout)
        r.raise_for_status()

        def mapper(obj):
            dt = datetime.strptime(obj["last_modified"] + " GMT",
                                   "%Y-%m-%dT%H:%M:%S.%f %Z")
            result = {
                "content-type": obj["content_type"],
                "content-length": obj["bytes"],
                "hash": obj["hash"],
                "last-modified": dt
            }
            return result

        return {"/" + x["name"]: mapper(x) for x in r.json()}

    @update_expired
    def get(self, container, path, headers=None):
        url = "%s/%s%s" % (self.auth.storage, container, path)
        if headers is None:
            headers = {}
        r = self.session.get(url, headers=headers, verify=True, timeout=self.timeout)
        r.raise_for_status()
        return r.content

    @update_expired
    def get_stream(self, container, path, headers=None, chunk=2**20):
        url = "%s/%s%s" % (self.auth.storage, container, path)
        if headers is None:
            headers = {}
        r = self.session.get(url, headers=headers, stream=True, verify=True, timeout=self.timeout)
        r.raise_for_status()
        return r.iter_content(chunk_size=chunk)

    @update_expired
    def put(self, container, path, content, headers=None, extract=None):
        url = "%s/%s%s" % (self.auth.storage, container, path)
        if headers is None:
            headers = {}
        if extract in self.SUPPORTED_ARCHIVES:
            url += "?extract-archive=%s" % extract
            headers["Accept"] = "application/json"
        if not extract:
            headers["ETag"] = hashlib.md5(content).hexdigest()
        r = self.session.put(url, data=content, headers=headers, verify=True, timeout=self.timeout)
        r.raise_for_status()
        if extract in self.SUPPORTED_ARCHIVES:
            answer = r.json()
            return (answer["Number Files Created"], answer["Errors"])

    @update_expired
    def put_stream(self, container, path, descriptor,
                   headers=None, chunk=2**20, extract=None):
        url = "%s/%s%s" % (self.auth.storage, container, path)
        if headers is None:
            headers = {}
        if extract in self.SUPPORTED_ARCHIVES:
            url += "?extract-archive=%s" % extract
            headers["Accept"] = "application/json"

        def gen():
            data = descriptor.read(chunk)
            while data:
                yield data
                data = descriptor.read(chunk)

        r = self.session.put(url, data=gen(), headers=headers, verify=True, timeout=self.timeout)
        r.raise_for_status()
        if extract in self.SUPPORTED_ARCHIVES:
            answer = r.json()
            return (answer["Number Files Created"], answer["Errors"])

    @update_expired
    def put_file(self, container, path, filename, headers=None, extract=None):
        url = "%s/%s%s" % (self.auth.storage, container, path)
        if headers is None:
            headers = {}
        if extract in self.SUPPORTED_ARCHIVES:
            url += "?extract-archive=%s" % extract
            headers["Accept"] = "application/json"
        with open(filename, 'r+b') as file:
            r = self.session.put(url, data=file, headers=headers, verify=True, timeout=self.timeout)
            r.raise_for_status()
        if extract in self.SUPPORTED_ARCHIVES:
            answer = r.json()
            return (answer["Number Files Created"], answer["Errors"])

    @update_expired
    def remove(self, container, path, force=False):
        url = "%s/%s%s" % (self.auth.storage, container, path)
        r = self.session.delete(url, verify=True, timeout=self.timeout)
        if force:
            if r.status_code == 404:
                return r.headers
            else:
                r.raise_for_status()
        else:
            r.raise_for_status()

    @update_expired
    def copy(self, container, src, dst, headers=None):
        dst = "%s/%s%s" % (self.auth.storage, container, dst)
        src = "%s%s" % (container, src)
        if headers is None:
            headers = {}
        headers["X-Copy-From"] = src
        r = self.session.put(dst, headers=headers, verify=True, timeout=self.timeout)
        r.raise_for_status()

    @update_expired
    def info(self, container, path=None):
        if path is None:
            url = "%s/%s" % (self.auth.storage, container)
        else:
            url = "%s/%s%s" % (self.auth.storage, container, path)
        r = self.session.head(url, verify=True, timeout=self.timeout)
        r.raise_for_status()
        if path is None:
            result = {
                "count": int(r.headers["X-Container-Object-Count"]),
                "usage": int(r.headers["X-Container-Bytes-Used"]),
                "public": (r.headers.get("X-Container-Meta-Type") == "public"),
                "tx": int(r.headers["X-Transfered-Bytes"]),
                "rx": int(r.headers["X-Received-Bytes"])
            }
        else:
            dt = datetime.strptime(r.headers["Last-Modified"],
                                   "%a, %d %b %Y %H:%M:%S %Z")
            result = {
                "content-length": int(r.headers["Content-Length"]),
                "last-modified": dt,
                "hash": r.headers["ETag"],
                "content-type": r.headers["Content-Type"],
                "downloads": int(r.headers["X-Object-Downloads"])
            }
        return result

    @update_expired
    def create(self, container, public=False, headers=None):
        url = "%s/%s" % (self.auth.storage, container)
        if headers is None:
            headers = {}
        if public:
            headers["X-Container-Meta-Type"] = "public"
        else:
            headers["X-Container-Meta-Type"] = "private"
        r = self.session.put(url, headers=headers, verify=True, timeout=self.timeout)
        r.raise_for_status()

    @update_expired
    def drop(self, container, force=False, recursive=False):
        url = "%s/%s" % (self.auth.storage, container)
        if recursive:
            for filename in self.list(container):
                self.remove(container, filename, force=force)
        r = self.session.delete(url, verify=True, timeout=self.timeout)
        if force:
            if r.status_code == 404:
                pass
            else:
                r.raise_for_status()
        else:
            r.raise_for_status()


class Container(object):
    METHODS = ["list", "get", "get_stream", "put",
               "put_stream", "put_file", "remove",
               "copy", "info"]

    def __init__(self, auth, key, name):
        self.name = name
        self.storage = Storage(auth, key)

        def make_method(name):
            def method(*args, **kwargs):
                fn = getattr(self.storage, name)
                return fn(self.name, *args, **kwargs)
            return method

        for name in self.METHODS:
            setattr(self, name, make_method(name))
