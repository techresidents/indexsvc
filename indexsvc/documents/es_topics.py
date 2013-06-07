from sqlalchemy.orm import joinedload

from trsvcscore.db.models import Topic
from trsvcscore.db.managers.tree import TreeManager

from document import DocumentGenerator


class ESTopicDocumentGenerator(DocumentGenerator):
    """ESTopicDocumentGenerator generates ES Topic docs."""

    def __init__(self, db_session_factory):
        super(ESTopicDocumentGenerator, self).__init__(db_session_factory)

    def _topic_to_json(self, topic, level):
        """ Converts a Topic object to JSON representation

         This method is intended to be used only for constructing the
         topic tree which is indexed.  It contains fields that are not
         included in the root topics that are indexed.

         Args:
            topic: Topic object
            level: topic level
        Returns:
            JSON dict
        """
        return {
            "id": topic.id,
            "type_id": topic.type_id,
            "type": topic.type.name,
            "duration": topic.duration,
            "title": topic.title,
            "description": topic.description,
            "recommended_participants": topic.recommended_participants,
            "rank": topic.rank,
            "public": topic.public,
            "active": topic.active,
            "level": level
        }

    def generate(self, keys):
        """Generates a JSON dict that can be indexed by ES

        Args:
            key: user db key
        Returns:
            Uses a generator to return a tuple of (key, JSON dictionary)
        """
        try:
            db_session = self.db_session_factory()

            # Only index root topics since there aren't any use cases at
            # the present time to search for sub-topics.  Subtopic titles
            # and descriptions are indexed via the 'subtopic_summary' field.
            root_topic_index = 0
            query = db_session.query(Topic).options(joinedload(Topic.type)) # TODO alternative to loading on Topic type using Enum
            query = query.filter(Topic.rank == root_topic_index)
            if len(keys):
                query = query.filter(Topic.id.in_(keys))

            for topic in query.all():

                # Create JSON topic tree
                topic_tree = []
                tree_manager = TreeManager(Topic)
                for topic, level in tree_manager.tree_by_rank(db_session, topic.id):
                    topic_tree.append(self._topic_to_json(topic, level))

                # Combine subtopic titles and descriptions
                subtopic_summary = ''
                for subtopic in topic.children:
                    subtopic_summary += subtopic.title + ': ' + subtopic.description

                topic_json = {
                    "id": topic.id,
                    "type": topic.type.name,
                    "duration": topic.duration,
                    "title": topic.title,
                    "description": topic.description,
                    "subtopic_summary": subtopic_summary,
                    "tree": topic_tree
                }
                yield (topic.id, topic_json)

            db_session.commit()

        finally:
            if db_session:
                db_session.close()
