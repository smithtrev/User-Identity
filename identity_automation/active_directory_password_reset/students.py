# Module:           Student Active Directory Job
# Purpose:          Compares the data in SQL to Active Directory and makes changes to the Active Directory to reflect the SQL data
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import logging
import pyodbc
import pytz
from datetime import datetime, timedelta
from pypika import MSSQLQuery, functions as fn
from identity_automation.common import constants
from identity_automation.lib import email
from identity_automation.lib import mssql
from identity_automation.lib import active_directory
from identity_automation.lib import notifications
from identity_automation.models import student_model
from identity_automation.models import school_model

# Open DB connection to be reused within module
db                  = mssql.db()
ldap                = active_directory.LDAP()
managed_group_list  = []

# Job Entry Point
def run():

    if constants.execute_changes:
        logging.info('Execution Mode: Preform')
    else:
        logging.info('Execution Mode: Simulate')
    
    # Get Active Students from Edsembli
    active_students = get_active_students()

    # iterate through active Edsembli students and create/modify accounts in Active Directory accordingly
    iterate_edsembli_students(active_students)

# End run

# Iterate through students to manage account creation, attributes and group memberships
def iterate_edsembli_students(students):

    # Loop through records adding them to the values dict
    for s in students:
        # Convert student dict to Student object
        student = student_model.Student.create_from_array(s)

        logging.debug('Start Student Processing: ' + student.email())

        # If AD Account exists for the current student reset password
        if student.ad_user_found:
            
            password = student.default_password()
            logging.info('Set Password for ' + student.first_name() + ' ' + student.last_name() + ' (' + student.email() + ') to ' + password)
            constants.execute_changes and student.set_password(password)

        else:
            logging.debug('Student Not Found: ' + student.email())
    # End For Loop
# End iterate_edsembli_students

# Returns all the active students for the organization
def get_active_students():
    # Build query
    students_table = MSSQLQuery.Table('Student_Demographics')
    query = MSSQLQuery.from_(students_table).select(
        students_table.Student_Code, students_table.Last_Name, students_table.First_Name, students_table.Usual_Name, students_table.Legal_Name, students_table.School_Code, students_table.Birthday, students_table.Grade_Level, students_table.Grad_Year, students_table.Ministry_Number, students_table.Email, students_table.Status
    ).where(
        students_table.status == 'Active'
    ).where(
        students_table.Home_Concurrent == 'H'
    )

    # Get Results
    results = db.select(query)

    # Convert Results to dict
    columns = [column[0] for column in db.db.description]
    students = []
    for row in results:
        students.append(dict(zip(columns, row)))

    return students
# End get_active_students