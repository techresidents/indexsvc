from trpycore.factory.base import Factory

from es_indexer import ESIndexer


class IndexerFactory(Factory):
    """Factory for creating Indexer objects."""

    def __init__(self, db_session_factory, index_client_pool, index_name, doc_type):
        """IndexerFactory constructor.

        Args:
            db_session_factory: callable returning a new sqlalchemy db session
            index_client_pool: pool of index client objects
            index_name: index name
            doc_type: document type
        """
        self.db_session_factory = db_session_factory
        self.index_client_pool = index_client_pool
        self.index_name = index_name
        self.doc_type = doc_type

    def create(self):
        """Create an instance of Indexer based upon input name and type

         Returns:
            Instance of Indexer for supported index names/document types.
            Returns None for unsupported name/type combinations.
        """
        ret = None
        if self.index_name == 'users' and self.doc_type == 'user' or\
           self.index_name == 'technologies' and self.doc_type == 'technology' or\
           self.index_name == 'topics' and self.doc_type == 'topic':
            ret = ESIndexer(
                self.db_session_factory,
                self.index_client_pool,
                self.index_name,
                self.doc_type
            )
        return ret
