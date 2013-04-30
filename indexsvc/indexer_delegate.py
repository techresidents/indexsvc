import abc
import logging

from documents.es.factory import ESDocumentFactory
from indexop import IndexAction


class IndexerDelegate(object):
    """IndexerDelegate abstract base class.

    Base class for concrete IndexerDelegate implementations.
    The concrete class is responsible for doing the actual
    work of indexing data.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, db_session_factory, index_client_pool, indexop):
        """IndexerDelegate constructor.

        Args:
            db_session_factory: callable returning a new sqlalchemy db session
            index_client_pool: Pool of index client objects
            indexop: IndexOp object
        """
        self.db_session_factory = db_session_factory
        self.index_client_pool = index_client_pool
        self.indexop = indexop

    @abc.abstractmethod
    def index(self):
        """ Perform indexing.

        This method will invoke create(), update(), or delete() based upon
        the specified index operation.

        Returns:
            None
        """
        return

    @abc.abstractmethod
    def create(self):
        """ Creates an index for the specified keys

        Returns:
            List of documents created
        """
        return

    @abc.abstractmethod
    def update(self):
        """Updates an index for the specified keys

        Returns:
            List of documents updated
        """
        return

    @abc.abstractmethod
    def delete(self):
        """Deletes an index for the specified keys

        Returns:
            List of keys deleted from index
        """
        return


class GenericIndexer(IndexerDelegate):
    """ Generic Indexer

    This indexer utilizes an ElasticSearch bulk indexer object, and an
    ElasticSearch document object.  The ESDocument object is generated
    dynamically based upon the provided index name and document type.

    This IndexerDelegate subclass has no special functionality in
    its create, update, and delete methods.  It simply iterates through
    the list of specified keys and invokes the ElasticSearch client methods.
    """
    def __init__(self, db_session_factory, index_client_pool, indexop):
        super(GenericIndexer, self).__init__(db_session_factory, index_client_pool, indexop)
        self.log = logging.getLogger(__name__)

        index_document_factory = ESDocumentFactory(
            self.db_session_factory,
            self.indexop.data.name,
            self.indexop.data.type
        )
        self.document = index_document_factory.create()

        # Get ES Client
        with self.index_client_pool.get() as es_client:
            self.indexer = es_client.get_bulk_index(
                self.indexop.data.name,
                self.indexop.data.type,
                autoflush=20
            )


    def index(self):
        if self.indexop.action == IndexAction.Create:
            self.create()
        elif self.indexop.action == IndexAction.Update:
            self.update()
        elif self.indexop.action == IndexAction.Delete:
            self.delete()
        else:
            self.log.error("Index action not supported.")

    def create(self):
        createdDocsList = []
        with self.indexer.flushing():
            for key in self.indexop.data.keys:
                doc = self.document.generate(key)
                #self.indexer.put(key, doc, create=True)
                createdDocsList.append(doc)
        return createdDocsList

    def update(self):
        updatedDocsList = []
        with self.indexer.flushing():
            for key in self.indexop.data.keys:
                doc = self.document.generate(key)
                self.indexer.put(key, doc, create=False)
                updatedDocsList.append(doc)
        return updatedDocsList

    def delete(self):
        deletedKeysList = []
        with self.indexer.flushing():
            for key in self.indexop.data.keys:
                #self.indexer.delete(key)
                deletedKeysList.append(key)
        return deletedKeysList