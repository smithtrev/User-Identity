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

namespace                   = '{http://www.maplewood.com/MWIntegration/StAc_Contact.xsd}'
sql_table                   = 'Student_Contacts'
edsembli_soap_request       = '''<GetContacts xmlns="http://www.maplewood.com:8091/mwWebSrvStAc">
                                    <schoolNum></schoolNum>
                                    <stuCode></stuCode>
                                 </GetContacts>'''
edsembli_records_element    = 'Contact_Details'

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
        record['Contact_Code']                              = edsembli.get(r, 'Contact_Code',                               namespace, 'string')
        record['Contact_Relationship']                      = edsembli.get(r, 'Contact_Relationship',                       namespace, 'number')
        record['Last_Name']                                 = edsembli.get(r, 'Last_Name',                                  namespace, 'number')
        record['First_Name']                                = edsembli.get(r, 'First_Name',                                 namespace, 'number')
        record['Sex']                                       = edsembli.get(r, 'Sex',                                        namespace, 'string')
        record['Email']                                     = edsembli.get(r, 'Email',                                      namespace, 'string')
        record['Address']                                   = edsembli.get(r, 'Address',                                    namespace, 'string')
        record['City']                                      = edsembli.get(r, 'City',                                       namespace, 'string')
        record['Region']                                    = edsembli.get(r, 'Region',                                     namespace, 'string')
        record['Country']                                   = edsembli.get(r, 'Country',                                    namespace, 'string')
        record['Postal_Code']                               = edsembli.get(r, 'Postal_Code',                                namespace, 'string')
        record['Personal_Phone']                            = edsembli.get(r, 'Personal_Phone',                             namespace, 'string')
        record['Contact_Order']                             = edsembli.get(r, 'Contact_Order',                              namespace, 'number')
        record['Emergency_Contact_Order']                   = edsembli.get(r, 'Emergency_Contact_Order',                    namespace, 'string')
        record['PersonId']                                  = edsembli.get(r, 'PersonId',                                   namespace, 'string')
        record['IsLegalGuardian']                           = edsembli.get(r, 'IsLegalGuardian',                            namespace, 'string')
        record['IsCustodian']                               = edsembli.get(r, 'IsCustodian',                                namespace, 'string')
        record['IsNonCustodialAccess']                      = edsembli.get(r, 'IsNonCustodialAccess',                       namespace, 'string')
        record['IsNonCustodialAccess_ParentSite']           = edsembli.get(r, 'IsNonCustodialAccess_ParentSite',            namespace, 'string')
        record['IsCustodian']                               = edsembli.get(r, 'IsCustodian',                                namespace, 'string')
        record['IsNonCustodialAccess']                      = edsembli.get(r, 'IsNonCustodialAccess',                       namespace, 'string')
        record['IsNonCustodialAccess_ParentSite']           = edsembli.get(r, 'IsNonCustodialAccess_ParentSite',            namespace, 'string')
        record['IsNonCustodialAccess_ReportCards']          = edsembli.get(r, 'IsNonCustodialAccess_ReportCards',           namespace, 'string')
        record['IsNonCustodialAccess_OtherStudentReports']  = edsembli.get(r, 'IsNonCustodialAccess_OtherStudentReports',   namespace, 'string')
        
        # Insert record into sql table
        db.insert(sql_table, record)
    # End For Loop - Records

# End interate