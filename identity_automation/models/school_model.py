# Module:           School Model
# Purpose:          Library wrap student demographics data from SQL and manage the account in Active Directory
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

from pypika import MSSQLQuery
from identity_automation.lib import mssql

# Open DB connection to be reused within module
db = mssql.db()

class School:
    _schools = {}
    _values = {}

    # Constructor save record
    def __init__(self, record):
        self._values = record
    # End init

    # Get School Name
    def name(self):
        return self._values.Name
    # End name

    # Get School Short Name
    def short_name(self):
        return self._values.Short_Name
    # End short_name

    # Get School Code
    def school_code(self):
        return self._values.School_Code
    # End School Code

    # Get School Code
    def student_notification_email(self):
        return self._values.Student_Notifications_Email
    # End School Code

    # Get School's Default Password (only used for K-3)
    def default_password(self):
        # Query SQL for the list of schools
        default_elementary_passwords_table = MSSQLQuery.Table('Default_Elementary_Passwords')
        query = MSSQLQuery.from_(default_elementary_passwords_table).select(
            default_elementary_passwords_table.Password
        ).where(
            default_elementary_passwords_table.School_Code == self.school_code()
        ) 

        # Create an indexed array of School instances so that schools can be referenced by school code
        for record in db.select(query):
            return record.Password
        return None
    # End default_password

    # Get a list of schools
    # This function caches the in the class and to save resources rather than query the SQL database every time the data is needed
    @staticmethod
    def get_schools():

        # If schools list is cached then return cache
        if School._schools:
            return School._schools

        # Query SQL for the list of schools
        schools_table = MSSQLQuery.Table('Schools')
        query = MSSQLQuery.from_(schools_table).select(
            schools_table.School_Code, schools_table.Name, schools_table.Short_Name, schools_table.Student_Notifications_Email
        )

        # Create an indexed array of School instances so that schools can be referenced by school code
        for record in db.select(query):
            if record.School_Code.isnumeric():
                School._schools[int(record.School_Code)] = School(record)

        return School._schools

    @staticmethod
    def get_school_code_by_short_name(short_name):
        
        for school in School.get_schools().values():
            if school.short_name() == short_name:
                return school.school_code()
            
        return ''
    # End get_school_code_by_short_name
