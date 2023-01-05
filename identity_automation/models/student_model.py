# Module:           School Model
# Purpose:          Library wrap student demographics data from SQL and manage the account in Active Directory
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import logging

from datetime import date, datetime
from identity_automation.lib import active_directory
from identity_automation.models import school_model
from identity_automation.common import constants

class Student:
    _sis_values      = {}
    _ad_values     = {}
    _dn              = None
    _ou              = ''
    ad_user_found    = False
    ldap             = None

    # Object constructor from dictionary and searches for the account in Active Directory
    # Stores the passed sis values, searches for the distiguished name and grabs the active directory values
    @classmethod
    def create_from_array(cls, record = {}):
        student = cls() # Create new empty Student

        student._sis_values = record
        
        # if email address is empty or not a myffca.com email address then replace it with the calculated value
        if (not student._sis_values['Email'] or not student._sis_values['Email'].lower().endswith('@myffca.com')):
            student._sis_values['Email'] = (student.first_name().replace(" ", "") + student.ministry_number()[-4:] + '@' + constants.ldap_student_domain).lower()
        
        # Create active directory connection if it doesn't already exist (Shared by all student objects)
        if not Student.ldap:
            Student.ldap = active_directory.LDAP()

        # Proactively get the DN.  Wirte to log if it's not found
        student.get_dn() or logging.info('LDAP DN Lookup: Couldn\'t find: ' + student.first_name() + ' ' + student.last_name() + '(' + str(student.email()) + ')')

        # Get the ldap values
        student._ad_values = Student.ldap.get_user_info(student.dn())

        return student
    # End create_from_array
 
    # Object Constructor.  Creating a new student with no SIS values but sets the DN
    @classmethod
    def create_from_dn(cls, dn):
        student = cls() # Create new empty Student
        student._dn = dn # Populate DN
        student._ou = dn.split(',',1)[1] # populate OU

        # Create active directory connection if it doesn't already exist (Shared by all student objects)
        if not Student.ldap:
            Student.ldap = active_directory.LDAP()

        return student
    # End create_from_dn

    # Get distiguished name
    def dn(self):
        return self._dn
    #End dn

    # Get ou location of user account
    def ou(self):
        return self._ou
    # End ou

    # Get school code of student
    def school_code(self):
        return self._sis_values['School_Code']
    # End school_code

    # Get student code
    def student_code(self):
        return self._sis_values['Student_Code']
    # End student_code

    # Get Minstry Number
    def ministry_number(self):
        return self._sis_values['Ministry_Number']
    # End ministry_number

    # Get last name
    def last_name(self):
        return self._sis_values['Last_Name']
    # End last_name    

    # get First name
    def first_name(self):
        return self._sis_values['Usual_Name']
    # End first_name

    # Get email address
    def email(self):
        if self._sis_values['Email']:
            return self._sis_values['Email']
        else: 
            return ''
    # End email

    # Get grade level
    def grade(self):
        if self._sis_values['Grade_Level'].strip() == 'K':
            return 'EC'
        else:
            return self._sis_values['Grade_Level'].strip()
    # End grade

    # Get grade level
    def birthday(self):
        return self._sis_values['Birthday']
    # End grade

    # get active status
    def status(self, school = None):
        return self._sis_values['Status']
    # End status

    # Get Edsembli values in dict
    def sis_values(self):
        return self._sis_values
    # End sis_values

    # Get Active Directory values in dict
    def ad_values(self):
        return self._ad_values
    # End ad_values

    # Search for the user to get the distiguished name in order (upn <- email, employeeID <- Student Code, upn <- Generated Email Address )
    def get_dn(self, force_query = False):
        
        # Check it's already been discovered if so return it
        if not force_query and self.dn():
            return self.dn()

        Student.ldap.check_bind()

        # If not already found try to find student by Ministry Number (ASN)
        self._dn = Student.ldap.get_user_by_employeeNumber(self.ministry_number())
        if self.dn():
            self.ad_user_found = True
            self._sis_values['Email'] = Student.ldap.get_user_upn(self.dn())
            self._ou = self.dn().split(',',1)[1]
            return self.dn()

        # If not already found try to find student by Student Code
        self._dn = Student.ldap.get_user_by_employeeID(self.student_code())
        if self.dn():
            self.ad_user_found = True
            self._sis_values['Email'] = Student.ldap.get_user_upn(self.dn())
            self._ou = self.dn().split(',',1)[1]
            return self.dn()

        # If not already found try to find student by UserPrincipalName
        self._dn = Student.ldap.get_user_by_upn(self.email())
        if self.dn():
            self.ad_user_found = True
            self._ou = self.dn().split(',',1)[1]
            return self.dn()

        # If not already found try to find student by Ministry Number in Notes field
        self._dn = Student.ldap.get_user_by_info(self.ministry_number())
        if self.dn():
            self.ad_user_found = True
            self._sis_values['Email'] = Student.ldap.get_user_upn(self.dn())
            self._ou = self.dn().split(',',1)[1]
            return self.dn()

        # One last try to see if the student account was found with a generated email address in the userPrincipalName
        email = (self.first_name().replace(" ", "")[0:6] + self.ministry_number()[-4:] + '@' + constants.ldap_student_domain).replace(' ', '')
        self._dn = Student.ldap.get_user_by_upn(email)
        if self.dn():
            self.ad_user_found = True
            self._sis_values['Email'] = email
            self._ou = self.dn().split(',',1)[1]
            return self.dn()
        
        # If not found return None
        return None
    # End get_dn

    def default_password(self):
        school = school_model.School.get_schools()[int(self.school_code())]

        if (self.grade() in ['EC', 'K', '1', '2', '3']):
            return school.default_password()
        else:
            return datetime.strptime(self.birthday(), '%Y-%m-%d').strftime('%Y-%b-%d').lower()

    # Change user's password
    def set_password (self, password):
        return Student.ldap.set_password(self.dn(), password, self.on_password_change_require_change_on_next_login())
    # End set_password

    def on_password_change_require_change_on_next_login(self):
        if (self.grade() in ['EC', 'K' '1', '2', '3', '4']):
            return False
        else:
            return False
    # end on_password_change_require_change_on_next_login

    # Create an Active Directory account for the current Edsembli student
    def create_account(self):
        school = school_model.School.get_schools()[int(self.school_code())]
        username = self.email()[0:self.email().find('@')] # username is the first part of the email address
        ou_path = 'OU=' + school.short_name() + ',' + constants.ldap_student_ou_base # Put user in the correct OU based on school short name
        # If grade is K-3 then use the school default password.  If the grade is 4-12 then use their birthdate in the format YYYY-mmm-dd (ie 2001-jan-01)
            
        # Create User in Active Directory and populate DN in student object
        self._dn = Student.ldap.create_user (
                                            self.student_code(), 
                                            username, 
                                            constants.ldap_student_domain, 
                                            self.first_name(), 
                                            self.last_name(), 
                                            ou_path
                                         )

        self.add_membership('Password Policy K-4')
        self.set_password(self.default_password())

        # if user created correctly store OU and mark as ad found
        if self._dn:
            self._ou = ou_path
            self.ad_user_found = True
        else: # User didn't create properly return None
            return None

        # Get the ldap values
        self._ad_values = Student.ldap.get_user_info(self.dn())

        return self.dn()
    # End create_account
    
    # Move user to a different OU
    def move_ou (self, ou):
        result = Student.ldap.move_user(self.dn(), ou)
        if result:
            self._ou = ou
            self._dn = self._dn.split(',',1)[0] + ',' + ou
        return result
    # End move_ou

    # Get User's Active Directory group memeberships
    def get_current_memberships (self):
        memberships = Student.ldap.get_user_memberships(self.dn())
        return memberships if memberships else {}
    # End get_current_memberships
        
    # Add User to Active Directory group
    def add_membership(self, group):
        return Student.ldap.add_group_membership(self.dn(), group)
    # End add_membership

    # Remove User from Active Directory group
    def remove_membership(self, group):
        return Student.ldap.remove_group_membership(self.dn(), group)
    # End remove_membership

    # get LDAP attribute of user
    def get_attribute(self, attribute):
        return Student.ldap.get_attribute(self.dn(), attribute)
    # End get_attribute

    # set LDAP user attribute
    def update_attribute(self, attribute, value):
        if attribute == 'cn':
           return Student.ldap.update_cn(self.dn(), value) 
        else:
            return Student.ldap.update_attribute(self.dn(), attribute, value)
    # End update_attribute

    # Get or Set Active Directory Status of user
    def ad_status(self, status = None):
        if status is None:
            # Check second bit to see if it's set or not (Holds Disabled status for user)
            userAccountControl = self.get_attribute('userAccountControl')
            if (userAccountControl == None): return True # Student was just created and you're running in simulation mode (assuming active)
            return False if int(userAccountControl) & (1 << (2 - 1)) else True
        elif status:
            self.update_attribute('userAccountControl', self.get_attribute('userAccountControl') & ~(1 << (2 - 1))) # Clears second bit
            self.update_attribute('streetAddress', 'Enabled: ' + date.today().strftime("%Y/%m/%d"))
        else:
            self.update_attribute('userAccountControl', self.get_attribute('userAccountControl') | (1 << (2 - 1))) # Sets second bit
            self.update_attribute('streetAddress', 'Disabled: ' + date.today().strftime("%Y/%m/%d"))
    # End update_attribute

