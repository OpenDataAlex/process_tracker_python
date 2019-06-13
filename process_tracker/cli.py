# ProcessTracker CLI Tool
# A set of tools to set up ProcessTracker and maintain lookup topics

import click
import logging

from process_tracker.data_store import DataStore
from process_tracker.utilities.logging import console

data_store = DataStore()
logger = logging.getLogger("Process Tracker")
logger.addHandler(console)


@click.group()
def main():
    """
    This script provides methods for initializing ProcessTracker and managing lookup topics (i.e. Actor, Tool, etc.)
    :return:
    """


@main.command()
@click.option(
    "-o",
    "--overwrite",
    default=False,
    help="Wipe out the current data store and rebuild" ", starting from fresh.",
)
def setup(overwrite=False):
    """
    Initialize ProcessTracker's data store with user provided input.  If already in place, do nothing unless overwrite
    set to True.
    :return:
    """
    click.echo("Attempting to initialize data store...")
    data_store.initialize_data_store(overwrite=overwrite)


@main.command()
def upgrade():
    """
    Upgrade ProcessTracker if data store on previous version.
    :return:
    """
    click.echo("Verifying version installed on data store vs package...")
    data_store.determine_versions()


@main.command()
@click.option("-t", "--topic", help="The topic being created")
@click.option("-n", "--name", help="The name for the topic.")
@click.option(
    "-p", "--parent", help="The parent process' name, if creating a process dependency"
)
@click.option(
    "-c",
    "--child",
    help="The child process' name, if creating a process dependency.  For cluster/process relationships, the name of "
    "the process.",
)
@click.option(
    "--max-processing",
    help="For clusters, the max processing ability allocated to the cluster",
)
@click.option(
    "--max-memory", help="For clusters, the max memory allocated to the cluster"
)
@click.option(
    "--processing-unit",
    help="For clusters, the unit of processing ability (Ghz, CPU, DPU, etc.",
)
@click.option(
    "--memory-unit", help="For clusters, the unit of allocated memory (MB, GB, etc."
)
@click.option(
    "--cluster", help="For cluster/process relationships, the name of the cluster"
)
def create(
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
    Create an item that is within the valid topics list.
    :param topic: The name of the topic.
    :type topic: string
    :param name: The name of the topic item to be added.
    :type name: string
    :param parent: The parent process' name, if creating a process dependency
    :type parent: string
    :param child: The child process' name, if creating a process dependency.  For cluster/process relationships, the
                  name of the process.
    :type child: string
    :param max_processing: For performance clusters, the maximum processing ability allocated to the cluster
    :type max_processing: integer
    :param max_memory: For performance clusters, the maximum memory allocated to the cluster
    :type max_memory: integer
    :param processing_unit: For performance clusters, the unit of processing ability allocated to the cluster
    :type processing_unit: string
    :param memory_unit: For performance clusters, the unit of allocated memory to the cluster
    :type memory_unit: string
    :param cluster: For cluster/process relationships, the name of the cluster.
    :type cluster: string
    """
    click.echo("Attempting to create %s with name %s" % (topic, name))
    data_store.topic_creator(
        topic=topic,
        name=name,
        parent=parent,
        child=child,
        max_processing=max_processing,
        max_memory=max_memory,
        processing_unit=processing_unit,
        memory_unit=memory_unit,
        cluster=cluster,
    )


@main.command()
@click.option("-t", "--topic", help="The topic being created")
@click.option("-n", "--name", help="The name for the topic.")
@click.option(
    "-p", "--parent", help="The parent process' name, if deleting a process dependency"
)
@click.option(
    "-c", "--child", help="The child process' name, if deleting a process dependency"
)
@click.option(
    "--cluster", help="For cluster/process relationships, the name of the cluster"
)
def delete(topic, name, parent=None, child=None, cluster=None):
    """
    Delete an item that is within the valid topics list and not a pre-loaded item.
    :param topic: The name of the topic.
    :type topic: string
    :param name: The name of the topic item to be deleted.
    :type name: string
    :param parent: The parent process' name, if deleting a process dependency
    :type parent: string
    :param child: The child process' name, if deleting a process dependency.  For cluster/process relationships, the
                  name of the process.
    :type child: string
    :param cluster: For cluster/process relationships, the name of the cluster.
    :type cluster: string
    """
    click.echo("Attempting to delete %s with name %s" % (topic, name))
    data_store.topic_deleter(
        topic=topic, name=name, parent=parent, child=child, cluster=cluster
    )


@main.command()
@click.option("-t", "--topic", help="The topic being created")
@click.option("-i", "--initial-name", help="The name that needs to be changed.")
@click.option("-n", "--name", help="The new name for the topic.")
@click.option(
    "--max-processing",
    help="For clusters, the max processing ability allocated to the cluster",
)
@click.option(
    "--max-memory", help="For clusters, the max memory allocated to the cluster"
)
@click.option(
    "--processing-unit",
    help="For clusters, the unit of processing ability (Ghz, CPU, DPU, etc.",
)
@click.option(
    "--memory-unit", help="For clusters, the unit of allocated memory (MB, GB, etc."
)
def update(
    topic,
    initial_name,
    name,
    max_processing=None,
    max_memory=None,
    processing_unit=None,
    memory_unit=None,
):
    """
    Update an item that is within the valid topics list and not a pre-loaded item.
    :param topic: The name of the topic.
    :type topic: string
    :param initial_name: The revised name of the topic item to be updated.
    :type initial_name: string
    :param name: The original name of the topic item to be updated.
    :type name: string
    :param max_processing: For performance clusters, the maximum processing ability allocated to the cluster
    :type max_processing: string
    :param max_memory: For performance clusters, the maximum memory allocated to the cluster
    :type max_memory: string
    :param processing_unit: For performance clusters, the unit of processing ability allocated to the cluster
    :type processing_unit: string
    :param memory_unit: For performance clusters, the unit of allocated memory to the cluster
    :type memory_unit: string
    """
    click.echo(
        "Attempting to update %s with name %s to %s" % (topic, initial_name, name)
    )
    data_store.topic_updater(
        topic=topic,
        initial_name=initial_name,
        name=name,
        max_processing=max_processing,
        max_memory=max_memory,
        processing_unit=processing_unit,
        memory_unit=memory_unit,
    )
