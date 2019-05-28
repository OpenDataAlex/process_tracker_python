# ProcessTracker CLI Tool
# A set of tools to set up ProcessTracker and maintain lookup topics

import click
import os
import logging

from process_tracker.data_store import DataStore
from process_tracker.logging import console

data_store = DataStore()
logger = logging.getLogger('Process Tracker')
logger.addHandler(console)


@click.group()
def main():
    """
    This script provides methods for initializing ProcessTracker and managing lookup topics (i.e. Actor, Tool, etc.)
    :return:
    """


@main.command()
# @click.option('-o', '--overwrite', default=False, help='Wipe out the current data store and rebuild'
#                                                        ', starting from fresh.')
def setup():
    """
    Initialize ProcessTracker's data store with user provided input.  If already in place, do nothing unless overwrite
    set to True.
    :return:
    """
    click.echo('Attempting to initialize data store...')
    data_store.initialize_data_store()


# @main.command()
# def upgrade():
#     """
#     Upgrade ProcessTracker if data store on previous version.
#     :return:
#     """


@main.command()
@click.option('-t', '--topic', help='The topic being created')
@click.option('-n', '--name', help='The name for the topic.')
def create(topic, name):
    """
    Create an item that is within the valid topics list.
    :param topic: The name of the topic.
    :type topic: string
    :param name: The name of the topic item to be added.
    :type name: string
    """
    click.echo('Attempting to create %s with name %s' % (topic, name))
    data_store.topic_creator(topic=topic, name=name)


@main.command()
@click.option('-t', '--topic', help='The topic being created')
@click.option('-n', '--name', help='The name for the topic.')
def delete(topic, name):
    """
    Delete an item that is within the valid topics list and not a pre-loaded item.
    :param topic: The name of the topic.
    :type topic: string
    :param name: The name of the topic item to be deleted.
    :type name: string
    """
    click.echo('Attempting to delete %s with name %s' % (topic, name))
    data_store.topic_deleter(topic=topic, name=name)


@main.command()
@click.option('-t', '--topic', help='The topic being created')
@click.option('-i', '--initial-name', help='The name that needs to be changed.')
@click.option('-n', '--name', help='The new name for the topic.')
def update(topic, initial_name, name):

    click.echo('Attempting to update %s with name %s to %s' % (topic, initial_name, name))
    data_store.topic_updater(topic=topic, initial_name=initial_name, name=name)
