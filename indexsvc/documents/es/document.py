import logging


class ESDocument(object):
    """ESDocument objects are responsible for knowing how to fetch
    needed data from our db and generate corresponding ES documents.

    This class is designed to be used as a base class. Derived classes are
    responsible for overriding the generate() method.

    Args:
        db_session_factory: callable returning a new sqlalchemy db session
    """

    def __init__(self, db_session_factory):
        self.log = logging.getLogger(__name__)
        self.db_session_factory = db_session_factory

    def generate(self, key):
        """ Generate JSON document

        Sub-classes should override this method which encapsulates the
        code to lookup data from our db (based upon the input key parameter)
        and returns a JSON dictionary.

        Args:
            key: db key

        Returns:
            JSON dictionary

        """
        pass