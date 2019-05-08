
from process_tracker import session
from models.process import ProcessTracking


class DataStore:

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
    def get_latest_tracking_record(process):
        """
        For the given process, find the latest tracking record.
        :param process: The process' process_id.
        :type process: integer
        :return:
        """

        instance = session.query(ProcessTracking)\
            .filter(ProcessTracking.process_id == process)\
            .order_by(ProcessTracking.process_run_id.desc())\
            .first()

        if instance is None:
            return False

        return instance
