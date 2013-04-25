import json
import logging

from sqlalchemy.sql import func

from trpycore.factory.base import Factory
from trpycore.pool.queue import QueuePool
from trpycore.thread.util import join
from trpycore.timezone import tz
from trsvcscore.db.models import IndexJob as IndexJobModel
from trsvcscore.service.handler.service import ServiceHandler
from trindexsvc.gen import TIndexService
from trindexsvc.gen.ttypes import UnavailableException, InvalidDataException

import settings

from encoder import Encoder
from jobmonitor import IndexJobMonitor, IndexThreadPool
from indexer import Indexer


class IndexServiceHandler(TIndexService.Iface, ServiceHandler):
    """IndexServiceHandler manages the index service.

    This class specifies the service interface.
    The handler base class provides functionality to register the
    service with ZooKeeper, and sets up connections to our db using
    SQLAlchemy.

    """
    def __init__(self, service):
        super(IndexServiceHandler, self).__init__(
		    service,
            zookeeper_hosts=settings.ZOOKEEPER_HOSTS,
            database_connection=settings.DATABASE_CONNECTION)

        self.log = logging.getLogger("%s.%s" % (__name__, IndexServiceHandler.__name__))

        # Create pool of Indexer objects which will do the
        # actual work of indexing.
        def indexer_factory():
            return Indexer(
                db_session_factory=self.get_database_session,
                job_retry_seconds=settings.INDEXER_JOB_RETRY_SECONDS
            )
        self.indexer_pool = QueuePool(
            size=settings.INDEXER_POOL_SIZE,
            factory=Factory(indexer_factory))

        # Create pool of threads to manage the work
        self.thread_pool = IndexThreadPool(
            num_threads=settings.INDEXER_THREADS,
            indexer_pool=self.indexer_pool)

        # Create job monitor which scans for new jobs
        # to process and delegates to the thread pool
        self.job_monitor = IndexJobMonitor(
            db_session_factory=self.get_database_session,
            thread_pool=self.thread_pool,
            poll_seconds=settings.INDEXER_POLL_SECONDS)

    def start(self):
        """Start handler."""
        super(IndexServiceHandler, self).start()
        self.thread_pool.start()
        self.job_monitor.start()

    def stop(self):
        """Stop handler."""
        self.job_monitor.stop()
        self.thread_pool.stop()
        super(IndexServiceHandler, self).stop()

    def join(self, timeout=None):
        """Join handler."""
        join([self.thread_pool, self.job_monitor, super(IndexServiceHandler, self)], timeout)

    def _validate_index_params(self, context, index_data, index_all):
        """Validate input params of the index() method
        """
        if not context:
            raise InvalidDataException('Invalid context')
        # TODO validate index_data

    def index(self, context, index_data):
        """Index data for specified keys. Use to update an existing index.

        This method creates a job to index the specified input data.

        Args:
            context: String to identify calling context
            index_data: Thrift IndexData object.
        Returns:
            None
        Raises:
            InvalidDataException if input data to index is invalid.
            UnavailableException for any other unexpected error.
        """
        try:
            return self._index(context, index_data, index_all=False)

        except InvalidDataException as error:
            self.log.exception(error)
            raise InvalidDataException()
        except Exception as error:
            self.log.exception(error)
            raise UnavailableException(str(error))

    def indexAll(self, context, index_data):
        """Index data for all keys. Use to update an existing index.

        This method creates a job to index the specified input data.

        Args:
            context: String to identify calling context
            index_data: Thrift IndexData object.
        Returns:
            None
        Raises:
            InvalidDataException if input data to index is invalid.
            UnavailableException for any other unexpected error.
        """
        try:
            return self._index(context, index_data, index_all=True)

        except InvalidDataException as error:
            self.log.exception(error)
            raise InvalidDataException()
        except Exception as error:
            self.log.exception(error)
            raise UnavailableException(str(error))

    def _index(self, context, index_data, index_all=False):
        """Helper function. Pulled out common code from index() & indexAll().

        This method creates a job to index the specified input data.

        Args:
            context: String to identify calling context
            index_data: Thrift IndexData object.
        Returns:
            None
        Raises:
            InvalidDataException if input data to index is invalid.
            UnavailableException for any other unexpected error.
        """
        try:
            # Validate inputs
            self._validate_index_params(context, index_data, index_all)

            # Get a db session
            db_session = self.get_database_session()

            # If input specified a start-processing-time
            # convert it to UTC DateTime object.
            if index_data.notBefore is not None:
                processing_start_time = tz.timestamp_to_utc(index_data.notBefore)
            else:
                processing_start_time = func.current_timestamp()

            # Create JSON representation of the input index data
            index_data_json = json.dumps(index_data, cls=Encoder)
            # Add the index operation to this JSON data so that the IndexJob
            # completely specifies the work that needs to be done.
            data = json.loads(index_data_json)
            data['action'] = 'UPDATE'

            # Create IndexJob
            job = IndexJobModel(
                created=func.current_timestamp(),
                context=context,
                not_before=processing_start_time,
                retries_remaining=settings.INDEXER_JOB_MAX_RETRY_ATTEMPTS,
                data=json.dumps(data)
            )
            db_session.add(job)
            db_session.commit()
            return

        finally:
            db_session.close()
