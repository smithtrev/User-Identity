# Module:           Student Edsembli Job
# Purpose:          Queries Edsembli to get Student data then interates through students to insert them into MS SQL Database
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import logging
import pyodbc
from pypika import MSSQLQuery, functions as fn
from identity_automation.lib import atrieve
from identity_automation.lib import mssql
from identity_automation.common import constants
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Open DB connection to be reused within module
db = mssql.db(constants.atrieve_sql_connection)

# Job Entry Point
def run():
    logging.debug('Starting Atrieve > Empoloyee Demographics > Run')
    browser = atrieve.login()

    for report in constants.atrieve_employee_reports:
        data = atrieve.get(browser, report['url'])

        db.clear_table(report['sql_table']) # Clear table to prepare for new data

        logging.info('Importing data in to' + report['sql_table'])
        iterate(report['sql_table'], data) #step through records and insert them into table

    clean_data()

#End Run

# iterate through edsembli records inserting each into sql
def iterate(sql_table, records): 
    logging.debug(f'Starting Atreive > sql_table > Iterate')

    # Loop through records adding them to the values dict
    for record in records:
        # Insert record into sql table
        db.insert(sql_table, record)
        
    # End For Loop

def clean_data():
    logging.debug('Starting Atreive > Clean_Data')
    logging.info('Appending domain to email addresses where missing')

    employee = MSSQLQuery.Table('Employee_Demographics')
    statement = employee.update().set(employee.email, fn.Concat(employee.email, '@ffca-calgary.com')).where(employee.email.not_like('%@%'))
    db.execute(str(statement))

# End clean_data