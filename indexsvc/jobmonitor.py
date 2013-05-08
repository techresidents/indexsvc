
import logging
import threading

from trpycore.thread.util import join
from trpycore.thread.threadpool import ThreadPool
from trsvcscore.db.models import IndexJob
from trsvcscore.db.job import DatabaseJobQueue, QueueEmpty, QueueStopped



class IndexThreadPool(ThreadPool):
    """Thread pool used to index documents.

    Given a work item (a databasejob), this class will process the
    job and delegate the work to do the indexing.
    """
    def __init__(self, num_threads, indexer_coordinator_pool):
        """Constructor.

        Arguments:
            num_threads: number of worker threads
            indexer_pool: pool of IndexerCoordinator objects responsible for
                doing the indexing work
        """
        super(IndexThreadPool, self).__init__(num_threads)
        self.log = logging.getLogger(__name__)
        self.indexer_coordinator_pool = indexer_coordinator_pool


    def process(self, database_job):
        """Worker thread process method.

        This method will be invoked by each worker thread when
        a new work item (job) is put on the queue.

        Args:
            database_job: DatabaseJob object, or objected derived from DatabaseJob
        """
        try:
            with self.indexer_coordinator_pool.get() as indexer_coordinator:
                indexer_coordinator.index(database_job)

        except Exception as e:
            self.log.exception(e)



class IndexJobMonitor(object):
    """Index Job monitor

    This class monitors for new index jobs,
    and delegates work items to a thread pool.
    """
    def __init__(self, db_session_factory, thread_pool, poll_seconds=60):
        """Constructor.

        Arguments:
            db_session_factory: callable returning a new sqlalchemy db session
            thread_pool: pool of worker threads
            poll_seconds: number of seconds between db queries to detect
                new jobs.
        """
        self.log = logging.getLogger(__name__)
        self.thread_pool = thread_pool

        self.db_job_queue = DatabaseJobQueue(
            owner='indexsvc',
            model_class=IndexJob,
            db_session_factory=db_session_factory,
            poll_seconds=poll_seconds,
        )

        self.monitor_thread = None
        self.running = False


    def start(self):
        """Start job monitor."""
        if not self.running:
            self.running = True
            self.db_job_queue.start()
            self.monitor_thread = threading.Thread(target=self.run)
            self.monitor_thread.start()


    def run(self):
        """Monitor thread run method."""
        while self.running:
            try:
                self.log.info("IndexJobMonitor is checking for new jobs to process...")

                # Grab jobs as they arrive and delegate
                # jobs to threadpool for processing
                job = self.db_job_queue.get()
                self.thread_pool.put(job)

            except QueueEmpty:
                pass
            except QueueStopped:
                break
            except Exception as error:
                self.log.exception(error)

        self.running = False


    def stop(self):
        """Stop monitor."""
        if self.running:
            self.running = False
            self.db_job_queue.stop()


    def join(self, timeout):
        """Join all threads."""
        threads = [self.db_job_queue]
        if self.monitor_thread is not None:
            threads.append(self.monitor_thread)
        join(threads, timeout)
