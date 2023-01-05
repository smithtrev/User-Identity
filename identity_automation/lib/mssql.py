# Module:           LDAP
# Purpose:          Library to query and modify MSSQL
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import pyodbc
import logging
from pypika import MSSQLQuery, functions as fn
from identity_automation.common import constants

# Database class
# The connection is established when the object is instancated and cleaned up with the object is destroyed
class db():

    db_connection = ''
    db = ''
    
    # Constructor
    # Default to edsembli_sql_connection (in constants file)
    # Connects to the database
    def __init__(self, connection = constants.edsembli_sql_connection):
        #Open Database Connections
        try:
            self.db_connection = pyodbc.connect(connection)
            self.db = self.db_connection.cursor()
        except pyodbc.Error as err:
            logging.critical(' Couldn\'t connect to database: ' + str(err))
            exit()
    # End Constructor
    
    # Destructor
    # Cleans up the connection to the database
    def __del__(self):
        # Close Database Connections
        self.db.close()
        self.db_connection.close()
    # End Deconstructor

    # Deletes all records from the given table
    def clear_table(self, table):
        logging.info('Deleting all records from ' + table)

        #Build Insert SQL statement from values dict
        query = MSSQLQuery.from_(table).delete()
        logging.debug(str(query))
        
        try:
            # Execute Delete SQL statement
            self.db.execute(str(query))
            self.db.commit()
        except pyodbc.Error as err:
            logging.error('Datbase Query: ' + str(query) + '\nError: ' + str(err))

    # Inserts passed dict into the given table
    # The dict index must the column name in SQL
    def insert(self, table, values):
        #Build Insert SQL statement from values dict
        query = MSSQLQuery.into(table).columns(list(values.keys())).insert(list(values.values()))
        logging.debug(str(query))

        try:   
            # Execute Insert SQL statement
            self.db.execute(str(query))
            self.db.commit()
        except pyodbc.Error as err:
            logging.error('Datbase Query: ' + str(query) + '\nError: ' + str(err))
    # End insert

    # Run select statments against database and returns result
    def select(self, query):
        logging.debug(str(query))

        try:   
            # Execute Insert SQL statement
            self.db.execute(str(query))
            return self.db.fetchall()
        except pyodbc.Error as err:
            logging.error('Datbase Select: ' + str(query) + '\nError: ' + str(err))
    # End insert

    # Run execute statments against database with no result
    def execute(self, query):
        logging.debug(str(query))

        query = 'SET NOCOUNT ON; ' + str(query) # bug fix for it throwing Error: No results. Previous SQL was not a query

        try:   
            # Execute SQL statement
            self.db.execute(str(query))
            self.db.commit()
            return True
        except pyodbc.Error as err:
            logging.error('Datbase Execute: ' + str(query) + '\nError: ' + str(err))
    # End execute

    # Checks the provided table to make sure that that there enough records in the table to meet the threshold otherwise returns false.
    def sainity_check(self, table, threshhold):
        students_table = MSSQLQuery.Table(table)
        query = MSSQLQuery.from_(students_table).select(fn.Count('*').as_('count'))
        
        record_count = self.select(query)[0].count
        return record_count >= threshhold
    # End sainity_check 
# End db class

