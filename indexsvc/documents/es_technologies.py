from sqlalchemy.orm import joinedload

from trsvcscore.db.models import Technology

from document import DocumentGenerator


class ESTechnologyDocumentGenerator(DocumentGenerator):
    """ESTechnologyDocumentGenerator generates ES Technology docs."""

    def __init__(self, db_session_factory):
        super(ESTechnologyDocumentGenerator, self).__init__(db_session_factory)

    def generate(self, keys):
        """Generates a JSON dict that can be indexed by ES

        Args:
            key: user db key
        Returns:
            Uses a generator to return a tuple of (key, JSON dictionary)
        """
        try:
            db_session = self.db_session_factory()

            query = db_session.query(Technology).options(joinedload(Technology.type))
            if len(keys):
                query = query.filter(Technology.id.in_(keys))
            
            for technology in query.all():
                
                technology_json = {
                    "id": technology.id,
                    "name": technology.name,
                    "description": technology.description,
                    "type_id": technology.type_id,
                    "type": technology.type.name
                }
                yield (technology.id, technology_json)
            
            db_session.commit()

        finally:
            if db_session:
                db_session.close()
