#!coding: utf-8
from __future__ import unicode_literals
from selectel.storage import Storage


class SelectelStorageException(Exception):
    pass


class SettingsSinglenton(object):
    USER = None
    PASSWORD = None
    CONTAINER = None
    DEBUG = False


settings = SettingsSinglenton()


class SelectelConnection(object):
    _CON = None

    def __getattr__(self, attr):
        if not self._CON:
            if not all((settings.USER, settings.PASSWORD, settings.CONTAINER)):
                raise SelectelStorageException('You must specify in the settings: SELECTEL_USER, SELECTEL_PASSWORD, SELECTEL_CONTAINER')
            self._CON = Storage(settings.USER, settings.PASSWORD)
        return getattr(self._CON, attr)

selectel_connection = SelectelConnection()


def init_flask_app(flask_app):
    settings.USER = flask_app.config.get('SELECTEL_USER')
    settings.PASSWORD = flask_app.config.get('SELECTEL_PASSWORD')
    settings.CONTAINER = flask_app.config.get('SELECTEL_CONTAINER')
    settings.DEBUG = flask_app.config.get('DEBUG')

