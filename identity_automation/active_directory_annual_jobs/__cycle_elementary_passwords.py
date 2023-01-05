# Module:           Student Active Directory Job
# Purpose:          Compares the data in SQL to Active Directory and makes changes to the Active Directory to reflect the SQL data
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import logging
import pyodbc
import random
from datetime import datetime
from pypika import MSSQLQuery, functions as fn
from pypika.terms import Values
from identity_automation.common import constants
from identity_automation.lib import mssql
from identity_automation.lib import active_directory
from identity_automation.models import student_model
from identity_automation.models import school_model

# Open DB connection to be reused within module
db                  = mssql.db()
ldap                = active_directory.LDAP()
sql_table           = 'Default_Elementary_Passwords'

# Job Entry Point
def run():

    db.clear_table(sql_table)

    for school in school_model.School.get_schools().values():
        record = {}

        record['School_Code']           = str(school.short_name())
        record['School_Short_Name']     = str(school.school_code())
        record['Password']              = password_generator()

        # Insert record into sql table
        db.insert(sql_table, record)

#End run

# Iterate through students to manage account creation, attributes and group memberships
def password_generator():
    word_list = ['bike','bird','book','chin','clam','club','corn','crow','crib','desk','dime','dirt','flag','game','heat','hill','home','horn','hose','kite','lake','mask','mice','milk','mint','meal','meat','moon','name','nest','nose','pear','rain','road','rock','room','rose','seed','shoe','shop','show','sink','snow','soda','sofa','star','step','stew','tank','team','tent','test','toes','tree','vest','wing','apple','class','crown','crowd','field','juice','plant','river','shape','snail','snake','stove','straw','swing','table','water']
    word = random.choice(word_list)
    number = str(random.randint(0, 9))
    return word + number
# End password_generator