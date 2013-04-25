import logging
import os
import sys
import time
import unittest

SERVICE_NAME = "indexsvc"
#Add SERVICE_ROOT to python path, for imports.
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", SERVICE_NAME))
sys.path.insert(0, SERVICE_ROOT)

from trindexsvc.gen.ttypes import IndexData, UnavailableException, InvalidDataException
from trpycore.timezone import tz
from trsvcscore.db.models import IndexJob as IndexJobModel

from testbase import IntegrationTestCase

import settings


class IndexServiceTest(IntegrationTestCase):
    """
        Test the Index Service interface.
    """

    @classmethod
    def setUpClass(cls):
        IntegrationTestCase.setUpClass()

        try:
            cls.db_session = cls.service.handler.get_database_session()
            cls.index_data = IndexData(
                name='users',
                type='user',
                keys=['1']
            )
        except Exception as e:
            logging.exception(e)
            cls.db_session.close()
            raise e

        # Test IndexJob data
        cls.context = 'indexSvcTestContext'
        cls.max_retry_attempts = settings.INDEXER_JOB_MAX_RETRY_ATTEMPTS

    @classmethod
    def tearDownClass(cls):
        IntegrationTestCase.tearDownClass()
        cls.db_session.close()


    def _cleanup_models(self, indexjob_models):
        """ Delete IndexJob models from db.
         Args:
            index_models: list of IndexJob models
        """
        for model in indexjob_models:
            self._cleanup_model(model)

    def _cleanup_model(self, model):
        """Delete IndexJob model from db.

        Args:
            model: IndexJob sqlalchemy model
        """
        try:
            # Clean up index jobs
            job_models = self.db_session.query(IndexJobModel).\
                filter(IndexJobModel.context==model.context).\
                all()
            for model in job_models:
                self.db_session.delete(model)

            # Commit changes to db
            self.db_session.commit()

        except Exception as e:
            logging.exception(e)
            self.db_session.rollback()
            self.db_session.close()
            raise e

    def _validate_indexjob_model(self, model, index_data, expected_retries_remaining):
        """Encapsulate code to validate an IndexJob model.
        Args:
            model: the IndexJob model to validate
            index_data: the Thrift IndexData the model was created from
            expected_retries_remaining: the expected number of retries remaining
        """
        self.assertAlmostEqual(index_data.notBefore, tz.utc_to_timestamp(model.not_before), places=7)
        self.assertIsNotNone(model.created)
        self.assertIsNone(model.start)
        self.assertIsNone(model.end)
        self.assertIsNone(model.owner)
        self.assertIsNone(model.successful)
        self.assertEqual(expected_retries_remaining, model.retries_remaining)

    def test_index(self):
        """Simple test case.
        """
        try:
            # Init models to None to avoid unnecessary cleanup on failure
            index_models = None

            # Create & write IndexJob to db
            self.service_proxy.index(self.context, self.index_data)

            # Verify IndexJob model
            index_job_model = self.db_session.query(IndexJobModel).\
                filter(IndexJobModel.context==self.context).\
                one()
            #self._validate_indexjob_model(index_job_model)

            # Add model to list for cleanup
            if index_models is None:
                index_models = []
            #index_models.append(index_job_model)

            # Allow processing of jobs to take place
            time.sleep(settings.INDEXER_POLL_SECONDS+30)

        finally:
            if index_models is not None:
                self._cleanup_models(index_models)


if __name__ == '__main__':
    unittest.main()
