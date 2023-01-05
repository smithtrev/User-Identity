# Module:           Contact Edsembli Job
# Purpose:          Queries Edsembli to get Contact data then interates through students to insert them into MS SQL Database
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

namespace                   = '{http://www.maplewood.com/MWIntegration/StAc_StuHomeroom.xsd}'
sql_table                   = 'Student_Homerooms'
edsembli_soap_request       = '''<GetStudentHomerooms xmlns="http://www.maplewood.com:8091/mwWebSrvStAc">
                                    <schoolNum></schoolNum>
                                    <stuCode></stuCode>
                                 </GetStudentHomerooms>'''
edsembli_records_element    = 'Student_Homeroom_Details'

# Job Entry Point
def run():
    
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

        record['Board_Code']                                = edsembli.get(r, 'Board_Code',                                 namespace, 'number')
        record['School_Code']                               = edsembli.get(r, 'School_Code',                                namespace, 'number')
        record['Student_Code']                              = edsembli.get(r, 'Student_Code',                               namespace, 'number')
        record['Room']                                      = edsembli.get(r, 'Room',                                       namespace, 'string')
        record['Designation']                               = edsembli.get(r, 'Designation',                                namespace, 'string')
        record['Track_Code']                                = edsembli.get(r, 'Track_Code',                                 namespace, 'string')
        
        # Insert record into sql table
        db.insert(sql_table, record)
    # End For Loop - Records

# End interate