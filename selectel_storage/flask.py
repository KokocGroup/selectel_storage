#! coding: utf-8
from selectel_storage.base import SelectelApi, mongoengine
from selectel_storage.exceptions import SelectelStorageExeption


class SelectelStorage(object):

    def __init__(self, app=None):
        self.mongoengine = mongoengine
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('SELECTEL_STORAGE', {})

        if not app.config.get('SELECTEL_STORAGE'):
            raise SelectelStorageExeption('Bad config: No SELECTEL_STORAGE options')

        self.connection = SelectelApi(
            user=app.config['SELECTEL_STORAGE']['USER'],
            password=app.config['SELECTEL_STORAGE']['PASSWORD'],
            container=app.config['SELECTEL_STORAGE']['CONTAINER']
        )

        app.extensions = getattr(app, 'extensions', {})
        app.extensions['selectel_storage'] = self
