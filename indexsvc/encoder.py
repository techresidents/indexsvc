import json

from trindexsvc.gen.ttypes import IndexData

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