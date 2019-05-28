import os
import logging

from click import ClickException

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists

from process_tracker.logging import console

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
        self.engine = data_store['engine']
        self.session = data_store['session']
        self.meta = data_store['meta']
        self.data_store_type = data_store['data_store_type']
        self.data_store_host = data_store['data_store_host']
        self.data_store_port = data_store['data_store_port']
        self.data_store_name = data_store['data_store_name']

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

        if instance is None:
            if create:
                self.logger.info('creating instance')
                instance = model(**kwargs)
                try:
                    self.session.add(instance)
                except Exception as e:
                    self.logger.error(e)
                try:
                    self.session.commit()
                except Exception as e:
                    self.logger.error(e)
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
        self.logger.info('Attempting to initialize Process Tracker data store.')
        if overwrite:
            self.logger.warn('ALERT - DATA STORE TO BE OVERWRITTEN - ALL DATA WILL BE LOST')
            self.meta.reflect()
            self.meta.drop_all(bind=self.engine)
            self.session.commit()

            version = None
        else:

            self.logger.debug('Obtaining system version, if exists.')
            version = self.session.query(System).filter(System.system_key == 'version').first()

        if version is None:

            self.logger.info('Data store initialization beginning.  Creating data store.')
            self.meta.create_all()

            self.logger.info('Setting up application defaults.')

            self.logger.info('Adding error types...')
            for error_type in preload_error_types:
                self.logger.info('Adding %s' % error_type)
                self.session.add(ErrorType(error_type_name=error_type))
            self.session.commit()

            self.logger.info('Adding extract status types...')
            for extract_status_type in preload_extract_status_types:
                self.logger.info('Adding %s' % extract_status_type)
                self.session.add(ExtractStatus(extract_status_name=extract_status_type))
            self.session.commit()

            self.logger.info('Adding process status types...')
            for process_status_type in preload_process_status_types:
                self.logger.info('Adding %s' % process_status_type)
                self.session.add(ProcessStatus(process_status_name=process_status_type))
            self.session.commit()

            self.logger.info('Adding process types...')
            for process_type in preload_process_types:
                self.logger.info('Adding %s' % process_type)
                self.session.add(ProcessType(process_type_name=process_type))
            self.session.commit()

            self.logger.info('Adding system keys...')
            for system_key, value in preload_system_keys:
                self.logger.info('Adding %s' % system_key)
                self.session.add(System(system_key=system_key, system_value=value))
            self.session.commit()
        else:
            self.logger.error('It appears the system has already been setup.')
            ClickException('It appears the system has already been setup.').show()

        self.logger.debug('Finished the initialization check.')

    def topic_creator(self, topic, name):
        """
        For the command line tool, validate the topic and create the new instance.
        :param topic:
        :param name:
        :return:
        """
        self.logger.info('Attempting to create %s item: %s' % (topic, name))

        if self.topic_validator(topic=topic):
            try:
                if topic == 'actor':
                    item = self.get_or_create_item(model=Actor, actor_name=name)
                    self.logger.info('Actor created: %s' % item.__repr__)
                if topic == 'extract status':
                    item = self.get_or_create_item(model=ExtractStatus, extract_status_name=name)
                    self.logger.info('Extract Status created: %s' % item.__repr__)
                if topic == 'error type':
                    item = self.get_or_create_item(model=ErrorType, error_type_name=name)
                    self.logger.info('Error Type created: %s' % item.__repr__)
                if topic == 'process type':
                    item = self.get_or_create_item(model=ProcessType, process_type_name=name)
                    self.logger.info('Process Type created: %s' % item.__repr__)
                if topic == 'process status':
                    item = self.get_or_create_item(model=ProcessStatus, process_status_name=name)
                    self.logger.info('Process Status created: %s' % item.__repr__)
                if topic == 'source':
                    item = self.get_or_create_item(model=Source, source_name=name)
                    self.logger.info('Source created: %s' % item.__repr__)
                if topic == 'tool':
                    item = self.get_or_create_item(model=Tool, tool_name=name)
                    self.logger.info('Tool created: %s' % item.__repr__)
            finally:
                ClickException('Invalid topic type.').show()

                self.logger.error('Invalid topic type.')
        else:
            ClickException('Invalid topic type.').show()

            self.logger.error('Invalid topic type.')

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

        self.logger.info('Attempting to delete %s item %s' % (topic, name))

        if self.topic_validator(topic=topic):

            if topic == 'actor':
                item_delete = True
                self.session.query(Actor).filter(Actor.actor_name == name).delete()
                self.logger.info('%s %s deleted.' % (topic, name))

            elif topic == 'extract status' and name not in preload_extract_status_types:
                item_delete = True
                self.session.query(ExtractStatus).filter(ExtractStatus.extract_status_name == name).delete()
                self.logger.info('%s %s deleted.' % (topic, name))

            elif topic == 'error type' and name not in preload_error_types:
                item_delete = True
                self.session.query(ErrorType).filter(ErrorType.error_type_name == name).delete()
                self.logger.info('%s %s deleted.' % (topic, name))

            elif topic == 'process type' and name not in preload_process_types:
                item_delete = True
                self.session.query(ProcessType).filter(ProcessType.process_type_name == name).delete()
                self.logger.info('%s %s deleted.' % (topic, name))

            elif topic == 'process status' and name not in preload_process_status_types:
                item_delete = True
                self.session.query(ProcessStatus).filter(ProcessStatus.process_status_name == name).delete()
                self.logger.info('%s %s deleted.' % (topic, name))

            elif topic == 'source':
                item_delete = True
                self.session.query(Source).filter(Source.source_name == name).delete()
                self.logger.info('%s %s deleted.' % (topic, name))

            elif topic == 'tool':
                item_delete = True
                self.session.query(Tool).filter(Tool.tool_name == name).delete()
                self.logger.info('%s %s deleted.' % (topic, name))

            else:
                ClickException('The item could not be deleted because it is a protected record.').show()
                self.logger.error('%s %s could not be deleted because it is  a protected record.' % (topic, name))
        else:
            ClickException('Invalid topic.  Unable to delete instance.').show()
            self.logger.error('%s is an invalid topic.  Unable to delete.' % topic)

        if item_delete:
            self.session.commit()

    def topic_updater(self, topic, initial_name, name):
        """
        For the command line tool, validate that the topic name is not a default value and if not, update it.
        :param topic: name of the SQLAlchemy object
        :type topic: string
        :param initial_name: The name of the object to be updated.
        :type initial_name: string
        :param name: The updated name of the object to be updated.
        :type name: string
        :return:
        """
        if self.topic_validator(topic=topic):
            if topic == 'actor':
                item = self.get_or_create_item(model=Actor, create=False, actor_name=initial_name)
                item.actor_name = name
                self.logger.info('%s %s updated.' % (topic, name))

            elif topic == 'extract status' and initial_name not in preload_extract_status_types:
                item = self.get_or_create_item(model=ExtractStatus, create=False, extract_status_name=initial_name)
                item.extract_status_name = name
                self.logger.info('%s %s updated.' % (topic, name))

            elif topic == 'error type' and initial_name not in preload_error_types:
                item = self.get_or_create_item(model=ErrorType, create=False, error_type_name=initial_name)
                item.error_type_name = name
                self.logger.info('%s %s updated.' % (topic, name))

            elif topic == 'process type' and initial_name not in preload_process_types:
                item = self.get_or_create_item(model=ProcessType, create=False, process_type_name=initial_name)
                item.process_type_name = name
                self.logger.info('%s %s updated.' % (topic, name))

            elif topic == 'process status' and initial_name not in preload_process_status_types:
                item = self.get_or_create_item(model=ProcessStatus, create=False, process_status_name=initial_name)
                item.process_status_name = name
                self.logger.info('%s %s updated.' % (topic, name))

            elif topic == 'source':
                item = self.get_or_create_item(model=Source, create=False, source_name=initial_name)
                item.source_name = name
                self.logger.info('%s %s updated.' % (topic, name))

            elif topic == 'tool':
                item = self.get_or_create_item(model=Tool, create=False, tool_name=initial_name)
                item.tool_name = name
                self.logger.info('%s %s updated.' % (topic, name))

            else:
                ClickException('The item could not be updated because it is a protected record.').show()
                self.logger.error('%s %s could not be updated because it is  a protected record.' % (topic, name))

            self.session.commit()

        else:
            ClickException('Invalid topic.  Unable to update instance.').show()
            self.logger.error('%s is an invalid topic.  Unable to update.' % topic)

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
            self.logger.error('topic type is invalid.  Please use one of the following: %s' % valid_topics.keys())
            return False

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
            data_store['engine'] = engine
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
