import abc
import logging

from documents.es.factory import ESFactory
from indexop import IndexAction


class IndexerDelegate(object):
    """IndexerDelegate abstract base class.

    Base class for concrete IndexerDelegate implementations.
    The concrete class is responsible for doing the actual
    work of indexing data and communicating with the index.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, db_session_factory, index_client_pool):
        """IndexerDelegate constructor.

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


class GenericIndexer(IndexerDelegate):
    """ Generic Indexer

    This indexer utilizes an ElasticSearch bulk indexer object, and an
    ElasticSearch document object.  The ESDocument object is generated
    dynamically based upon the provided index name and document type.

    This IndexerDelegate subclass has no special functionality in
    its index() method.  It simply iterates through the list of
    specified keys and invokes the underlying ElasticSearch client.
    """
    def __init__(self, db_session_factory, index_client_pool):
        """ GenericIndexer Constructor

         Args:
            db_session_factory: callable returning a new sqlalchemy db session
            index_client_pool: pool of index client objects
        """
        super(GenericIndexer, self).__init__(db_session_factory, index_client_pool)
        self.log = logging.getLogger(__name__)


    def index(self, indexop):

        es_factory = ESFactory(
            self.db_session_factory,
            indexop.data.name,
            indexop.data.type
        )
        # es_factory returns an ESDocumentFactory instance
        document_factory = es_factory.create()

        # Get ESClient
        with self.index_client_pool.get() as es_client:
            # get bulk index
            index = es_client.get_bulk_index(
                indexop.data.name,
                indexop.data.type,
                autoflush=20
            )
            # perform index operation
            if indexop.action == IndexAction.Create:
                self.create(indexop, index, document_factory)
            elif indexop.action == IndexAction.Update:
                self.update(indexop, index, document_factory)
            elif indexop.action == IndexAction.Delete:
                self.delete(indexop, index)
            else:
                self.log.error("Index action not supported.")


    def create(self, indexop, index, document_factory):
        createdDocsList = []
        with index.flushing():
            for key in indexop.data.keys:
                doc = document_factory.generate(key)
                # setting create=True flag means that the index operation will
                # fail if the document already exists
                index.put(key, doc, create=True)
                createdDocsList.append(doc)
        return createdDocsList

    def update(self, indexop, index, document_factory):
        updatedDocsList = []
        with index.flushing():
            for key in indexop.data.keys:
                doc = document_factory.generate(key)
                # setting create=False means that the index operation will
                # succeed if the document already exists.  It also means that
                # the document *will be* created if it doesn't already exist.
                index.put(key, doc, create=False)
                updatedDocsList.append(doc)
        return updatedDocsList

    def delete(self, indexop, index):
        deletedKeysList = []
        with index.flushing():
            for key in indexop.data.keys:
                index.delete(key)
                deletedKeysList.append(key)
        return deletedKeysList