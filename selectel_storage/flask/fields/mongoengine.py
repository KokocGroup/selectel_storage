#! coding: utf-8
from selectel_storage.base.mongoengine import BaseMongoEngineField
from selectel_storage.flask.fields import FlaskFieldMixin


class SelectelStorageField(FlaskFieldMixin, BaseMongoEngineField):
    pass
