# Module:           Student Active Directory Job
# Purpose:          Compares the data in SQL to Active Directory and makes changes to the Active Directory to reflect the SQL data
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import logging
import io
import pyodbc
from datetime import datetime
from ftplib import FTP
from pypika import MSSQLQuery, functions as fn
from identity_automation.common import constants
from identity_automation.lib import mssql
from identity_automation.lib import active_directory
from identity_automation.models import student_model
from identity_automation.models import school_model

# Open DB connection to be reused within module
db                  = mssql.db()
ldap                = active_directory.LDAP()
sql_table           = 'Student_Emails'

# Job Entry Point
def run():

    # Get Students from Active Directory
    student_accounts = get_active_student_accounts()

    # iterate through Active Directory accounts and disable accounts not found in Edsembli
    csv_string = iterate_student_accounts(student_accounts)

    upload_to_edsembli(csv_string)

#End run

# Iterate through students to manage account creation, attributes and group memberships
def iterate_student_accounts(accounts):
    csv_string = 'Student_Number|"d2luser"|"Student_Email"\r\n'

    db.clear_table(sql_table)

    # Loop through records adding them to the values dict
    for account in accounts:
        logging.debug('Adding to Student_Emails table: ' + str(account.mail))

        # Find student by student code in Edsembli
        record = {}

        record['Student_Code']      = str(account.employeeID)
        record['Username']          = str(account.sAMAccountName)
        record['Email']             = str(account.mail)
        
        # Insert record into sql table
        db.insert(sql_table, record)

        csv_string = csv_string + record['Student_Code'] + '|"' + record['Username'] + '"|"' + record['Email'] + '"\r\n'
    # End For Loop

    return csv_string
# End iterate_student_accounts

# Returns all the student accounts in school OUs
def get_active_student_accounts():
    students = []
    schools = school_model.School.get_schools()

    # Get students from each school OU
    for school in schools.values():
        students = students + ldap.get_active_users('OU=' + school.short_name() + ',' + constants.ldap_student_ou_base)

    return students
# End get_active_students

def upload_to_edsembli(file):
    ftp = FTP(constants.edsembli_ftp_server)
    ftp.login(constants.edsembli_ftp_username, constants.edsembli_ftp_password)
    ftp.cwd('/FFCA/Incoming')
    ftp.storbinary('STOR AccountStudent.csv', io.BytesIO(bytearray(file, 'utf-8')))