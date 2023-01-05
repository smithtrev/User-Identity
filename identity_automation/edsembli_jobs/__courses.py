# Module:           Course Edsembli Job
# Purpose:          Queries Edsembli to get Course data then interates through students to insert them into MS SQL Database
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

namespace                   = '{http://www.maplewood.com/MWIntegration/StAc_Course.xsd}'
sql_table                   = 'Courses'
edsembli_soap_request       = '''<GetCourses xmlns="http://www.maplewood.com:8091/mwWebSrvStAc">
                                    <schoolNum></schoolNum>
                                 </GetCourses>'''
edsembli_records_element    = 'Course_Details'

# Job Entry Point
def run():
    print('Running Courses')
    tree = ET.fromstring(edsembli.soap(edsembli_soap_request))   # get result from query function then parse into Element Tree
    
    # If no records were found then skip this job (without clearing the table)
    if edsembli.record_count(tree, namespace) == 0:
        return

    db.clear_table(sql_table) # Clear table to prepare for new data

    iterate(tree.iter(namespace + edsembli_records_element)) #step through records and insert them into 
#End Run

# iterate through edsembli records inserting each into sql
def iterate(records):

    # Loop through records adding them to the records dict
    for r in records:
        record = {}

        record['Board_Code']                        = edsembli.get(r, 'Board_Code',                         namespace, 'number')
        record['School_Code']                       = edsembli.get(r, 'School_Code',                        namespace, 'number')
        record['Course_Code']                       = edsembli.get(r, 'Course_Code',                        namespace, 'number')
        record['Name']                              = edsembli.get(r, 'Name',                               namespace, 'string')
        record['Course_Type']                       = edsembli.get(r, 'Course_Type',                        namespace, 'number')
        record['Low_Grade_Level']                   = edsembli.get(r, 'Low_Grade_Level',                    namespace, 'number')
        record['High_Grade_Level']                  = edsembli.get(r, 'High_Grade_Level',                   namespace, 'number')
        record['Credit_Value']                      = edsembli.get(r, 'Credit_Value',                       namespace, 'string')
        record['Fee']                               = edsembli.get(r, 'Fee',                                namespace, 'string')
        record['Weight']                            = edsembli.get(r, 'Weight',                             namespace, 'string')
        record['Course_Code_Number']                = edsembli.get(r, 'Course_Code_Number',                 namespace, 'string')
        record['Code_Name']                         = edsembli.get(r, 'Code_Name',                          namespace, 'string')
        record['Code_Delivery_Desc']                = edsembli.get(r, 'Code_Delivery_Desc',                 namespace, 'string')
        record['Code_Delivery_Grouping']            = edsembli.get(r, 'Code_Delivery_Grouping',             namespace, 'string')
        record['Is_Reported_To_Onsis']              = edsembli.get(r, 'Is_Reported_To_Onsis',               namespace, 'number')
        record['Display_During_Choice_Selection']   = edsembli.get(r, 'Display_During_Choice_Selection',    namespace, 'string')
        
        # Insert record into sql table
        db.insert(sql_table, record)
    # End For Loop - Records

# End interate