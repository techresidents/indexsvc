from trpycore.factory.base import Factory

from es_users import ESUserDocumentGenerator
from es_technologies import ESTechnologyDocumentGenerator
from es_topics import ESTopicDocumentGenerator
from es_locations import ESLocationDocumentGenerator


class DocumentGeneratorFactory(Factory):
    """Factory for creating DocumentGenerator objects."""

    def __init__(self, db_session_factory, name, type):
        """DocumentGeneratorFactory constructor.

        Args:
            db_session_factory: callable returning a new sqlalchemy db session
            name: The index name
            type: The document type
        """
        self.db_session_factory = db_session_factory
        self.name = name
        self.type = type

    def create(self):
        """Create an instance of DocumentGenerator based upon input name and type

        Returns:
            Instance of DocumentGenerator for supported index names/document types.
            Returns None for unsupported name/type combinations.
        """
        ret = None
        if self.name == 'users' and self.type == 'user':
            ret = ESUserDocumentGenerator(self.db_session_factory)
        elif self.name == 'technologies' and self.type == 'technology':
            ret = ESTechnologyDocumentGenerator(self.db_session_factory)
        elif self.name == 'topics' and self.type == 'topic':
            ret = ESTopicDocumentGenerator(self.db_session_factory)
        elif self.name == 'locations' and self.type == 'location':
            ret = ESLocationDocumentGenerator(self.db_session_factory)
        return ret
