import logging

from click import ClickException

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import aliased, sessionmaker
from sqlalchemy_utils import database_exists

from process_tracker.utilities.settings import SettingsManager

from process_tracker.models.model_base import Base
from process_tracker.models.actor import Actor
from process_tracker.models.capacity import Cluster, ClusterProcess
from process_tracker.models.extract import ExtractStatus
from process_tracker.models.process import (
    ErrorType,
    Process,
    ProcessDependency,
    ProcessType,
    ProcessStatus,
)
from process_tracker.models.source import Source
from process_tracker.models.system import System
from process_tracker.models.tool import Tool

preload_error_types = ["File Error", "Data Error", "Process Error"]
preload_extract_status_types = [
    "initializing",
    "ready",
    "loading",
    "loaded",
    "archived",
    "deleted",
    "error",
]
preload_process_status_types = ["running", "completed", "failed"]
preload_process_types = ["extract", "load"]
preload_system_keys = [{"version", "0.2.0"}]

supported_data_stores = ["postgresql", "mysql", "oracle", "mssql", "snowflake"]


class DataStore:
    def __init__(self, config_location=None):
        """
        Need to initialize the data store connection when starting to access the data store.
        :param config_location: Location where Process Tracker configuration file is.
        :type config_location: file path
        """
        config = SettingsManager().config
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config["DEFAULT"]["log_level"])

        self.config_location = config_location

        data_store = self.verify_and_connect_to_data_store()
        self.engine = data_store["engine"]
        self.meta = data_store["meta"]
        self.session = data_store["session"]
        self.data_store_type = data_store["data_store_type"]
        self.data_store_host = data_store["data_store_host"]
        self.data_store_port = data_store["data_store_port"]
        self.data_store_name = data_store["data_store_name"]

    def delete_data_store(self):
        """
        Initializes data store deletion, including wiping of all data within.
        :return:
        """

        self.logger.warn("ALERT - DATA STORE TO BE OVERWRITTEN - ALL DATA WILL BE LOST")

        for table in reversed(Base.metadata.sorted_tables):
            try:
                self.logger.info("Table will be deleted: %s" % table)
                table.drop(self.engine)
            except Exception:
                self.logger.error(
                    "Table %s unable to be deleted.  Does it exist?" % table
                )

    def determine_versions(self):
        """
        Find the data store version and the package version and return them.
        :return:
        """

        self.session.query(System.system_value).filter(System.system_key == "version")

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
        self.logger.debug("Attempting to obtain record.")
        instance = self.session.query(model).filter_by(**kwargs).first()

        if instance is None:

            self.logger.debug("Record did not exist.")

            if create:

                self.logger.info("Creating instance.")

                instance = model(**kwargs)

                try:
                    self.logger.debug("Committing instance.")
                    self.session.add(instance)
                except Exception as e:
                    self.logger.error(e)
                try:
                    self.session.commit()
                except Exception as e:
                    self.logger.error(e)
            else:
                raise Exception(
                    "There is no record match in %s ." % model.__tablename__
                )
        else:
            self.logger.info("The instance already exists in %s." % model.__tablename__)

        return instance

    def initialize_data_store(self, overwrite=False):
        """
        Only run if data store does not already exist.  Initializes data store creation and populates system defaults.
        :param overwrite: Only use if data store needs to be wiped and recreated.  Default is False.
        :type overwrite: bool
        """
        self.logger.info("Attempting to initialize Process Tracker data store.")

        if overwrite:
            self.delete_data_store()

        self.logger.info("Data store initialization beginning.  Creating data store.")
        for table in Base.metadata.sorted_tables:
            try:
                self.logger.info("Table will be created: %s" % table)
                table.create(self.engine)
            except Exception:
                self.logger.error("Object %s already exists?" % table)

        self.logger.info("Setting up application defaults.")

        self.logger.info("Adding error types...")
        for error_type in preload_error_types:
            self.logger.info("Adding %s" % error_type)
            self.get_or_create_item(model=ErrorType, error_type_name=error_type)

        self.logger.info("Adding extract status types...")
        for extract_status_type in preload_extract_status_types:
            self.logger.info("Adding %s" % extract_status_type)
            self.get_or_create_item(
                ExtractStatus, extract_status_name=extract_status_type
            )

        self.logger.info("Adding process status types...")
        for process_status_type in preload_process_status_types:
            self.logger.info("Adding %s" % process_status_type)
            self.get_or_create_item(
                model=ProcessStatus, process_status_name=process_status_type
            )

        self.logger.info("Adding process types...")
        for process_type in preload_process_types:
            self.logger.info("Adding %s" % process_type)
            self.get_or_create_item(model=ProcessType, process_type_name=process_type)

        self.logger.info("Adding system keys...")
        for key, value in preload_system_keys:
            self.logger.info("Adding %s" % key)
            self.get_or_create_item(model=System, system_key=key, system_value=value)

        self.session.commit()

        self.logger.debug("Finished the initialization check.")

    def topic_creator(
        self,
        topic,
        name,
        parent=None,
        child=None,
        max_processing=None,
        processing_unit=None,
        max_memory=None,
        memory_unit=None,
        cluster=None,
    ):
        """
        For the command line tool, validate the topic and create the new instance.
        :param topic: The name of the topic.
        :type topic: string
        :param name: The name of the topic item to be added.
        :type name: string
        :param parent: The parent process' name, if creating a process dependency
        :type parent: string
        :param child: The child process' name, if creating a process dependency.For cluster/process relationships, the
                      name of the process.
        :type child: string
        :param max_processing: For performance clusters, the maximum processing ability allocated to the cluster
        :type max_processing: string
        :param max_memory: For performance clusters, the maximum memory allocated to the cluster
        :type max_memory: string
        :param processing_unit: For performance clusters, the unit of processing ability allocated to the cluster
        :type processing_unit: string
        :param memory_unit: For performance clusters, the unit of allocated memory to the cluster
        :type memory_unit: string
        :param cluster: For cluster/process relationships, the name of the cluster.
        :type cluster: string
        :return:
        """
        self.logger.info("Attempting to create %s item: %s" % (topic, name))

        if self.topic_validator(topic=topic):

            if topic == "actor":
                item = self.get_or_create_item(model=Actor, actor_name=name)
                self.logger.info("Actor created: %s" % item.__repr__)

            elif topic == "cluster":
                item = self.get_or_create_item(
                    model=Cluster,
                    cluster_name=name,
                    cluster_max_memory=max_memory,
                    cluster_max_memory_unit=memory_unit,
                    cluster_max_processing=max_processing,
                    cluster_max_processing_unit=processing_unit,
                )
                self.logger.info("Cluster created: %s" % item.__repr__)

            elif topic == "cluster process":
                cluster = self.get_or_create_item(
                    model=Cluster, create=False, cluster_name=cluster
                )
                process = self.get_or_create_item(
                    model=Process, create=False, process_name=child
                )

                item = self.get_or_create_item(
                    model=ClusterProcess,
                    cluster_id=cluster.cluster_id,
                    process_id=process.process_id,
                )

                self.logger.info("Cluster Process created: %s" % item.__repr__)

            elif topic == "extract status":
                item = self.get_or_create_item(
                    model=ExtractStatus, extract_status_name=name
                )
                self.logger.info("Extract Status created: %s" % item.__repr__)

            elif topic == "error type":
                item = self.get_or_create_item(model=ErrorType, error_type_name=name)
                self.logger.info("Error Type created: %s" % item.__repr__)

            elif topic == "process dependency":
                parent_process = self.get_or_create_item(
                    model=Process, process_name=parent, create=False
                )
                child_process = self.get_or_create_item(
                    model=Process, process_name=child, create=False
                )

                item = self.get_or_create_item(
                    model=ProcessDependency,
                    parent_process_id=parent_process.process_id,
                    child_process_id=child_process.process_id,
                )

                self.logger.info("Process Dependency created: %s" % item.__repr__)

            elif topic == "process type":
                item = self.get_or_create_item(
                    model=ProcessType, process_type_name=name
                )
                self.logger.info("Process Type created: %s" % item.__repr__)

            elif topic == "process status":
                item = self.get_or_create_item(
                    model=ProcessStatus, process_status_name=name
                )
                self.logger.info("Process Status created: %s" % item.__repr__)

            elif topic == "source":
                item = self.get_or_create_item(model=Source, source_name=name)
                self.logger.info("Source created: %s" % item.__repr__)

            elif topic == "tool":
                item = self.get_or_create_item(model=Tool, tool_name=name)
                self.logger.info("Tool created: %s" % item.__repr__)

            else:
                ClickException("Invalid topic type.").show()

                self.logger.error("Invalid topic type.")
        else:
            ClickException("Invalid topic type.").show()

            self.logger.error("Invalid topic type.")

        return item

    def topic_deleter(self, topic, name, parent=None, child=None, cluster=None):
        """
        For the command line tool, validate that the topic name is not a default value and if not, delete it.
        :param topic: The SQLAlchemy object type
        :type topic: SQLAlchemy object
        :param name: Name of the item to be deleted.
        :type name: string
        :param parent: The parent process' name, if deleting a process dependency
        :type parent: string
        :param child: The child process' name, if deleting a process dependency.  For cluster/process relationship, the name of the process.
        :type child: string
        :param cluster: For cluster/process relationship, the name of the cluster.
        :return:
        """
        item_delete = False

        self.logger.info("Attempting to delete %s item %s" % (topic, name))

        if self.topic_validator(topic=topic):

            if topic == "actor":
                item_delete = True
                self.session.query(Actor).filter(Actor.actor_name == name).delete()
                self.logger.info("%s %s deleted." % (topic, name))

            elif topic == "cluster":
                item_delete = True
                self.session.query(Cluster).filter(
                    Cluster.cluster_name == name
                ).delete()
                self.logger.info("%s %s deleted." % (topic, name))

            elif topic == "cluster process":
                item_delete = True
                cluster = self.get_or_create_item(
                    model=Cluster, create=False, cluster_name=cluster
                )
                process = self.get_or_create_item(
                    model=Process, create=False, process_name=child
                )

                item = self.get_or_create_item(
                    model=ClusterProcess,
                    create=False,
                    cluster_id=cluster.cluster_id,
                    process_id=process.process_id,
                )

                self.session.delete(item)

                self.logger.info("%s %s - %s deleted." % (topic, cluster, child))

            elif topic == "extract status" and name not in preload_extract_status_types:
                item_delete = True
                self.session.query(ExtractStatus).filter(
                    ExtractStatus.extract_status_name == name
                ).delete()
                self.logger.info("%s %s deleted." % (topic, name))

            elif topic == "error type" and name not in preload_error_types:
                item_delete = True
                self.session.query(ErrorType).filter(
                    ErrorType.error_type_name == name
                ).delete()
                self.logger.info("%s %s deleted." % (topic, name))
            elif topic == "process dependency":
                item_delete = True

                parent_process = self.get_or_create_item(
                    model=Process, process_name=parent, create=False
                )

                child_process = self.get_or_create_item(
                    model=Process, process_name=child, create=False
                )

                item = self.get_or_create_item(
                    model=ProcessDependency,
                    parent_process_id=parent_process.process_id,
                    child_process_id=child_process.process_id,
                )

                self.session.delete(item)

                self.logger.info("%s %s - %s deleted." % (topic, parent, child))

            elif topic == "process type" and name not in preload_process_types:
                item_delete = True
                self.session.query(ProcessType).filter(
                    ProcessType.process_type_name == name
                ).delete()
                self.logger.info("%s %s deleted." % (topic, name))

            elif topic == "process status" and name not in preload_process_status_types:
                item_delete = True
                self.session.query(ProcessStatus).filter(
                    ProcessStatus.process_status_name == name
                ).delete()
                self.logger.info("%s %s deleted." % (topic, name))

            elif topic == "source":
                item_delete = True
                self.session.query(Source).filter(Source.source_name == name).delete()
                self.logger.info("%s %s deleted." % (topic, name))

            elif topic == "tool":
                item_delete = True
                self.session.query(Tool).filter(Tool.tool_name == name).delete()
                self.logger.info("%s %s deleted." % (topic, name))

            else:
                ClickException(
                    "The item could not be deleted because it is a protected record."
                ).show()
                self.logger.error(
                    "%s %s could not be deleted because it is  a protected record."
                    % (topic, name)
                )
        else:
            self.logger.error("%s is an invalid topic.  Unable to delete." % topic)
            raise ClickException("Invalid topic.  Unable to delete instance.")

        if item_delete:
            self.session.commit()

        return "blarg"

    def topic_updater(
        self,
        topic,
        initial_name,
        name,
        max_processing=None,
        processing_unit=None,
        max_memory=None,
        memory_unit=None,
    ):
        """
        For the command line tool, validate that the topic name is not a default value and if not, update it.
        :param topic: name of the SQLAlchemy object
        :type topic: string
        :param initial_name: The name of the object to be updated.
        :type initial_name: string
        :param name: The updated name of the object to be updated.
        :type name: string
        :param max_processing: For performance clusters, the maximum processing ability allocated to the cluster
        :type max_processing: string
        :param max_memory: For performance clusters, the maximum memory allocated to the cluster
        :type max_memory: string
        :param processing_unit: For performance clusters, the unit of processing ability allocated to the cluster
        :type processing_unit: string
        :param memory_unit: For performance clusters, the unit of allocated memory to the cluster
        :type memory_unit: string
        :return:
        """
        if self.topic_validator(topic=topic):
            if topic == "actor":
                item = self.get_or_create_item(
                    model=Actor, create=False, actor_name=initial_name
                )
                item.actor_name = name
                self.logger.info("%s %s updated." % (topic, name))

            elif topic == "cluster":
                item = self.get_or_create_item(
                    model=Cluster, create=False, cluster_name=initial_name
                )

                item.cluster_name = name
                if max_memory is not None:
                    item.cluster_max_memory = max_memory

                if memory_unit is not None:
                    item.cluster_max_memory_unit = memory_unit

                if max_processing is not None:
                    item.cluster_max_processing = max_processing

                if processing_unit is not None:
                    item.cluster_max_processing_unit = processing_unit

                self.logger.info("%s %s updated." % (topic, name))

            elif (
                topic == "extract status"
                and initial_name not in preload_extract_status_types
            ):
                item = self.get_or_create_item(
                    model=ExtractStatus, create=False, extract_status_name=initial_name
                )
                item.extract_status_name = name
                self.logger.info("%s %s updated." % (topic, name))

            elif topic == "error type" and initial_name not in preload_error_types:
                item = self.get_or_create_item(
                    model=ErrorType, create=False, error_type_name=initial_name
                )
                item.error_type_name = name
                self.logger.info("%s %s updated." % (topic, name))

            elif topic == "process type" and initial_name not in preload_process_types:
                item = self.get_or_create_item(
                    model=ProcessType, create=False, process_type_name=initial_name
                )
                item.process_type_name = name
                self.logger.info("%s %s updated." % (topic, name))

            elif (
                topic == "process status"
                and initial_name not in preload_process_status_types
            ):
                item = self.get_or_create_item(
                    model=ProcessStatus, create=False, process_status_name=initial_name
                )
                item.process_status_name = name
                self.logger.info("%s %s updated." % (topic, name))

            elif topic == "source":
                item = self.get_or_create_item(
                    model=Source, create=False, source_name=initial_name
                )
                item.source_name = name
                self.logger.info("%s %s updated." % (topic, name))

            elif topic == "tool":
                item = self.get_or_create_item(
                    model=Tool, create=False, tool_name=initial_name
                )
                item.tool_name = name
                self.logger.info("%s %s updated." % (topic, name))

            else:
                ClickException(
                    "The item could not be updated because it is a protected record."
                ).show()
                self.logger.error(
                    "%s %s could not be updated because it is  a protected record."
                    % (topic, name)
                )

            self.session.commit()

        else:
            ClickException("Invalid topic.  Unable to update instance.").show()
            self.logger.error("%s is an invalid topic.  Unable to update." % topic)

    def topic_validator(self, topic):
        """
        For the command line tool, determine if the topic is valid for the cli to work on.
        :param topic:
        :return: boolean
        """

        topic = topic.lower()

        self.logger.info("Validating if %s can be managed via CLI..." % topic)

        # Only data store topics that should be allowed to be created from the command line tool.
        valid_topics = [
            "actor",
            "cluster",
            "cluster process",
            "error type",
            "extract status",
            "process dependency",
            "process status",
            "process type",
            "source",
            "tool",
        ]

        if topic in valid_topics:
            self.logger.info("Topic validated.")
            return True
        else:
            self.logger.info("Topic invalidated.  Please try again.")
            self.logger.error(
                "topic type is invalid.  Please use one of the following: %s"
                % valid_topics.keys()
            )
            return False

    def verify_and_connect_to_data_store(self):
        """
        Based on environment variables, create the data store connection engine.
        :return:
        """
        self.logger.info("Obtaining application configuration.")
        config = SettingsManager(config_location=self.config_location).config

        data_store_type = config["DEFAULT"]["data_store_type"]
        data_store_username = config["DEFAULT"]["data_store_username"]
        data_store_password = config["DEFAULT"]["data_store_password"]
        data_store_host = config["DEFAULT"]["data_store_host"]
        data_store_port = config["DEFAULT"]["data_store_port"]
        data_store_name = config["DEFAULT"]["data_store_name"]

        errors = []

        if data_store_type is None or data_store_type == "None":
            errors.append(Exception("Data store type is not set."))

        if data_store_username is None or data_store_username == "None":
            errors.append(Exception("Data store username is not set."))

        if data_store_password is None or data_store_password == "None":
            errors.append(Exception("Data store password is not set"))

        if data_store_host is None or data_store_host == "None":
            errors.append(Exception("Data store host is not set"))

        if data_store_port is None or data_store_port == "None":
            errors.append(Exception("Data store port is not set"))

        if data_store_name is None or data_store_name == "None":
            errors.append(Exception("Data store name is not set"))

        if errors:

            errors.append(
                Exception(
                    "Data store has not been properly configured.  Please read how to set up the "
                    "Process Tracking data store by going to: https://process-tracker.readthedocs.io/en/latest/"
                )
            )

            raise Exception(errors)

        if data_store_type in supported_data_stores:

            self.logger.info("Data store is supported.")
            self.logger.info("Data store is %s" % data_store_type)

            if (
                data_store_type == "postgresql"
                or data_store_type == "oracle"
                or data_store_type == "snowflake"
            ):

                engine = create_engine(
                    data_store_type
                    + "://"
                    + data_store_username
                    + ":"
                    + data_store_password
                    + "@"
                    + data_store_host
                    + ":"
                    + data_store_port
                    + "/"
                    + data_store_name
                )

            elif data_store_type == "mysql":

                engine = create_engine(
                    "mysql+pymysql://"
                    + data_store_username
                    + ":"
                    + data_store_password
                    + "@"
                    + data_store_host
                    + ":"
                    + data_store_port
                    + "/"
                    + data_store_name
                )
            elif data_store_type == "mssql":

                engine = create_engine(
                    "mssql+pymssql://"
                    + data_store_username
                    + ":"
                    + data_store_password
                    + "@"
                    + data_store_host
                    + ":"
                    + data_store_port
                    + "/"
                    + data_store_name
                )

            else:
                self.logger.error("Data store type valid but not configured.")
                raise Exception("Data store type valid but not configured.")

            self.logger.info(
                "Attempting to connect to data store %s, found at %s:%s"
                % (data_store_name, data_store_host, data_store_port)
            )

            if database_exists(engine.url):

                self.logger.info("Data store exists.  Continuing to work.")

            else:

                self.logger.error(
                    "Data store does not exist.  Please create and try again."
                )
                raise Exception(
                    "Data store does not exist.  Please create and try again."
                )

            session = sessionmaker(bind=engine)

            session = session(expire_on_commit=False)

            if data_store_type == "postgresql":
                session.execute("SET search_path TO %s" % data_store_name)
            elif data_store_type == "mysql":
                session.execute("USE %s" % data_store_name)

            meta = MetaData(schema="process_tracking")

            data_store = dict()
            data_store["engine"] = engine
            data_store["meta"] = meta
            data_store["session"] = session
            data_store["data_store_type"] = data_store_type
            data_store["data_store_host"] = data_store_host
            data_store["data_store_port"] = data_store_port
            data_store["data_store_name"] = data_store_name
            data_store["data_store_username"] = data_store_username
            data_store["data_store_password"] = data_store_password

            return data_store
        else:
            raise Exception(
                "Invalid data store type provided.  Please use: "
                + ", ".join(supported_data_stores)
            )
