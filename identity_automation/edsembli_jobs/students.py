# Module:           Student Edsembli Job
# Purpose:          Queries Edsembli to get Student data then interates through students to insert them into MS SQL Database
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import logging
import pyodbc
import xml.etree.ElementTree as ET
from pypika import MSSQLQuery
from identity_automation.lib import edsembli
from identity_automation.lib import mssql
from identity_automation.common import constants

# Open DB connection to be reused within module
db = mssql.db()

namespace                       = '{http://www.maplewood.com/MWIntegration/StAc_Student.xsd}'
sql_table                       = 'Student_Demographics'
edsembli_soap_request           = '''<GetStudents xmlns="http://www.maplewood.com:8091/mwWebSrvStAc">
                                        <schoolNum></schoolNum>
                                        <stuInitial></stuInitial>
                                     </GetStudents>'''
edsembli_records_element        = 'Student_Details'

# Job Entry Point
def run():
    logging.debug('Starting Edsembli > Student > Run')
    tree = ET.fromstring(edsembli.soap(edsembli_soap_request))   # get result from query function then parse into Element Tree
    
    # If no records were found then skip this job (without clearing the table)
    if edsembli.record_count(tree, namespace) == 0:
        return

    db.clear_table(sql_table) # Clear table to prepare for new data

    logging.info('Importing Students in to MS SQL')
    iterate(tree.iter(namespace + edsembli_records_element)) #step through records and insert them into 
#End Run

# iterate through edsembli records inserting each into sql
def iterate(records):
    logging.debug('Starting Edsembli > Student > Iterate')

    # Loop through records adding them to the values dict
    for r in records:
        record = {}

        record['Board_Code']              = edsembli.get(r, 'Board_Code',            namespace, 'number')
        record['School_Code']             = edsembli.get(r, 'School_Code',           namespace, 'number')
        record['Student_Code']            = edsembli.get(r, 'Student_Code',          namespace, 'number')
        record['Last_Name']               = edsembli.get(r, 'Last_Name',             namespace, 'string')
        record['First_Name']              = edsembli.get(r, 'First_Name',            namespace, 'string')
        record['Usual_Name']              = edsembli.get(r, 'Usual_Name',            namespace, 'string')
        record['Legal_Name']              = edsembli.get(r, 'Legal_Name',            namespace, 'string')
        record['Middle_Name']             = edsembli.get(r, 'Middle_Name',           namespace, 'string')
        record['Sex']                     = edsembli.get(r, 'Sex',                   namespace, 'string')
        record['Email']                   = edsembli.get(r, 'Email',                 namespace, 'string')
        record['Phone']                   = edsembli.get(r, 'Phone',                 namespace, 'string')
        record['Birthday']                = edsembli.get(r, 'Birthday',              namespace, 'date'  )
        record['Grade_Level']             = edsembli.get(r, 'Grade_Level',           namespace, 'string').strip()
        record['Ministry_Number']         = edsembli.get(r, 'Ministry_Number',       namespace, 'number')
        record['Alternate_GUID']          = edsembli.get(r, 'Alternate_GUID',        namespace, 'string')
        record['Status']                  = edsembli.get(r, 'Status',                namespace, 'string')
        record['Home_Concurrent']         = edsembli.get(r, 'Home_Concurrent',       namespace, 'string')
        record['Start_Date']              = edsembli.get(r, 'Start_Date',            namespace, 'date'  )
        record['End_Date']                = edsembli.get(r, 'End_Date',              namespace, 'date'  )
        record['Elementary_Start_Date']   = edsembli.get(r, 'Elementary_Start_Date', namespace, 'date'  )
        record['Secondary_Start_Date']    = edsembli.get(r, 'Secondary_Start_Date',  namespace, 'date'  )
        record['MW_Status']               = edsembli.get(r, 'MW_Status',             namespace, 'string')
        record['PersonId']                = edsembli.get(r, 'PersonId',              namespace, 'string')
        
        # Insert record into sql table
        db.insert(sql_table, record)
        
    # End For Loop

# End Interate