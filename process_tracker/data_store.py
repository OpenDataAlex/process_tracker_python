import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DataStore:

    def __init__(self):
        """
        Need to initialize the data store connection when starting to access the data store.
        """
        self.logger = logging.getLogger(__name__)

        data_store = self.verify_and_connect_to_data_store()
        self.session = data_store['session']
        self.data_store_type = data_store['data_store_type']
        self.data_store_host = data_store['data_store_host']
        self.data_store_port = data_store['data_store_port']
        self.data_store_name = data_store['data_store_name']

    def get_or_create(self, model, create=True, **kwargs):
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

        instance = self.session.query(model).filter_by(**kwargs).first()

        if not instance:

            if create:
                instance = model(**kwargs)
                self.session.add(instance)
                self.session.commit()

            else:
                raise Exception('There is no record match in %s .' % model.__tablename__)

        return instance

    def verify_and_connect_to_data_store(self):
        """
        Based on environment variables, create the data store connection engine.
        :return:
        """

        data_store_type = os.environ.get('process_tracking_data_store_type')
        data_store_username = os.environ.get('process_tracking_data_store_username')
        data_store_password = os.environ.get('process_tracking_data_store_password')
        data_store_host = os.environ.get('process_tracking_data_store_host')
        data_store_port = os.environ.get('process_tracking_data_store_port')
        data_store_name = os.environ.get('process_tracking_data_store_name')

        data_store_error_flag = False

        if data_store_type is None:
            raise Exception('Data store type is not set.')
            data_store_error_flag = True

        if data_store_username is None:
            raise Exception('Data store username is not set.')
            data_store_error_flag = True

        if data_store_password is None:
            raise Exception('Data store password is not set')
            data_store_error_flag = True

        if data_store_host is None:
            raise Exception('Data store host is not set')
            data_store_error_flag = True

        if data_store_port is None:
            raise Exception('Data store port is not set')
            data_store_error_flag = True

        if data_store_name is None:
            raise Exception('Data store name is not set')
            data_store_error_flag = True

        if data_store_error_flag:
            raise Exception('Data store has not been properly configured.  Please read how to set up the Process '
                            'Tracking data store by going to: <insert read the docs url here>')

        relational_stores = ['postgresql']
        nonrelational_stores = []

        supported_data_stores = relational_stores + nonrelational_stores

        if data_store_type in supported_data_stores:

            if data_store_type in relational_stores:
                if data_store_type == 'postgresql':
                    engine = create_engine(data_store_type + '://' + data_store_username + ':' + data_store_password
                                           + '@' + data_store_host + '/' + data_store_name)

                    self.logger.info("Attempting to connect to datastore %s, found at %s:%s" % (data_store_name
                                                                                        , data_store_host
                                                                                        , data_store_port))

                Session = sessionmaker(bind=engine)

                session = Session(expire_on_commit=False)
                session.execute("SET search_path TO %s" % data_store_name)

            elif data_store_type in nonrelational_stores:
                Session = ''

            data_store = dict()
            data_store['session'] = session
            data_store['data_store_type'] = data_store_type
            data_store['data_store_host'] = data_store_host
            data_store['data_store_port'] = data_store_port
            data_store['data_store_name'] = data_store_name
            data_store['data_store_username'] = data_store_username
            data_store['data_store_password'] = data_store_password

            return data_store
        else:
            raise Exception('Invalid data store type provided.  Please use: ' + ", ".join(supported_data_stores))
            exit()