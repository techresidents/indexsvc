import abc


class Indexer(object):
    """Indexer abstract base class.

    Base class for concrete Indexer implementations.
    The concrete class is responsible for doing the actual
    work of indexing data and communicating with the index.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, db_session_factory, index_client_pool):
        """Indexer constructor.

        Args:
            db_session_factory: callable returning a new sqlalchemy db session
            index_client_pool: Pool of index client objects
        """
        self.db_session_factory = db_session_factory
        self.index_client_pool = index_client_pool

    @abc.abstractmethod
    def index(self, indexop):
        """ Perform indexing.

        Args:
            indexop: IndexOp object

        Returns:
            None
        """
        return