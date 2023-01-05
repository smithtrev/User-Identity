# Module:           Classes Edsembli Job
# Purpose:          Queries Edsembli to get Class data then interates through students to insert them into MS SQL Database
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import pyodbc
import xml.etree.ElementTree as ET
from pypika import MSSQLQuery
from identity_automation.lib import edsembli
from identity_automation.lib import mssql
from identity_automation.common import constants

# Open DB connection to be reused within module
db = mssql.db()

namespace                   = '{http://www.maplewood.com/MWIntegration/StAc_Class.xsd}'
sql_table                   = 'Courses'
edsembli_soap_request       = '''<GetClasses xmlns="http://www.maplewood.com:8091/mwWebSrvStAc">
                                    <schoolNum></schoolNum>
                                 </GetClasses>'''
edsembli_records_element    = 'Class_Details'

# Job Entry Point
def run():
    
    tree = ET.fromstring(edsembli.soap(edsembli_soap_request))   # get result from query function then parse into Element Tree
    
    # If no records were found then skip this job (without clearing the table)
    if edsembli.record_count(tree, namespace) == 0:
        return

    db.clear_table(sql_table) # Clear table to prepare for new data
    db.clear_table('Class_Class_Sets') # Clear table to prepare for new data
    db.clear_table('Class_Day_Period_Set') # Clear table to prepare for new data

    iterate(tree.iter(namespace + edsembli_records_element)) #step through records and insert them into 
#End Run

# iterate through edsembli records inserting each into sql
def iterate(records):

    # Loop through records adding them to the records dict
    for r in records:
        record = {}

        record['Board_Code']              = edsembli.get(r, 'Board_Code',                namespace, 'number')
        record['School_Code']             = edsembli.get(r, 'School_Code',               namespace, 'number')
        record['Course_Code']             = edsembli.get(r, 'Course_Code',               namespace, 'number')
        record['Class_Section']           = edsembli.get(r, 'Class_Section',             namespace, 'string')
        record['Track_Code']              = edsembli.get(r, 'Track_Code',                namespace, 'string')
        record['Name']                    = edsembli.get(r, 'Name',                      namespace, 'string')
        record['Class_Size']              = edsembli.get(r, 'Class_Size',                namespace, 'number')
        record['Class_Max_Seats']         = edsembli.get(r, 'Class_Max_Seats',           namespace, 'number')
        record['Class_Credit_Value']      = edsembli.get(r, 'Class_Credit_Value',        namespace, 'number')
        record['Code_Grade']              = edsembli.get(r, 'Code_Grade',                namespace, 'string')
        record['Code_Name']               = edsembli.get(r, 'Code_Name',                 namespace, 'string')
        record['Code_Delivery_Desc']      = edsembli.get(r, 'Code_Delivery_Desc',        namespace, 'string')
        record['Code_Delivery_Grouping']  = edsembli.get(r, 'Code_Delivery_Grouping',    namespace, 'string')
        record['Code_Number']             = edsembli.get(r, 'Code_Number',               namespace, 'number')
        record['Is_Reportable']           = edsembli.get(r, 'Is_Reportable',             namespace, 'string')
        record['Is_ContinuousEntry']      = edsembli.get(r, 'Is_ContinuousEntry',        namespace, 'string')
        
        # Insert record into sql table
        db.insert(sql_table, record)

        for s in r.iter(namespace + 'ClassSet'):
            set = {}
            set['Board_Code']             = record['Board_Code']
            set['School_Code']            = record['School_Code'] 
            set['Course_Code']            = record['School_Code'] 
            set['Set']                    = edsembli.get(s, 'Set',                       namespace, 'string')
            set['Pattern']                = edsembli.get(s, 'Pattern',                   namespace, 'string')
            set['Semester']               = edsembli.get(s, 'Semester',                  namespace, 'string')
            set['Term']                   = edsembli.get(s, 'Term',                      namespace, 'string')

            # Insert record into sql table
            db.insert('Class_Class_Sets', set)
        # End For Loop - ClassSet

        for s in r.iter(namespace + 'DayPeriodSet'):
            set = {}
            set['Board_Code']             = record['Board_Code']
            set['School_Code']            = record['School_Code'] 
            set['Course_Code']            = record['School_Code'] 
            set['Day']                    = edsembli.get(s, 'Day',                       namespace, 'string')
            set['Period']                 = edsembli.get(s, 'Period',                    namespace, 'string')
            set['Semester']               = edsembli.get(s, 'Semester',                  namespace, 'string')
            set['Term']                   = edsembli.get(s, 'Term',                      namespace, 'string')
            
            # Insert record into sql table
            db.insert('Class_Day_Period_Set', set)
        # End For Loop - DayPeriodSet

    # End For Loop - Records

# End interate