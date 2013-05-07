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
        """Return instance of Indexer"""
        return ESIndexer(
            self.db_session_factory,
            self.index_client_pool,
            self.index_name,
            self.doc_type
        )
        # We only have a ESIndexer right now, so return that.
        # For the future, we'll return an indexer based upon the input
        # index name and document type, like this:
        # if index_name == 'users' and doc_type == 'user':
        #    ret = ESIndexer()