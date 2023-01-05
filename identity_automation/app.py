#!/usr/bin/python

# This script searches for python files in the 
#

import os
import importlib
import logging
import platform
from datetime import datetime, timedelta
from identity_automation.common import constants
from chromedriver_py import binary_path

os_name = platform.system()

# Trigger Job (initiated from __main__)
def run():
    start_time = datetime.now() # Start the clock

    
    config_directories()

    # configure the logging configuratioin perameters (pulled from contants file)
    config_logging()

    # jobs are grouped into collections (folders).  The collections are ran in the the order of the list provided to the first for loop
    #for job_collection in ['edsembli_jobs', 'active_directory_jobs']:
    #for job_collection in ['atrieve_jobs', 'destiny_jobs']:
    for job_collection in ['edsembli_jobs', 'atrieve_jobs', 'active_directory_jobs', 'destiny_jobs']:
        # The collection is ran in alphabetical order.  The order could be controlled through a file name prefix if required
        for job in list_jobs(job_collection):
            logging.info('Running Job: ' + job_collection + '.' + job)
            job = importlib.import_module('identity_automation.' + job_collection +'.' + job) # load the module and get it's handle
            if hasattr(job, 'run'): # Make sure it has a run function
                job.run() # Run the job
            else:
                logging.error('Run function not found in ' + job + '.  Skipping...')

    end_time = datetime.now() # Stop the clock

    logging.info('Run Time: ' + str(end_time - start_time))
# End Run

# Return list of jobs in the jobs folder
# Modules can be disabled by renaming them to start with '__'
def list_jobs(folder):
    if os_name == 'Windows':
        folder_seperator = '\\'
    else:
        folder_seperator = '/'

    modules = []

    # Get list of modules from the jobs folder and add them to the modules list
    for module in os.listdir(os.path.dirname(__file__) + folder_seperator + folder):
        if module.startswith('__') or module[-3:] != '.py': # skip files starting with '__' and not ending '.py'
            continue
        
        # Add module to list and strip file extension
        modules.append(module[:-3])

    return modules
# End list_jobs

def config_logging():
    

    logging_file = constants.logging_path + constants.logging_file

    # Create log folder if it doesn't already exist.
    os.makedirs(os.path.dirname(logging_file), exist_ok=True)
    # Create handle to log file
    file_handler = logging.FileHandler(logging_file, mode="a", encoding=None, delay=False)

    # set up logging to file
    logging.basicConfig(
        filename = logging_file,
        level    = constants.logging_log_level, 
        format   = constants.logging_file_format,
        datefmt  = constants.logging_file_time_format
    )

    logging.debug('Logging Setup 1/2')

    if constants.logging_log_to_screen:
        # set up logging to console
        console = logging.StreamHandler()
        console.setLevel(constants.logging_log_level)
        # set a format which is simpler for console use
        console.setFormatter(logging.Formatter(constants.logging_console_format))
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)

    logging.debug('Logging Setup 2/2')

def config_directories ():
    constants.selenium_chromediriver =  binary_path
    os.makedirs(constants.selenium_download_dir, exist_ok=True)
