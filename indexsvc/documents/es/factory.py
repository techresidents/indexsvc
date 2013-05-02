from trpycore.factory.base import Factory

from users import ESUserDocumentFactory


class ESFactory(Factory):
    """Factory for creating ElasticSearch document factories."""

    def __init__(self, db_session_factory, name, type):
        """ESFactory constructor.

        Args:
            db_session_factory: callable returning a new sqlalchemy db session
            name: The index name
            type: The document type
        """
        self.db_session_factory = db_session_factory
        self.name = name
        self.type = type

    def create(self):
        """Create an instance of ESDocumentFactory based upon input name and type

        Returns:
            Instance of ESDocumentFactory for supported index names/document types.
            Returns None for unsupported name/type combinations.
        """
        ret = None
        if self.name == 'users' and self.type == 'user':
            ret = ESUserDocumentFactory(self.db_session_factory)
        return ret