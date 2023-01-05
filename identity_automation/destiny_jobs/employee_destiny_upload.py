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
db                  = mssql.db(constants.atrieve_sql_connection)

# Job Entry Point
def run():

    # Get Students from Active Directory
    csv_string = get_active_employees()

    upload_to_destiny(csv_string)

#End run

# Returns all the student accounts in school OUs
def get_active_employees():
    # Build query
    assignments_table = MSSQLQuery.Table('Assignments')
    employees_table = MSSQLQuery.Table('Employee_Demographics')
    locations_table = MSSQLQuery.Table('Locations')
    

    query = MSSQLQuery.from_(assignments_table).select(
        locations_table.Name.as_('Site_Name'),
        fn.Concat('P ', fn.Cast(assignments_table.employee_number, 'VARCHAR(50)')).as_('Barcode'),
        fn.Concat('9999', fn.Cast(assignments_table.employee_number, 'VARCHAR(50)')).as_('DistrictID'),
        employees_table.last_name.as_('Last_Name'), 
        employees_table.first_name.as_('First_Name'),
        terms.Term.wrap_constant("Faculty").as_('Patron_Type'),
        terms.Term.wrap_constant('Patron').as_('Access_Level'),
        terms.Term.wrap_constant('A').as_('Status'),
        Case()
            .when(employees_table.gender == 'X', 'U')
            .else_(employees_table.gender).as_('Sex'),
        terms.Term.wrap_constant("Staff").as_('Homeroom'),
        terms.Term.wrap_constant("").as_('Grade_Level'),
        terms.Term.wrap_constant((datetime.today() + timedelta(days=constants.destiny_keep_active_for_days)).strftime('%Y-%m-%d')).as_('Card_Expires'),
        terms.Term.wrap_constant("").as_('Grad_Year'),
        employees_table.email.as_('Username'),
        employees_table.email.as_('Email_1'),
    ).distinct(
    ).join(employees_table, JoinType.left
    ).on(assignments_table.employee_number == employees_table.employee_number
    
    ).join(locations_table, JoinType.left
    ).on(assignments_table.location == locations_table.id
    
    ).where(assignments_table.employee_number.notnull()
    ).where(assignments_table.type != 'CASU'
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
    sftp.putfo(buffer, constants.destiny_ftp_employee_filename)
# End upload_to_destiny

# Custom Format Date function because Pypika doesn't have a function for FORMAT
class format_date(terms.Function):
	def __init__(self, field, format):
		super(format_date, self).__init__('FORMAT', field, format) 