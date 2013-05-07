import logging


class DocumentGenerator(object):
    """DocumentGenerator objects are responsible for knowing how to fetch
    needed data from the db and generate indexable documents.

    This class is designed to be used as a base class. Derived classes are
    responsible for overriding the generate() method.

    Args:
        db_session_factory: callable returning a new sqlalchemy db session
    """

    def __init__(self, db_session_factory):
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory

    def generate(self, keys):
        """ Generate a document

        Sub-classes should override this method which encapsulates the
        code to lookup data from our db (based upon the input keys parameter)
        and return an indexable document.

        Args:
            keys: list of db keys

        Returns:
            Uses a generator to return an indexable document

        """
        pass