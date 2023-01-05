# Module:           Student Active Directory Job
# Purpose:          Pull Student Data from MSQL (via Edsembli) and upload it to Destiny to manage student patrons
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy

import csv
import logging
import io
import pyodbc
import paramiko
from datetime import datetime, timedelta
from pypika import MSSQLQuery, functions as fn, Case, JoinType, terms
from identity_automation.common import constants
from identity_automation.lib import mssql

# Open DB connection to be reused within module
db                  = mssql.db()

# Job Entry Point
def run():

    # Get Students from Active Directory
    csv_string = get_active_students()

    upload_to_destiny(csv_string)

#End run

# Returns all the student accounts in school OUs
def get_active_students():
    # Build query
    students_table = MSSQLQuery.Table('Student_Demographics')
    contact1_table = MSSQLQuery.Table('Student_Contacts').as_('Contact_1')
    contact2_table = MSSQLQuery.Table('Student_Contacts').as_('Contact_2')
    contact3_table = MSSQLQuery.Table('Student_Contacts').as_('Contact_3')
    homeroom_table = MSSQLQuery.Table('Student_Homerooms')
    school_table = MSSQLQuery.Table('Schools')

    query = MSSQLQuery.from_(students_table).select(
        school_table.Short_Name.as_('Site_Name'),
        students_table.Ministry_Number.as_('Barcode'),
        fn.Cast(fn.Cast(students_table.Student_Code, 'INT'), 'VARCHAR(50)').as_('DistrictID'),
        students_table.Last_Name, 
        students_table.Usual_Name,
        students_table.Middle_Name,
        Case()
            .when(students_table.Grade_Level == '9', 'Grade 9')
            .else_("Student").as_('Patron_Type'),
        terms.Term.wrap_constant('Patron').as_('Access_Level'),
        terms.Term.wrap_constant('A').as_('Status'),
        Case()
            .when(students_table.Sex == 'X', 'U')
            .else_(students_table.Sex).as_('Sex'),
        homeroom_table.Designation.as_('Homeroom'),
        students_table.Grade_Level,
        terms.Term.wrap_constant((datetime.today() + timedelta(days=constants.destiny_keep_active_for_days)).strftime('%Y-%m-%d')).as_('Card_Expires'),
        students_table.Grad_Year,
        #format_date(fn.Cast(students_table.Birthday, 'date'), 'Y-%m-%d').as_('Birthday'),
        students_table.Email.as_('Username'),
        students_table.Email.as_('Email_1'),
        contact1_table.Email.as_('Email_2'),
        contact2_table.Email.as_('Email_3'),
        contact3_table.Email.as_('Email_4')
    ).distinct(
    ).join(contact1_table, JoinType.left
#   ).on((students_table.Student_Code == contact1_table.Student_Code) & (contact1_table.Contact_Order == terms.Term.wrap_constant('1')) & (contact1_table.Emergency_Contact_Order == terms.Term.wrap_constant('')) & (contact1_table.Contact_Relationship.notin(['Doctor', 'Emergency Contact', 'Sitter']))
    ).on((students_table.Student_Code == contact1_table.Student_Code) & (contact1_table.Contact_Relationship == terms.Term.wrap_constant('M'))
    
    ).join(contact2_table, JoinType.left
    ).on((students_table.Student_Code == contact2_table.Student_Code) & (contact2_table.Contact_Relationship == terms.Term.wrap_constant('F'))
    
    ).join(contact3_table, JoinType.left
    ).on((students_table.Student_Code == contact3_table.Student_Code) & (contact3_table.Contact_Relationship == terms.Term.wrap_constant('G'))

    ).join(school_table, JoinType.left
    ).on(students_table.School_Code == school_table.School_Code
    
    ).join(homeroom_table, JoinType.left
    ).on((students_table.Student_Code == homeroom_table.Student_Code) & (students_table.School_Code == homeroom_table.School_Code)

    ).where(
        (students_table.Status == 'Active')
    )

    # Get Results
    results = db.select(query)

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow([column[0] for column in db.db.description])

    for row in results:
        writer.writerow(row)
        
    return output.getvalue()
# End get_active_students

def upload_to_destiny(file):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(constants.destiny_ftp_server, username=constants.destiny_ftp_username, password=constants.destiny_ftp_password)
    sftp = ssh.open_sftp()
    buffer = io.BytesIO(bytearray(file, 'utf-8'))
    buffer.seek(0)
    sftp.putfo(buffer, constants.destiny_ftp_student_filename)
# End upload_to_destiny

# Custom Format Date function because Pypika doesn't have a function for FORMAT
class format_date(terms.Function):
	def __init__(self, field, format):
		super(format_date, self).__init__('FORMAT', field, format) 