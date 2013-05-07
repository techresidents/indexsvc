from datetime import datetime
import pprint

from trsvcscore.db.models import User

from document import DocumentGenerator


class ESUserDocumentGenerator(DocumentGenerator):
    """ ESUserDocumentGenerator is responsible for generating an ElasticSearch user document

    This class is responsible for fetching all needed data from the db
    based upon the input keys parameter, and returning a JSON dictionary that
    can be indexed by ES.
    """

    def __init__(self, db_session_factory):
        super(ESUserDocumentGenerator, self).__init__(db_session_factory)

    def generate(self, keys):
        """Generates a JSON dict that can be indexed by ES

        Args:
            key: user db key
        Returns:
            A tuple of (key, JSON dictionary)
        """
        try:
            # lookup user and associated data
            db_session = self.db_session_factory()

            # Read all users at once as performance optimization
            developer_tenant_id = 1
            query = db_session.query(User).filter(User.tenant_id==developer_tenant_id)
            if len(keys):
                query = query.filter(User.id.in_(keys))
            # An empty keys list implies to index all keys
            users = query.all()

            for user in users:
                # generate ES document JSON
                es_user = ESUserDocument(user.id, user.date_joined)
                for skill in user.skills:
                    es_user.add_skill(skill)
                for location_pref in user.job_location_prefs:
                    es_user.add_location_pref(location_pref)
                for technology_pref in user.job_technology_prefs:
                    es_user.add_technology_pref(technology_pref)
                for position_pref in user.job_position_type_prefs:
                    es_user.add_position_pref(position_pref)
                # Calculate total yrs experience
                if user.developer_profile.developer_since:
                    current_year = datetime.now().year
                    yrs_experience = current_year - user.developer_profile.developer_since.year
                    es_user.set_yrs_experience(yrs_experience)
                else:
                    # Derive total yrs experience from the skill with the most yrs
                    yrs_experience = None
                    for skill in es_user.skills:
                        if skill['yrs_experience'] > yrs_experience:
                            yrs_experience = skill['yrs_experience']
                    es_user.set_yrs_experience(yrs_experience)

                # return (key, doc) tuple
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(es_user.to_json())
                yield (user.id, es_user.to_json())

        finally:
            if db_session:
                db_session.close()



class ESUserDocument(object):
    """ESUserDocument holds all of the data needed to generate the ESUserDocument JSON
    """
    def __init__(self, id, date_joined):
        """ESUserDocument Constructor

        Args:
            id: user db ID
            date_jointed: date object that reps when user joined TechResidents
        """
        self.id = id
        self.joined = date_joined
        self.skills = []
        self.technology_prefs = []
        self.location_prefs = []
        self.position_prefs = []
        self.yrs_experience = None
        self.score = 0

    def to_json(self):
        """ Return a JSON dictionary"""
        return {
            'id': self.id,
            'skills': self.skills,
            'technology_prefs': self.technology_prefs,
            'location_prefs': self.location_prefs,
            'position_prefs': self.position_prefs,
            'yrs_experience': self.yrs_experience,
            'joined': self.joined,
            'score': self.score
        }

    def add_skill(self, skill):
        """add_skill

         Args:
            skill: SQLAlchemy Skill object
        Returns:
            None
        """
        skill_dict = {
            'id': skill.id,
            'name': skill.technology.name,
            'yrs_experience': skill.yrs_experience,
            'technology_id': skill.technology.id,
            'expertise_type_id': skill.expertise_type.id,
            'expertise_type': skill.expertise_type.name
        }
        self.skills.append(skill_dict)

    def add_location_pref(self, location_pref):
        """add_location_pref

         Args:
            skill: SQLAlchemy JobLocationPref object
        Returns:
            None
        """
        city = location_pref.location.city
        state = location_pref.location.state
        city_state = city + ', ' + state
        location_pref_dict = {
            'id': location_pref.id,
            'location_id': location_pref.location.id,
            'city': city,
            'state': state,
            'name': city_state if city else state
        }
        self.location_prefs.append(location_pref_dict)

    def add_technology_pref(self, technology_pref):
        """add_technology_pref

         Args:
            skill: SQLAlchemy JobTechnologyPref object
        Returns:
            None
        """
        technology_pref_dict = {
            'id': technology_pref.id,
            'name': technology_pref.technology.name,
            'technology_id': technology_pref.technology.id
        }
        self.technology_prefs.append(technology_pref_dict)

    def add_position_pref(self, position_pref):
        """add_position_pref

         Args:
            skill: SQLAlchemy JobPositionPref object
        Returns:
            None
        """
        position_pref_dict = {
            'id': position_pref.id,
            'type': position_pref.position_type.name,
            'type_id': position_pref.position_type.id,
            'salary_start': position_pref.salary_start,
            'salary_end': position_pref.salary_end
        }
        self.position_prefs.append(position_pref_dict)

    def set_yrs_experience(self, yrs):
        """set_yrs_experience

        Args:
            yrs: number of yrs experience
        Returns:
            None
        """
        self.yrs_experience = yrs