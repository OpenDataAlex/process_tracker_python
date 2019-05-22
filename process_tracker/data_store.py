import os
import logging

from click import ClickException

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists

from process_tracker.models.actor import Actor
from process_tracker.models.extract import ExtractStatus
from process_tracker.models.process import ErrorType, ProcessType, ProcessStatus
from process_tracker.models.source import Source
from process_tracker.models.system import System
from process_tracker.models.tool import Tool

preload_error_types = ['File Error', 'Data Error', 'Process Error']
preload_extract_status_types = ['initializing', 'ready', 'loading', 'loaded', 'archived', 'deleted', 'error']
preload_process_status_types = ['running', 'completed', 'failed']
preload_process_types = ['extract', 'load']
preload_system_keys = [{'key': 'version', 'value': '0.1.0'}]


class DataStore:

    def __init__(self):
        """
        Need to initialize the data store connection when starting to access the data store.
        """
        self.logger = logging.getLogger(__name__)

        data_store = self.verify_and_connect_to_data_store()
        self.session = data_store['session']
        self.meta = data_store['meta']
        self.data_store_type = data_store['data_store_type']
        self.data_store_host = data_store['data_store_host']
        self.data_store_port = data_store['data_store_port']
        self.data_store_name = data_store['data_store_name']

    def get_item(self, topic, name):
        """
        For the command line tool, find the given item and return it.  Intentionally not as flexible as
        get_or_create_item.
        :param topic:
        :param name:
        :return:
        """
        if topic == Actor:
            item = self.get_or_create_item(model=topic, create=False, actor_name=name)
        elif topic == ExtractStatus and name not in preload_extract_status_types:
            item = self.get_or_create_item(model=topic, create=False, extract_status_name=name)
        elif topic == ErrorType and name not in preload_error_types:
            item = self.get_or_create_item(model=topic, create=False, error_type_name=name)
        elif topic == ProcessType and name not in preload_process_types:
            item = self.get_or_create_item(model=topic, create=False, process_type_name=name)
        elif topic == ProcessStatus and name not in preload_process_status_types:
            item = self.get_or_create_item(model=topic, create=False, process_status_name=name)
        elif topic == Source:
            item = self.get_or_create_item(model=topic, create=False, source_name=name)
        elif topic == Tool:
            item = self.get_or_create_item(model=topic, create=False, tool_name=name)
        else:
            ClickException('The item is a protected record.').show()

        return item

    def get_or_create_item(self, model, create=True, **kwargs):
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
        else:
            self.logger.info('The instance already exists in %s.' % model.__tablename__)

        return instance

    def initialize_data_store(self, overwrite=False):
        """
        Only run if data store does not already exist.  Initializes data store creation and populates system defaults.
        :param overwrite: Only use if data store needs to be wiped and recreated.  Default is False.
        :type overwrite: bool
        """

        if overwrite:
            self.logger.info('ALERT - DATA STORE TO BE OVERWRITTEN - ALL DATA WILL BE LOST')
            self.meta.reflect()
            self.meta.drop_all()

        version = self.session.query(System).filter(System.session_key == 'version').first()

        if version is None:

            self.logger.info('Data store initialization beginning.  Creating data store.')
            self.meta.create_all()

            self.logger.info('Setting up application defaults.')

            self.logger.info('Adding error types...')
            for error_type in preload_error_types:
                self.session.add(ErrorType(error_type_name=error_type))
            self.session.commit()

            self.logger.info('Adding extract status types...')
            for extract_status_type in preload_extract_status_types:
                self.session.add(ExtractStatus(extract_status_name=extract_status_type))
            self.session.commit()

            self.logger.info('Adding process status types...')
            for process_status_type in preload_process_status_types:
                self.session.add(ProcessStatus(process_status_name=process_status_type))
            self.session.commit()

            self.logger.info('Adding process types...')
            for process_type in preload_process_types:
                self.session.add(ProcessType(process_type_name=process_type))
            self.session.commit()

            self.logger.info('Adding system keys...')
            for system_key, value in preload_system_keys:
                self.session.add(System(system_key=system_key, system_value=value))
            self.session.commit()
        else:
            self.logger.info('It appears the system has already been initialized.')

    def topic_creator(self, topic, name):
        """
        For the command line tool, validate the topic and create the new instance.
        :param topic:
        :param name:
        :return:
        """

        if self.topic_validator(topic=topic):
            if topic == 'actor':
                item = self.get_or_create_item(model=Actor, actor_name=name)
            elif topic == 'extract status':
                item = self.get_or_create_item(model=ExtractStatus, extract_status_name=name)
            elif topic == 'error type':
                item = self.get_or_create_item(model=ErrorType, error_type_name=name)
            elif topic == 'process type':
                item = self.get_or_create_item(model=ProcessType, process_type_name=name)
            elif topic == 'process status':
                item = self.get_or_create_item(model=ProcessStatus, process_status_name=name)
            elif topic == 'source':
                item = self.get_or_create_item(model=Source, source_name=name)
            elif topic == 'tool':
                item = self.get_or_create_item(model=Tool, tool_name=name)
            else:
                ClickException('Invalid topic type.').show()
        else:
            ClickException('Invalid topic type.').show()

        return item

    def topic_deleter(self, topic, name):
        """
        For the command line tool, validate that the topic name is not a default value and if not, delete it.
        :param topic: The SQLAlchemy object type
        :type topic: SQLAlchemy object
        :param name: Name of the item to be deleted.
        :type name: string
        :return:
        """
        item_delete = False

        if self.topic_validator(topic=topic):
            if topic == 'actor':
                item_delete = True
                self.session.query(Actor).filter(Actor.actor_name == name).delete()

            elif topic == 'extract status' and name not in preload_extract_status_types:
                item_delete = True
                self.session.query(ExtractStatus).filter(ExtractStatus.extract_status_name == name).delete()

            elif topic == 'error type' and name not in preload_error_types:
                item_delete = True
                self.session.query(ErrorType).filter(ErrorType.error_type_name == name).delete()

            elif topic == 'process type' and name not in preload_process_types:
                item_delete = True
                self.session.query(ProcessType).filter(ProcessType.process_type_name == name).delete()

            elif topic == 'process status' and name not in preload_process_status_types:
                item_delete = True
                self.session.query(ProcessStatus).filter(ProcessStatus.process_status_name == name).delete()

            elif topic == 'source':
                item_delete = True
                self.session.query(Source).filter(Source.source_name == name).delete()

            elif topic == 'tool':
                item_delete = True
                self.session.query(Tool).filter(Tool.tool_name == name).delete()

            else:
                ClickException('The item could not be deleted because it is a protected record.').show()
        else:
            ClickException('Invalid topic.  Unable to delete instance.').show()

        if item_delete:
            self.session.commit()

    @staticmethod
    def topic_updater(topic, item, name):
        """
        For the command line tool, validate that the topic name is not a default value and if not, update it.
        :param topic: The SQLAlchemy object type
        :type topic: SQLAlchemy object
        :param item: The SQLALchemy record to be updated.
        :type item: SQLAlchemy record
        :param name: The name of the item to be deleted.
        :type name: str
        :return:
        """
        if topic == Actor:
            item.actor_name = name
        elif topic == ExtractStatus and item.extract_status_name not in preload_extract_status_types:
            item.extract_status_name = name
        elif topic == ErrorType and item.error_type_name not in preload_error_types:
            item.error_type_name = name
        elif topic == ProcessType and item.process_type_name not in preload_process_types:
            item.process_type_name = name
        elif topic == ProcessStatus and item.process_status_name not in preload_process_status_types:
            item.process_status_name = name
        elif topic == Source:
            item.source_name = name
        elif topic == Tool:
            item.tool_name = name
        else:
            raise Exception('The item could not be updated because it is a protected record.')

        item_session = Session.object_session(item)
        item_session.commit()

    def topic_validator(self, topic):
        """
        For the command line tool, determine if the topic is valid for the cli to work on.
        :param topic:
        :return: boolean
        """

        topic = topic.lower()

        self.logger.info('Validating if %s can be managed via CLI...' % topic)

        # Only data store topics that should be allowed to be created from the command line tool.
        valid_topics = ['actor', 'error type', 'extract status', 'process status', 'process type', 'source', 'tool']

        if topic in valid_topics:
            self.logger.info('Topic validated.')
            return True
        else:
            self.logger.info('Topic invalidated.  Please try again.')
            return False
            self.logger.error('topic type is invalid.  Please use one of the following: %s' % valid_topics.keys())

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

        errors = []

        if data_store_type is None:
            errors.append(Exception('Data store type is not set.'))

        if data_store_username is None:
            errors.append(Exception('Data store username is not set.'))

        if data_store_password is None:
            errors.append(Exception('Data store password is not set'))

        if data_store_host is None:
            errors.append(Exception('Data store host is not set'))

        if data_store_port is None:
            errors.append(Exception('Data store port is not set'))

        if data_store_name is None:
            errors.append(Exception('Data store name is not set'))

        if errors:

            errors.append(Exception('Data store has not been properly configured.  Please read how to set up the '
                                    'Process Tracking data store by going to: <insert read the docs url here>'))

            raise Exception(errors)

        relational_stores = ['postgresql']
        nonrelational_stores = []

        supported_data_stores = relational_stores + nonrelational_stores

        if data_store_type in supported_data_stores:

            if data_store_type in relational_stores:
                if data_store_type == 'postgresql':
                    engine = create_engine(data_store_type + '://' + data_store_username + ':' + data_store_password
                                           + '@' + data_store_host + '/' + data_store_name)

                    self.logger.info("Attempting to connect to data store %s, found at %s:%s" % (data_store_name
                                                                                        , data_store_host
                                                                                        , data_store_port))
                if database_exists(engine.url):
                    self.logger.info("Data store exists.  Continuing to work.")

                Session = sessionmaker(bind=engine)

                session = Session(expire_on_commit=False)
                session.execute("SET search_path TO %s" % data_store_name)

                meta = MetaData(engine)

            elif data_store_type in nonrelational_stores:
                Session = ''
                session = ''
                meta = ''

            data_store = dict()
            data_store['session'] = session
            data_store['meta'] = meta
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