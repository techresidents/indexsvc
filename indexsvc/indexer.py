import abc
import logging

from documents.factory import DocumentGeneratorFactory
from indexop import IndexAction


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


class ESIndexer(Indexer):
    """ ElasticSearch Indexer

    This indexer utilizes an ElasticSearch bulk indexer object, and an
    ElasticSearch document object.  The ESDocument object is generated
    dynamically based upon the provided index name and document type.

    This Indexer subclass has no special functionality in
    its index() method.  It simply iterates through the list of
    specified keys and invokes the underlying ElasticSearch client.
    """
    def __init__(self, db_session_factory, index_client_pool, index_name, doc_type):
        """ ESIndexer Constructor

         Args:
            db_session_factory: callable returning a new sqlalchemy db session
            index_client_pool: pool of index client objects
            index_name: index name
            doc_type: document type
        """
        super(ESIndexer, self).__init__(db_session_factory, index_client_pool)
        self.log = logging.getLogger(__name__)

        # get an DocumentGeneratorFactory instance
        factory = DocumentGeneratorFactory(
            self.db_session_factory,
            index_name,
            doc_type
        )
        self.document_generator = factory.create()


    def index(self, indexop):

        # Get an ESClient and perform indexing
        with self.index_client_pool.get() as es_client:
            # get bulk index
            index = es_client.get_bulk_index(
                indexop.data.name,
                indexop.data.type,
                autoflush=20
            )
            # perform index operation
            if indexop.action == IndexAction.Create:
                self.create(indexop, index)
            elif indexop.action == IndexAction.Update:
                self.update(indexop, index)
            elif indexop.action == IndexAction.Delete:
                self.delete(indexop, index)
            else:
                self.log.error("Index action not supported.")


    def create(self, indexop, index):
        createdDocsCount = 0
        with index.flushing():
            for key,doc in self.document_generator.generate(indexop.data.keys):
                # setting create=True flag means that the index operation will
                # fail if the document already exists
                index.put(key, doc, create=True)
                createdDocsCount += 1
        return createdDocsCount

    def update(self, indexop, index):
        updatedDocsCount = 0
        with index.flushing():
            for key,doc in self.document_generator.generate(indexop.data.keys):
                # setting create=False means that the index operation will
                # succeed if the document already exists.  It also means that
                # the document *will be* created if it doesn't already exist.
                index.put(key, doc, create=False)
                updatedDocsCount += 1
        return updatedDocsCount

    def delete(self, indexop, index):
        deletedKeysCount = 0
        with index.flushing():
            for key in indexop.data.keys:
                index.delete(key)
                deletedKeysCount += 1
        return deletedKeysCount