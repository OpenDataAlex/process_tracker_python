import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)

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

            log.info("Attempting to connect to datastore %s, found at %s:%s" % (data_store_name
                                                                                , data_store_host
                                                                                , data_store_port))

    elif data_store_type in nonrelational_stores:
        Session = ''

    Session = sessionmaker(bind=engine)

    session = Session(expire_on_commit=False)
    session.execute("SET search_path TO %s" % data_store_name)

else:
    raise Exception('Invalid data store type provided.  Please use: ' + ", ".join(supported_data_stores))
    exit()