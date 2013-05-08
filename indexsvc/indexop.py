import json
import logging

from trindexsvc.gen.ttypes import IndexData


class IndexAction:
    """ Class to represent allowed index actions."""
    Create, Update, Delete = range(3)


class IndexOp(object):
    """ Object to represent data describing an index operation.

    This method represents index operations using the following json:
    {
        action: <index action>
        name: <index name>
        type: <document type>
        keys: <list of keys to perform index operation on>
              If keys is empty, the index action is to be performed on the
              entire index.
    }
    """
    def __init__(self, action, data):
        """Constructor

        Args:
            action: IndexAction enum
            data: Thrift IndexData object
        """
        self.log = logging.getLogger(__name__)
        self.action = action
        self.data = data

    def to_json(self):
        """ Return IndexOp as JSON formatted string"""
        return {
            "action": self.action,
            "name": self.data.name,
            "type": self.data.type,
            "keys": [key for key in self.data.keys]
        }

    @staticmethod
    def from_json(data):
        """ Return IndexOp object from JSON formatted string"""
        data_obj = json.loads(data)
        action = data_obj['action']
        name = data_obj['name']
        type = data_obj['type']
        keys = data_obj['keys']
        return IndexOp(action, IndexData(name=name, type=type, keys=keys))