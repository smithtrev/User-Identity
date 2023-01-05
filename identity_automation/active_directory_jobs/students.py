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
    sanity_check()

    if constants.execute_changes:
        logging.info('Execution Mode: Preform')
    else:
        logging.info('Execution Mode: Simulate')

    if constants.execute_moving_past_users:
        logging.info('Move Past Users: Preform')
    else:
        logging.info('Move Past Users: Simulate')
    
    # Get Active Students from Edsembli
    active_students = get_active_students()

    # iterate through active Edsembli students and create/modify accounts in Active Directory accordingly
    iterate_edsembli_students(active_students)

    # Get Students from Active Directory
    student_accounts = get_active_student_accounts()

    # iterate through Active Directory accounts and disable accounts not found in Edsembli
    iterate_student_accounts(student_accounts)

    # iterate through the schools and email out notifications of the key changes
    iterate_school_notifications()

# End run

# Test Connections 
def sanity_check():
    if not db.sainity_check('Student_Demographics', constants.sanity_student_threshold):
        logging.critical('Santity Check Failed: Student_Demographics < ' + constants.sanity_student_threshold + ' records')
        exit()

    if not ldap.connect.result != 'success':
        logging.critical('Santity Check Failed: Active Directory Connection to  < ' + constants.ldap_server + ' failed')
        exit()
# End sanity_check

# Iterate through students to manage account creation, attributes and group memberships
def iterate_edsembli_students(students):

    # Loop through records adding them to the values dict
    for s in students:
        # Convert student dict to Student object
        student = student_model.Student.create_from_array(s)

        logging.debug('Start Student Processing: ' + student.email())

        # If AD Account doesn't not exist for the current student create it
        if not student.ad_user_found:
            logging.info('Create User ' + student.first_name() + ' ' + student.last_name() + ' (' + student.email() + ')')
            constants.execute_changes and student.create_account()
            notifications.add_notification(student.student_code(), student.first_name() + ' ' + student.last_name(), student.email(), student.school_code(), 'Created', student.default_password())

        # Calcuate expected OU of student
        expected_ou = 'OU=' + school_model.School.get_schools()[int(student.school_code())].short_name() + ',' + constants.ldap_student_ou_base
        
        # If the expected ou and current ou are not the same, move the student to the expected OU
        if expected_ou != student.ou():
            stale_account = student.ou().find(constants.ldap_student_disabled_ou_base) > 0
            logging.info('Move User ' + student.email() + ' from ' + student.ou() + ' to ' + expected_ou)
            
            ou_no_base = student.ou().replace(',' + constants.ldap_student_ou_base, '') # Strip Base OU to to prepare to get school short name from next level up ou on the next line
            if (student.ou().find('Stale') == -1):
                notifications.add_notification(student.student_code(), student.first_name() + ' ' + student.last_name(), student.email(), school_model.School.get_school_code_by_short_name(ou_no_base[ou_no_base.rfind('OU=') + 3:]), 'Moved Out')
            
            constants.execute_changes and student.move_ou(expected_ou)
            
            # If account hasn't logged in in ## number day (constants.ldap_student_pwd_reset_reactivate) then reset password to default
            #if stale_account and student.get_attribute('lastLogonTimestamp') < pytz.UTC.localize(datetime.now() - timedelta(days=constants.ldap_student_pwd_reset_reactivate)):
            #    password = student.default_password()
            #    logging.info('Reset Password ' + student.email() + ' to ' + password)
            #    constants.execute_changes and student.set_password(password)
            #    notifications.add_notification(student.student_code(), student.first_name() + ' ' + student.last_name(), student.email(), student.school_code(), 'Moved In', student.default_password())
            #else:
            notifications.add_notification(student.student_code(), student.first_name() + ' ' + student.last_name(), student.email(), student.school_code(), 'Moved In')

        current_values  = student.ad_values() #Get current demographic info from Active Directory
        expected_values = student.sis_values() #Get current demographic info from Edsembli

        # update active directory record with SIS student dempgraphic info
        update_user_info(student, current_values, expected_values)
        
        current_memberships         = student.get_current_memberships() # Get current memberships from Active Directory
        current_managed_memberships = managed_groups(current_memberships)
        expected_memberships        = get_expected_memberships(student) # Calcuate the expected group memberships

        # Add any missing groups that were expected
        for group in list(set(expected_memberships) - set(current_managed_memberships)):
            logging.info('Adding User ' + student.email() + ' to group ' + group)
            constants.execute_changes and student.add_membership(group)

        # Remove any managed groups that the student is a member of and shouldn't be
        for group in list(set(current_managed_memberships)  - set(expected_memberships)):
            logging.info('Removing User ' + student.email() + ' from group ' + group)
            constants.execute_changes and student.remove_membership(group)

        # Get user's Active Directory account status
        ad_status = student.ad_status()

        # If user is in the Manually Disabled Users group and currently active then disable the user
        if 'Manually Disabled Users' in current_memberships and ad_status:
            logging.info('Disabling User: ' + student.email())
            constants.execute_changes and student.ad_status(False)
        # If the user is not in the Manually Disabled Users group and currently disabled then enable the user (only active students are being intereated through)
        elif not ad_status:
            logging.info('Enabling User: ' + student.email())
            constants.execute_changes and student.ad_status(True)

        logging.debug('End Student Processing: ' + student.email())
    # End For Loop
# End iterate_edsembli_students

# Iterate through students to manage account creation, attributes and group memberships
def iterate_student_accounts(accounts):

    # Loop through records adding them to the values dict
    for account in accounts:
        logging.debug('Start Student Processing: ' + str(account.mail))

        # If the accounts doesn't have a value in the employeeID attribute then it was a manually created test account and should be left alone
        if len(account.employeeID) == 0:
            logging.info(str(account.mail) + ' has no student ID in the employeeID attribute.... Skipping')
            continue

        # Find student by student code in Edsembli
        students_table = MSSQLQuery.Table('Student_Demographics')
        query = MSSQLQuery.from_(students_table).select(
            students_table.Status
        ).where(
            students_table.Student_Code == str(account.employeeID),
        ).where(
            students_table.Status == 'Active'
        )

        # Get results
        results = db.select(query)

        # If a record wasn't found or the status is not Active then diable the account and move to stale OU
        if results == None or not len(results):
            student = student_model.Student.create_from_dn(str(account.distinguishedName))
            logging.info('Disable User: ' + str(account.mail))
            constants.execute_changes and constants.execute_disabling_past_users and student.ad_status(False)
            logging.info('Move User ' + str(account.mail) + ' from ' + str(account.distinguishedName).split(',', 1)[1] + ' to ' + constants.ldap_student_disabled_ou_base)
            constants.execute_changes and constants.execute_moving_past_users and student.move_ou(constants.ldap_student_disabled_ou_base)

            #If account's department is blank fill it in with unknown
            if not hasattr( 'account', 'department') or account.department == '':
                school_code = '9999'
            else:
                school_code = school_model.get_school_code_by_short_name(account.department)

            #Move student to A1 license
            student.add_membership('365 A1 Student License')
            student.remove_membership('365 A3 Student License')

            # Write to notification log if the student was modified (if it's not it will only show up in the log file)
            if constants.execute_changes and (constants.execute_moving_past_users or constants.execute_disabling_past_users):
                notifications.add_notification(str(account.employeeID), str(account.givenName) + ' ' + str(account.sn), str(account.mail), str(school_code), 'Disabled')

        logging.debug('End Student Processing: ' + str(account.mail))

    # End For Loop
# End iterate_student_accounts

# Iterate through students to manage account creation, attributes and group memberships
def iterate_school_notifications():
    
    # Get School Data
    for school in school_model.School.get_schools().values():
        body = ''
        activations = ''
        deactivations = ''

        for notification in notifications.get_notifications_by_school(school.school_code()):
            
            if notification.Action in ['Created', 'Moved In', 'Reactivated']:
                activations = activations + '<tr><td>' + str(notification.Student_Code) + '</td><td>' + notification.Student_Name + '</td><td>' + notification.Username +'</td><td>' + (notification.Password if isinstance(notification.Password, str) else '') + '</td><td>' + notification.Action +'</td></tr>'
                if isinstance(notification.Comment, str) and len(notification.Comment) :
                    activations = activations + '<tr><td align="right">Comment: </td><td colspan="4">' + notification.Comment + '</td></tr>'
            else: # If deactivation
                deactivations = deactivations + '<tr><td>' + str(notification.Student_Code) + '</td><td>' + notification.Student_Name + '</td><td>' + notification.Username +'</td><td>' + notification.Action +'</td></tr>'
                if isinstance(notification.Comment, str) and len(notification.Comment) :
                    deactivations = deactivations + '<tr><td align="right">Comment: </td><td colspan="4">' + notification.Comment + '</td></tr>'

        # if no account changes were made then don't send an email
        if  len(activations) or len (deactivations):
            body = body + '<h2>' + school.short_name() + ' Activations</h2>'
            body = body + '<p><small>Accounts that have been newly created, reactivated or moved from another school</small></p>'
            body = body + '<table width="100%"><tr><td><b>Student Code</b></td><td><b>Student Name</b></td><td><b>Username</b></td><td><b>Password</b></td><td><b>Action</b></td></tr>'
            
            if len(activations):
                body = body + activations
            else:
                body = body + '<tr><td colspan="5">No Records<td></tr>'
            body = body + '</table>'

            body = body + '<h2>' + school.short_name() + ' Deactivations</h2>'
            body = body + '<p><small>Accounts that have been newly disabled due to not being active in Esembli</small></p>'
            body = body + '<table width="100%"><tr><td><b>Student Code</b></td><td><b>Student Name</b></td><td><b>Username</b><td><b>Action</b></td></tr>'
            
            if len(deactivations):
                body = body + deactivations
            else:
                body = body + '<tr><td colspan="5">No Records<td></tr>'
            body = body + '</table>'
            body = body + '<br><br>'
            body = body + '<small>This is an automated message.  If you have any questions or concerns about the changes made please create a ticket by emailing: <a href="mailto:ffcatech@ffca-calgary.com">ffcatech@ffca-calgary.com</a>'

            if email.send(school.student_notification_email(), 'FFCA ' + school.short_name() + ' Student Account Changes', body):
                logging.info(school.short_name() + ' Email successfully sent to ' + school.student_notification_email())
                notifications.clear_notifications_by_school(school.school_code())
                logging.info(' Clear Notifications table for: ' + school.short_name())
# end iterate_school_notifications

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

# Returns all the student accounts in school OUs
def get_active_student_accounts():
    students = []
    schools = school_model.School.get_schools()

    # Get students from each school OU
    for school in schools.values():
        students = students + ldap.get_active_users('OU=' + school.short_name() + ',' + constants.ldap_student_ou_base)

    return students
# End get_active_students

# Calcuate the groups the student should belong to
def get_expected_memberships (student):

    # Groups that every student belongs go
    memberships = ['Student-All']

    # Determine the password policy based on the student's grade
    if student.grade().strip() in ['EC', 'K', '1', '2', '3', '4']:
        memberships.append('Password Policy K-4')
    else:
        memberships.append ('Password Policy 5-12')

    # Determine the student's Office 365 licensing based on active status

    if student.status() == 'Active' and not student.grade().strip() in ['EC', 'K']:
        memberships.append('365 A3 Student License')
    else:
        memberships.append('365 A1 Student License')
    
    # Add the Student School group
    memberships.append('Student-' + school_model.School.get_schools()[int(student.school_code())].short_name())
    
    # Add the Student grade group
    memberships.append('Student-Grade-' + student.grade().strip())

    # return calcuated group memberships
    return memberships
# End get_expected_memberships

# Remove unmanaged groups from the the group list so they aren't deleted
def managed_groups (groups):
    global managed_group_list # Use global variable

    # If managed_group_list is empty (first call of this function), populate it and store it in the global variable
    if not managed_group_list:
        schools = school_model.School.get_schools() # Get School instances
        managed_group_list = constants.ldap_managed_groups # Get Statis Managed groups from constants file

        # Add School Groups to managed_group_list 
        for school in schools.values():
            managed_group_list.append('Student-' + school.short_name())

        # Add Grade Groups to managed_group_list 
        for grade in ['EC'] + list(range (1, 13)): # EC to 12
            managed_group_list.append('Student-Grade-' + str(grade))

    filtered_groups = []
    # Loop through managed_group_list to see if the student and return only the groups that the student belongs to that are in that list
    for group in managed_group_list:
        if group in groups:
            filtered_groups.append(group)
    return filtered_groups
# End managed_groups

# Compare curent AD info to SIS info and update any values that aren't indentical
# Note: the proxyAddress field is not managed because it is not needed for students accounts which use Google Workspace for their email
def update_user_info(student, current, expected):
    if not current:
        logging.info('Skipping user: ' + student.email() + ' cannot find active directory account.')
        return

    # Get School Shortname from array of schools returned from get_schools
    school_code = school_model.School.get_schools()[int(expected['School_Code'])].short_name()

    # Get username (everything before the @ in the email address)
    username = (expected['Email'][0:expected['Email'].find('@')]).lower()
    
    # the description attribute is a tuple in ldap, so if we only get the first value of the tuple.  So it can also be handled if it's empty.
    if isinstance(current['description'], tuple):
        current['description'] = current['description'][0]

    # For each field test if they're different, if they are, change the value and log it
    test_update_field(student, 'cn',                            current['cn'],                          username)
    test_update_field(student, 'company',                       current['company'],                     expected['Grad_Year'])
    test_update_field(student, 'department',                    current['department'],                  school_code)
    test_update_field(student, 'description',                   current['description'],                 expected['First_Name'] + ' ' + expected['Legal_Name'])
    test_update_field(student, 'displayName',                   current['displayName'],                 expected['Usual_Name'] + ' ' + expected['Last_Name'])
    test_update_field(student, 'employeeID',                    current['employeeID'],                  expected['Student_Code'])
    test_update_field(student, 'employeeNumber',                current['employeeNumber'],              expected['Ministry_Number'])
    test_update_field(student, 'employeeType',                  current['employeeType'],                'Student')
    test_update_field(student, 'givenName',                     current['givenName'],                   expected['Usual_Name'])
    test_update_field(student, 'info',                          current['info'],                        expected['Ministry_Number'])
    test_update_field(student, 'mail',                          current['mail'],                        expected['Email'])
    test_update_field(student, 'physicalDeliveryOfficeName',    current['physicalDeliveryOfficeName'],  'Grade ' + expected['Grade_Level'].strip())
    test_update_field(student, 'sAMAccountName',                current['sAMAccountName'],              username)
    test_update_field(student, 'sn',                            current['sn'],                          expected['Last_Name'])
    test_update_field(student, 'title',                         current['title'],                       'Student')
    test_update_field(student, 'userPrincipalName',             current['userPrincipalName'],           expected['Email']) \
        and student.get_dn() # get_dn is fired if the userPrincipalName is changed since this is the unique identifier used to reference the student in Active Directory.  The value doesn't need to be saved since this will just update the stored dn value in the object
# End update_user_info

# Test the field and updates it if needed.
# Returns True if the value was changed
def test_update_field(student, field, old_value, new_value):
    old_value = str(old_value)
    new_value = str(new_value)
    if (old_value is not None and old_value.casefold() != new_value.casefold()): # Compare values as case insensitive
        if not old_value: old_value = ''
        if not new_value: new_value = ''
        logging.info('Updating user: ' + str(student.email()) + ' ' + field + ' from "' + old_value + '" to "' + new_value + '"')
        constants.execute_changes and student.update_attribute(field, new_value)
        return True
    else:
        return False
#End test_update_field