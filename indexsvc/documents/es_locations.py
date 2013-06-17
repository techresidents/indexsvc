from trsvcscore.db.models import Location

from document import DocumentGenerator


class ESLocationDocumentGenerator(DocumentGenerator):
    """ESLocationDocumentGenerator generates ES Location docs."""

    def __init__(self, db_session_factory):
        super(ESLocationDocumentGenerator, self).__init__(db_session_factory)

    def generate(self, keys):
        """Generates a JSON dict that can be indexed by ES

        Args:
            key: user db key
        Returns:
            Uses a generator to return a tuple of (key, JSON dictionary)
        """
        try:
            db_session = self.db_session_factory()
            query = db_session.query(Location)
            if len(keys):
                query = query.filter(Location.id.in_(keys))

            for location in query.all():
                location_json = {
                    "id": location.id,
                    "region": location.region
                }
                yield (location.id, location_json)

            db_session.commit()

        finally:
            if db_session:
                db_session.close()