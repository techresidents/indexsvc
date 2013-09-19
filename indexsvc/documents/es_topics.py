from sqlalchemy.orm import joinedload

from trsvcscore.db.models import Topic, TopicTag, Tag
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
            root_topic_rank = 0

            # TODO alternative to loading on Topic type using Enum
            query = db_session.query(Topic).options(joinedload(Topic.type))
            query = query.filter(Topic.rank == root_topic_rank)
            if len(keys):
                query = query.filter(Topic.id.in_(keys))

            for root_topic in query.all():
                # Combine subtopic titles and descriptions
                subtopic_summary = ''

                # Create JSON topic tree
                topic_tree = []

                tree_manager = TreeManager(Topic)
                for topic, level in tree_manager.tree_by_rank(db_session, root_topic.id):
                    topic_tree.append(self._topic_to_json(topic, level))
                    # Skip adding the root topic's title & description to subtopic_summary
                    if topic.rank != root_topic_rank:
                        subtopic_summary += topic.title + ' ' + topic.description

                #tags
                tags = db_session.query(Tag)\
                        .join(TopicTag)\
                        .filter(TopicTag.topic_id == root_topic.id)\
                        .all()
                tags_json = []
                for tag in tags:
                    tags_json.append({
                        "id": tag.id,
                        "name": tag.name
                    })

                topic_json = {
                    "id": root_topic.id,
                    "type": root_topic.type.name,
                    "duration": root_topic.duration,
                    "title": root_topic.title,
                    "description": root_topic.description,
                    "subtopic_summary": subtopic_summary,
                    "public": topic.public,
                    "active": topic.active,
                    "tree": topic_tree,
                    "tags": tags_json
                }

                yield (root_topic.id, topic_json)

            db_session.commit()

        finally:
            if db_session:
                db_session.close()
