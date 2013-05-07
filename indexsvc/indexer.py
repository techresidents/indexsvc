import abc
import logging

from documents.es.factory import ESFactory
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

        # es_factory returns an ESDocumentFactory instance
        es_factory = ESFactory(
            self.db_session_factory,
            index_name,
            doc_type
        )
        self.document_factory = es_factory.create()


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
        createdDocsList = []
        with index.flushing():
            # TODO  look at zip
            for key,doc in self.document_factory.generate(indexop.data.keys):
                index.put(key, doc, create=True)
                createdDocsList.append(doc) #TODO delete after testing, return count

            for key in indexop.data.keys:
                doc = self.document_factory.generate(key)
                # setting create=True flag means that the index operation will
                # fail if the document already exists
                index.put(key, doc, create=True)
                createdDocsList.append(doc)
        return createdDocsList

    def update(self, indexop, index):
        updatedDocsList = []
        with index.flushing():
            for key in indexop.data.keys:
                doc = self.document_factory.generate(key)
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