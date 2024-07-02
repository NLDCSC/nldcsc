from flask_sqlalchemy import SQLAlchemy

from .model_base import ModelBase


class FlaskSQLAlchemy(SQLAlchemy):
    def __init__(self, *args, **kwargs):
        base_class = kwargs.pop("model_class", None)

        if base_class is None:
            base_class = ModelBase

        kwargs["model_class"] = base_class

        super().__init__(*args, **kwargs)
