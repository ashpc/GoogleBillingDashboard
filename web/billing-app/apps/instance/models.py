__author__ = "Ashwini Chandrasekar(@sriniash)"
__email__ = "ASHWINI_CHANDRASEKAR@homedepot.com"
__version__ = "1.0"
__doc__ = "Models relating to the DB tables"

import json

from sqlalchemy.ext.declarative.api import DeclarativeMeta
from apps.config.apps_config import Base

from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String, DATETIME, FLOAT, DECIMAL


class Instance(Base):
    __tablename__ = 'Instance'
    id = Column(Integer, primary_key=True)
    instanceId = Column(String(200))
    key = Column(String(200))
    value = Column(String(200))

    def __init__(self, instanceId, key, value):
        self.instanceId = instanceId
        self.key = key
        self.value = value

    def __repr__(self):
        return '<Instance %r %r %r %r %r %r %r >' % (
            self.instanceId, self.key, self.value)


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)  # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)
