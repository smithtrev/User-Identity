
from identity_automation.lib import mssql
from identity_automation.common import constants
from pypika import MSSQLQuery

# Open DB connection to be reused within module
db              = mssql.db()
sql_table       = 'Student_AD_Notifications'

def clean_table ():
    db.clear_table(sql_table)

def add_notification (student_code, student_name, username, school_code, action, password = None, comment = None):
    record = {}

    record['Student_Code']        = student_code
    record['Student_Name']        = student_name
    record['Username']            = username
    record['Password']            = password
    record['School_Code']         = school_code
    record['Action']              = action
    record['Comment']             = comment
    
    # Insert record into sql table
    db.insert(sql_table, record)

def get_notifications_by_school (school_code):
    # Query SQL for the list of schools
    table = MSSQLQuery.Table(sql_table)
    query = MSSQLQuery.from_(table).select(
        table.Student_Code,
        table.Student_Name,
        table.Username,
        table.Password,
        table.Action,
        table.Comment 
    ).where(
        table.School_Code == school_code
    )

    return db.select(query)

def clear_notifications_by_school (school_code):
    table = MSSQLQuery.Table(sql_table)
    query = MSSQLQuery.from_(table).delete().where(
        table.School_Code == school_code
    )

    db.execute(query)

