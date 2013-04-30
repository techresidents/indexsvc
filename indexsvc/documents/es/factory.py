from trpycore.factory.base import Factory

from users import ESUserDocument

class ESDocumentFactory(Factory):
    """Factory for creating ElasticSearch Document objects."""

    def __init__(self, db_session_factory, name, type):
        """ESDocumentFactory constructor.

        Args:
            db_session_factory: callable returning a new sqlalchemy db session
            name: The index name
            type: The document type
        """
        self.db_session_factory = db_session_factory
        self.name = name
        self.type = type

    def create(self):
        """Create an instance of ESDocument based upon input name and type

        Returns:
            Instance of ESDocument for supported index names/document types.
            Returns None for unsupported name/type combinations.
        """
        ret = None
        if self.name == 'users' and self.type == 'user':
            ret = ESUserDocument(self.db_session_factory)
        return ret