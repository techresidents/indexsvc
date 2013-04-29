import abc
import logging

from tres.index import BulkIndex

from documents.es.factory import ESDocumentFactory
from indexop import IndexAction


class IndexerDelegate(object):
    """IndexerDelegate abstract base class.

    Base class for concrete IndexerDelegate implementations.
    The concrete class is responsible for doing the actual
    work of indexing data.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, db_session_factory, indexop):
        """IndexerDelegate constructor.

        Args:
            db_session_factory: callable returning a new sqlalchemy db session
            indexop: IndexOp object
        """
        self.db_session_factory = db_session_factory
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
    def __init__(self, indexop):
        super(GenericIndexer, self).__init__(indexop)
        self.log = logging.getLogger(__name__)

        es_client = ''
        self.indexer = BulkIndex(
            es_client,
            self.indexop.name,
            self.indexop.type,
            autoflush=100
        )

        index_document_factory = ESDocumentFactory(
            self.db_session_factory,
            self.indexop.name,
            self.indexop.type
        )
        self.document = index_document_factory.create()


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
        for key in self.indexop.keys:
            doc = self.document.generate(key)
            createdDocsList.append(doc)
            self.indexer.put(key, doc, create=True, type=self.indexop.type)
        self.indexer.flush()
        return createdDocsList

    def update(self):
        updatedDocsList = []
        for key in self.indexop.keys:
            doc = self.document.generate(key)
            updatedDocsList.append(doc)
            self.indexer.put(key, doc, create=False, type=self.indexop.type)
        self.indexer.flush()
        return updatedDocsList

    def delete(self):
        deletedKeysList = []
        for key in self.indexop.keys:
            self.indexer.delete(key, type=self.indexop.type)
            deletedKeysList.append(key)
        self.indexer.flush()
        return deletedKeysList