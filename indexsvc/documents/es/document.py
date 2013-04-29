import logging


class ESDocument(object):
    """ESDocument objects are responsible for knowing how to fetch
    needed data from our db and generate corresponding ES documents.

    This class is designed to be used as a base class. Derived classes are
    responsible for overriding the generate() method.

    Args:
        db_session_factory: callable returning a new sqlalchemy db session
        name: index name
        type: document type
    """

    def __init__(self, db_session_factory, name, type):
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory
        self.name = name
        self.type = type

    def generate(self, key):
        """ Generate JSON document

        Sub-classes should override this method which encapsulates the
        code to lookup data from our db (based upon the input key)
        and return a JSON formatted string that can be indexed.

        Args:
            key: db key

        Returns:
            JSON formatted string which can be indexed

        """
        pass


class ESUserDocument(ESDocument):
    """ Responsible for generating an ElasticSearch user document"""

    def __init__(self, db_session_factory, name, type):
        super(ESUserDocument, self).__init__(db_session_factory, name, type)

    def generate(self, key):
        try:
            db_session = self.db_session_factory()

            # TODO
            # lookup key and associated data
            # read ES schema?
            # generate ES document JSON

        except Exception as e:
            self.log.exception(e)
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()
