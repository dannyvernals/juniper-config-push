"""
Script: config_push.py
About: Push configuration to a multiple Juniper devices
By: Danny Vernals 
"""

import sys
import argparse
import getpass
import os
import logging
from logging.handlers import RotatingFileHandler
from jnpr.junos.exception import (ConnectTimeoutError, ConnectRefusedError,
                                  ConnectAuthError, ConnectUnknownHostError, ConfigLoadError)
from jnpr.junos import Device
from jnpr.junos.utils.config import Config


def logging_func(directory):
    """Instantiate Logging."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not os.path.exists(directory + '/logs'):
        os.makedirs(directory + '/logs')
    handler_file = RotatingFileHandler(directory + '/logs/config_push.log',
                                       maxBytes=100000, backupCount=10
                                       )
    handler_file.setLevel(logging.INFO)
    handler_stout = logging.StreamHandler(sys.stdout)
    handler_stout.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler_file.setFormatter(formatter)
    logger.addHandler(handler_file)
    logger.addHandler(handler_stout)
    return logger


def cli_grab():
    """take stuff from cli, output it in a dict"""
    parser = argparse.ArgumentParser(description='Push config to multiple Juniper devices')
    parser.add_argument("routers_file", help="File that contains a list of routers to update")
    parser.add_argument("config_file", help="File that contains config you want to push")
    parser.add_argument("config_format", help="Format of the config: xml, text or set")
    parser.add_argument("-k", "--key", help="location of SSH key to authenticate with")
    parser.add_argument("-t", action='store_true', help="Test run.  Apply the config, run a "
                                                        "'show | compare' then rollback.  "
                                                        "The change is not committed.")
    parser.add_argument("-c", action='store_true', help="Execute a 'commit full'")
    parser.add_argument("-f", action='store_true', help="Force: Ignore any commit errors'")
    parser.add_argument('-d', action='store_true', help="If the -d flag is set, 'config_file' is a"
                                                        " directory. Here device specific configs "
                                                        "are stored. Is it used to push different "
                                                        "configs to each router. Configs must be "
                                                        "named ${Device}.conf")
    args = vars(parser.parse_args())
    args['uid'] = input('username: ')
    args['pwd'] = getpass.getpass('password (blank if using SSH keys): ')
    return args


def router_connect(router, uid, pwd):
    """"attempt to connect to a router with the passed credentials"""
    try:
        dev = Device(host=router, user=uid, password=pwd)
        dev.open()
        # dev.timeout = 120  # Timeout for all RPCs
    except (ConnectTimeoutError, ConnectRefusedError, ConnectAuthError,
            ConnectUnknownHostError, ConfigLoadError) as err:
        LOGGER.info(err)
        LOGGER.info("Skipping {} and moving onto the next router in the list".format(router))
        return None
    LOGGER.info("Connected to '{}'. Device hostname: '{}'. Software version: '{}'\n".format(
        router,
        dev.facts['hostname'],
        dev.facts['version']
        )
                )
    return dev


def instantiate_config_object(dev, config_format, config_text):
    """Instantiate an object from Config() and attempt to apply the configuration changes"""
    config_dev = Config(dev)
    try:
        config_dev.lock()
        config_dev.load(config_text, format=config_format)
    except ConfigLoadError as err:
        LOGGER.info(err)
        print("Errors detected, rolling back the change and disconnecting\n")
        config_dev.rollback()
        config_dev.unlock()
        dev.close()
        return None
    return config_dev


def commit_config(config_dev, commit_full):
    """Attempt to commit the loaded configuration"""
    if config_dev.commit_check():
        LOGGER.info("Commit check passed, commiting changes\n...")
        if commit_full:
            LOGGER.info("Performing 'commit full', this could take some time!")
            config_dev.commit(full=True, timeout=120)
            LOGGER.info("Commit full complete")
        else:
            config_dev.commit()
            LOGGER.info("Commit complete")
    else:
        LOGGER.info("Commit failed, rolling back")
        config_dev.rollback()


def upload_config(args):
    """push config to multiple devices"""
    config_file = args['config_file']
    multi_conf = args['d']
    test_run = args['t']
    commit_full = args['c']
    force = args['f']
    with open(args['routers_file']) as routers_raw:
        routers_list = routers_raw.read().splitlines()
    for router in routers_list:
        if multi_conf:
            with open(config_file + '/' + router + ".conf") as config_raw:
                config_text = config_raw.read()
        else:
            with open(config_file) as config_raw:
                config_text = config_raw.read()
        print("=" * 110)
        LOGGER.info("Pushing {} to {}".format(config_file, router))
        device = router_connect(router, args['uid'], args['pwd'])
        if device is None:
            continue
        print("-" * 110)
        config_dev = instantiate_config_object(device, args['config_format'], config_text)
        if config_dev is None and not multi_conf and not force:
            LOGGER.info("As an error was detected in config application.\n"
                        "The assumption is this will happen on multiple devices so exiting.\n"
                        "To change this behaviour use '-f'.")
            sys.exit()
        elif config_dev is None:
            continue
        config_diff = config_dev.diff()
        LOGGER.info("Config diff: {}".format(config_diff))
        print("-" * 110)
        if test_run:
            config_dev.rollback()
            LOGGER.info("Test Run only, rolling back the change")
        elif config_diff is None:
            config_dev.rollback()
            LOGGER.info("Diff is 'None' so cancelling commit")
        else:
            commit_config(config_dev, commit_full)
        print("-" * 110)
        config_dev.unlock()
        device.close()
        LOGGER.info("Disconnected from {}\n".format(router))


if __name__ == '__main__':
    DIRECTORY = os.path.dirname(os.path.realpath(__file__))
    LOGGER = logging_func(DIRECTORY)
    ARGS = cli_grab()
    upload_config(ARGS)
