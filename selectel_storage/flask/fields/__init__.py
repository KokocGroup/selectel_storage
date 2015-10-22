#! coding: utf-8
from selectel_storage.base import BaseFieldMixin
from flask import current_app


class FlaskFieldMixin(BaseFieldMixin):

    @property
    def api_conn(self):
        return current_app.extensions['selectel_storage'].connection
