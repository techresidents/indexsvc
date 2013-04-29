import json
import logging

from trindexsvc.gen.ttypes import IndexData


class IndexAction:
    """ Class to represent allowed index operations."""
    Create, Update, Delete = range(3)


class IndexOp(object):
    """ Object to represent data describing an index operation.

    This method represents index operations using the following json:
    {
        action: <index action>
        name: <index name>
        type: <document type>
        keys: <list of keys to perform index operation on>
    }

    Args:
        action: IndexAction enum
        data: Thrift IndexData object
    """
    def __init__(self, action, data):
        self.log = logging.getLogger(__name__)
        self.action = action
        self.data = data

    def to_json(self):
        """ Return IndexOp as JSON formatted string"""

        # Grab only the pertinent info from the input Thrift IndexData obj.
        # Note that this doesn't include the index operation.
        index_data_json = json.dumps(self.data, cls=Encoder)

        # Add the index action to this JSON data so that this object
        # completely specifies the indexing work that needs to be done.
        index_data = json.loads(index_data_json)
        index_data['action'] = self.action
        return json.dumps(index_data)

    @staticmethod
    def from_json(json):
        """ Return IndexOp object from JSON formatted string"""
        data = json.loads(json)
        action = data['action']
        name = data['name']
        type = data['type']
        keys = data['keys']
        return IndexOp(action, IndexData(name=name, type=type, keys=keys))



class Encoder(json.JSONEncoder):
    """Encoder to encode Thrift IndexData objects

    Args:
        action: action for the indexer to perform.
            Supported values: 'CREATE', 'UPDATE', 'DELETE'
    """
    def __init__(self, *args, **kwargs):
        super(Encoder, self).__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, IndexData):
            return {
                "name": obj.name,
                "type": obj.type,
                "keys": [key for key in obj.keys]
            }
        return json.JSONEncoder.default(self, obj)