
import hashlib

from process_tracker import session


class DataStore:

    def generate_universally_unique_identifier(self, **kwargs):
        """
        Given a set a values, append them into a single string to be converted into a UUID.  While this is designed for
        generic input, as long as the use is identical within instances of an object type it should be universally
        unique (sans the odds for collisions).
        :param kwargs: Name/value pairs of attributes needed to ensure uniqueness for the given thing.
        :return:
        """
        identification_string = ""

        for key, value in kwargs.items():
            identification_string.join("%s || " % value)
            print(identification_string)

        identification_string = identification_string.encode('utf-8')
        identification_hash = hashlib.sha256(identification_string)

        print("Testing hash: %s" % identification_hash)

        return identification_hash.hexdigest()

    @staticmethod
    def get_or_create(model, create=True, **kwargs):
        """
        Testing if an entity instance exists or not.  If does, return entity key.  If not, create entity instance
        and return key.
        :param model: The model entity type.
        :type model: SQLAlchemy Model instance
        :param create: If the entity instance does not exist, do we need to create or not?  Default is to create.
        :type create: Boolean
        :param kwargs: The filter criteria required to find the specific entity instance.
        :return:
        """

        instance = session.query(model).filter_by(**kwargs).first()

        if not instance:

            if create:
                instance = model(**kwargs)
                session.add(instance)
                session.commit()

            else:
                raise Exception('There is no record match in %s' % model.__tablename__)
                exit()

        return instance

    @staticmethod
    def get_latest_tracking_record(model, process):
        """
        For the given process, find the latest tracking record.
        :param model:
        :param process:
        :return:
        """

        instance = session.query(model).filter(model.process_id == process ).order_by(model.run_id.desc()).first()

        return instance
