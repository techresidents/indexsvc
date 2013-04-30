from datetime import datetime

from trsvcscore.db.models import User, DeveloperProfile, Skill, \
    JobLocationPref, JobTechnologyPref, JobPositionTypePref

from document import ESDocument


class ESUserDocument(ESDocument):
    """ ESUserDocument is responsible for generating an ElasticSearch user document"""

    def __init__(self, db_session_factory):
        super(ESUserDocument, self).__init__(db_session_factory)

    def generate(self, key):
        """Generates a JSON dict that can be indexed by ES

        Args:
            key: user db key
        Returns:
            JSON document that is consumable by ESClient
        """
        try:
            # lookup user and associated data
            db_session = self.db_session_factory()
            user = db_session.query(User).\
                filter(User.id==key).\
                one()
            developer_profile = db_session.query(DeveloperProfile).\
                filter(DeveloperProfile.user_id==key).\
                one()
            skills = db_session.query(Skill).\
                filter(Skill.user_id==user.id).\
                all()
            location_prefs = db_session.query(JobLocationPref).\
                filter(JobLocationPref.user_id==user.id).\
                all()
            technology_prefs = db_session.query(JobTechnologyPref).\
                filter(JobTechnologyPref.user_id==user.id).\
                all()
            position_prefs = db_session.query(JobPositionTypePref).\
                filter(JobPositionTypePref.user_id==user.id).\
                all()

            # generate ES document JSON
            es_user = ESUser(user.id, user.date_joined)
            for skill in skills:
                es_user.add_skill(skill)
            for location_pref in location_prefs:
                es_user.add_location_pref(location_pref)
            for technology_pref in technology_prefs:
                es_user.add_technology_pref(technology_pref)
            for position_pref in position_prefs:
                es_user.add_position_pref(position_pref)
            if developer_profile.developer_since:
                current_year = datetime.now().year
                yrs_experience = current_year - developer_profile.developer_since.year
                es_user.set_yrs_experience(yrs_experience)

            return es_user.to_json()

        except Exception as e:
            self.log.exception(e)
            if db_session:
                db_session.rollback()
        finally:
            if db_session:
                db_session.close()



class ESUser(object):
    """ESUser holds all of the data needed to generate the ESUserDocument JSON
    """
    def __init__(self, id, date_joined):
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
        skill_dict = {'id': skill.id, 'name': skill.technology.name}
        self.skills.append(skill_dict)

    def add_location_pref(self, location_pref):
        location_pref_dict = {'id': location_pref.location.id, 'city': location_pref.location.city}
        self.location_prefs.append(location_pref_dict)

    def add_technology_pref(self, technology_pref):
        technology_pref_dict = {'id': technology_pref.technology.id, 'name': technology_pref.technology.name}
        self.technology_prefs.append(technology_pref_dict)

    def add_position_pref(self, position_pref):
        position_pref_dict = {'id': position_pref.position_type.id, 'type': position_pref.position_type.name}
        self.position_prefs.append(position_pref_dict)

    def set_yrs_experience(self, yrs):
        self.yrs_experience = yrs
