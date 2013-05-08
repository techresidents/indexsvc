import datetime
import logging

from sqlalchemy.sql import func

from trpycore.timezone import tz
from trsvcscore.db.models import IndexJob
from trsvcscore.db.job import JobOwned

from indexers.factory import IndexerFactory
from indexop import IndexOp


class IndexerCoordinator(object):
    """ IndexerCoordinator is responsible for processing IndexJobs and delegating
    the work of indexing to Indexer objects.

    Args:
        db_session_factory: callable returning a new sqlalchemy db session
        job_retry_seconds: number of seconds delay between job retries
        index_client_pool: pool of index client objects
            Index clients are responsible for communicating with the
            search service (e.g. ElasticSearch)
    """

    def __init__(self, db_session_factory, job_retry_seconds, index_client_pool):
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        self.job_retry_seconds = job_retry_seconds
        self.index_client_pool = index_client_pool


    def _retry_job(self, failed_job):
        """Create a new IndexJob from a failed job.

        This method creates a new IndexJob from a
        job that failed processing.

        Args:
            failed_job: DatabaseJob object, or objected derived from DatabaseJob
        Returns:
            None
        """
        try:
            db_session = None

            #create new job in db to retry.
            if failed_job.retries_remaining > 0:
                not_before = tz.utcnow() + datetime.timedelta(seconds=self.job_retry_seconds)
                new_job = IndexJob(
                    data=failed_job.data,
                    context=failed_job.context,
                    created=func.current_timestamp(),
                    not_before=not_before,
                    retries_remaining=failed_job.retries_remaining-1
                )
                # Add job to db
                db_session = self.db_session_factory()
                db_session.add(new_job)
                db_session.commit()
            else:
                self.log.info("No retries remaining for job for index_job_id=%s"\
                              % (failed_job.id))
                self.log.error("Job for index_job_id=%s failed!"\
                               % (failed_job.id))
        except Exception as e:
            self.log.exception(e)
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()


    def index(self, database_job):
        """ Index the data specified by the input job.

        Args:
            database_job: DatabaseJob object, or objected derived from DatabaseJob
        Returns:
            None
        """
        try:
            with database_job as job:

                # Claiming the job and finishing the job are
                # handled by this context manager. Here, we
                # specify how to process the job. The context
                # manager returns 'job' as an IndexJob
                # db model object.
                indexop = IndexOp.from_json(job.data)
                factory = IndexerFactory(
                    self.db_session_factory,
                    self.index_client_pool,
                    indexop.data.name,
                    indexop.data.type
                )
                indexer = factory.create()
                indexer.index(indexop)
                self.log.info("IndexJob with index_job_id=%d successfully processed" % job.id)
                # TODO return async object

        except JobOwned:
            # This means that the IndexJob was claimed just before
            # this thread claimed it. Stop processing the job. There's
            # no need to abort the job since no processing of the job
            # has occurred.
            self.log.warning("IndexJob with index_job_id=%d already claimed. Stopping processing." % job.id)
        except Exception as e:
            #failure during processing.
            self.log.exception(e)
            self._retry_job(job)