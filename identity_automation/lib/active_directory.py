# Module:           LDAP
# Purpose:          Library to search and modify users
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import ldap3
import logging
from datetime import datetime, timedelta
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups
from ldap3.extend.microsoft.removeMembersFromGroups import ad_remove_members_from_groups
from ldap3.extend.microsoft.modifyPassword import ad_modify_password
from identity_automation.common import constants

# Set connection info for ldap.  LDAP requires Domain Admin access to make changes to users


class LDAP():

    connect = None
    
    # Constructor
    # Intiates a single connection to the ldap server that will be used for all queries
    def __init__(self, ldap_server = constants.ldap_server, username = constants.ldap_username, password = constants.ldap_password):
        server = ldap3.Server(ldap_server, port = 636, use_ssl = True)
        self.connect = ldap3.Connection(server, username, password, auto_bind=True)

    # Get All Users
    def get_active_users (self, search_base):
        try:
            self.check_bind()
            self.connect.search(
                                            search_base, 
                                            '(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))',
                                            attributes=['employeeID', 'employeeNumber', 'givenName', 'sn', 'distinguishedName', 'mail', 'sAMAccountName']
                                       )

            return self.connect.entries
        except Exception as err:
            # If users can't be found return none
            logging.error('LDAP Search: ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_users

        # Get All Users
    def get_users_expiry (self, search_base):
        try:
            self.check_bind()
            self.connect.search(
                                            search_base,
                                            '(&(objectCategory=person)(objectClass=user))',
                                            attributes=['mail', 'sAMAccountName', 'pwdLastSet']
                                       )

            return self.connect.entries
        except Exception as err:
            # If users can't be found return none
            logging.error('LDAP Search: ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_users

    def check_bind(self):
        if not self.connect.bound:
            if not self.connect.bind():
                logging.critical('Error Connecting to Active Directory: ' + self.connect.result)
                exit()


    # Get attributes of given user
    def get_user_info (self, dn, search_base = constants.ldap_search_base):

        attributes_list=['sAMAccountName', 'cn', 'company', 'employeeID', 'employeeNumber', 'employeeType', 'department', 'description', 'displayName', 'distinguishedName', 'givenName', 'info', 'mail', 'physicalDeliveryOfficeName', 'postalCode', 'sn', 'telephoneNumber', 'title', 'userAccountControl', 'userPrincipalName']

        try:
            self.connect.search(
                                    search_base,
                                    ('(&(objectClass=user)(distinguishedName=%s))' % dn),
                                    attributes = attributes_list
                                )

            # Convert to dict                    
            values = {}
            for key in attributes_list:
                values[key] = getattr(self.connect.entries[0], key).value

            return values

        except Exception as err:
            # If user info can't be found return none
            logging.debug('LDAP DN Search: ' + str(dn) + ' in ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_user_info

    # Get distinguishedName of user by searching userPrincipalName
    def get_user_upn (self, dn, search_base = constants.ldap_search_base):
        try:
            self.connect.search(
                                    search_base, 
                                    ('(&(objectClass=user)(distinguishedName=%s))' % dn), 
                                    attributes=['userPrincipalName']
                                )

            return self.connect.entries[0].userPrincipalName.value
        except Exception as err:
            # If user can't be found return none
            logging.debug('LDAP UPN Lookup: ' + dn + ' ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_user_by_upn
    
    # Get distinguishedName of user by searching userPrincipalName
    def get_user_by_upn (self, upn, search_base = constants.ldap_search_base):
        if not upn: upn = ''
        try:
            self.connect.search(
                                    search_base, 
                                    ('(&(objectClass=user)(userPrincipalName=%s))' % upn), 
                                    attributes=['distinguishedName']
                                )
            return self.connect.entries[0].entry_dn
        except Exception as err:
            # If user can't be found return none
            logging.debug('LDAP UPN Search: ' + upn + ' ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_user_by_upn

    # Get distiguished name of user by searching employee ID
    def get_user_by_employeeID (self, value, search_base = constants.ldap_search_base):
        try:
            self.connect.search(
                                    search_base, 
                                    '(&(objectClass=user)(employeeID=%s))' % value, 
                                    attributes=['distinguishedName']
                                )
            return self.connect.entries[0].entry_dn

        except Exception as err:
            # If user can't be found return none
            logging.debug('LDAP EmployeeId Search: ' + value + ' ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_user_by_employeeID

    # Get distiguished name of user by searching employee number
    def get_user_by_employeeNumber (self, value, search_base = constants.ldap_search_base):
        try:
            self.connect.search(
                                    search_base,
                                    ('(&(objectClass=user)(employeeNumber=%s))' % value),
                                    attributes=['distinguishedName']
                                )
            return self.connect.entries[0].entry_dn

        except Exception as err:
            # If user can't be found return none
            logging.debug('LDAP EmployeeNumber Search: ' + value + ' ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_user_by_employeeNumber

    # Get distiguished name of user by searching info
    def get_user_by_info (self, employeeNumber, search_base = constants.ldap_search_base):
        try:
            self.connect.search(
                                    search_base, 
                                    '(&(objectClass=user)(info=%s))' % employeeNumber, 
                                    attributes=['distinguishedName']
                                )
            return self.connect.entries[0].entry_dn

        except Exception as err:
            # If user can't be found return none
            logging.debug('LDAP Info Search: ' + employeeNumber + ' ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_user_by_info

    # Get distiguished name of group by searching cn
    def get_group_by_cn (self, group_cn, search_base = constants.ldap_search_base):
        try:
            self.connect.search(
                                    search_base, 
                                    '(&(objectClass=group)(cn=%s))' % group_cn, 
                                    attributes=['distinguishedName']
                                )
            return self.connect.entries[0].entry_dn

        except Exception as err:
            # If user can't be found return none
            logging.debug('LDAP Group CN Search: ' + group_cn + ' ' + str(search_base) + '\nError: ' + str(err))
            return None
    # End get_group_by_cn

    # Create User
    def create_user (self, employeeid, username, domain, first_name, last_name, ou):
        try:
            dn = 'CN=' + username + ',' + ou

            attrs = {}
            attrs['cn'] = username
            attrs['employeeID'] = employeeid
            attrs['givenName'] = first_name
            attrs['sn'] = last_name
            attrs['sAMAccountname'] =  username
            attrs['userPrincipalName'] = username + '@' + domain

            # Create User
            self.connect.add(dn, object_class = ['user', 'organizationalPerson', 'person', 'top'], attributes = attrs)

            return dn
        except Exception as err:
            # If create user fails, continue script
            logging.error('LDAP Create User: ' + str(username) + '@' + str(domain) + ' failed\nError: ' + str(err))
            return None
    # End create_user

    def set_password (self, dn, password, force_password_change = False):
        # Set account to active
        self.update_attribute(dn, 'userAccountControl', 512)
        
        # Set Password
        result = ad_modify_password(self.connect, dn, password, None)

        print(password)
        print(result)

        # Force Password change
        if force_password_change:
            self.update_attribute(dn, 'pwdLastSet', 0)
    # end set_password

    # Move user to different OU
    def move_user (self, user, ou):
        try:
            self.connect.modify_dn(user, user.split(',', 1)[0], new_superior = ou)

            return True
        except Exception as err:
            # If move user fails, continue script
            logging.error('LDAP Move User: ' + str(user) + ' to ' + str(ou) + '\nError: ' + str(err))
            return False
    # End move_user

    # Get groups that the user belongs to
    def get_user_memberships (self, user, search_base = constants.ldap_search_base):
        try:
            person = ldap3.ObjectDef('user')

            groups = ldap3.Reader(self.connect, person, search_base, '(&(member=' + user + ')(objectClass=group))').search()
            
            memberships = []
            if len(groups):
                for group in groups: 
                    memberships.append(group.entry_dn[3:group.entry_dn.find(',')]) # Get CN name of group from DN and add it to list

            return memberships
        except Exception as err:
            # If looks up fails, return none and continue script
            logging.error('LDAP Get Memberships: ' + str(user) + '\nError: ' + str(err))
            return None
    # End get_user_memberships

    # Add User to group
    def add_group_membership(self, user, group):
        try:
            group_dn = self.get_group_by_cn(group) # Get DN from CN
            if not group_dn is None:
                ad_add_members_to_groups(self.connect, user, group_dn, True, True)
            else:
                logging.error('LDAP Add Membership: ' + str(user) + ' to ' + str(group) + '\nError: Group not found')
            return True
        except Exception as err:
            # If adding user to the group fails, log and continue with script
            logging.error('LDAP Add Membership: ' + str(user) + ' to ' + str(group_dn) + '\nError: ' + str(err))
            return False
    # End add_group_membership

    # remove user from group
    def remove_group_membership(self, user, group):
        try:
            group = self.get_group_by_cn(group) # Get DN from CN
            
            ad_remove_members_from_groups(self.connect, user, group, True, True)
            return True
        except Exception as err:
            # If removing user to the group fails, log and continue with script
            logging.error('LDAP Remove Membership: ' + str(user) + ' from ' + str(group) + '\nError: ' + str(err))
            return False
    # End remove_group_membership

    # get LDAP attribute of user
    def get_attribute(self, user, attribute):
        try:
            self.connect.search(
                                    user.split(',', 1)[1], 
                                    '(&(objectClass=user)(distinguishedName=%s))' % user, 
                                    attributes=[attribute]
                                )
                  
            return self.connect.entries[0][attribute].value
        except Exception as err:
            # If removing user to the group fails, log and continue with script
            logging.error('LDAP Get Attribute: ' + str(user) + ' from ' + str(attribute) + '\nError: ' + str(err))
            return None
    # End get_attribute

    # set LDAP user attribute
    def update_attribute(self, user, attribute, value):
        try:
            self.connect.modify(user,
                {attribute: [(ldap3.MODIFY_REPLACE, [value])]})

            #return user.update_attribute(attribute, value)
        except Exception as err:
            # If removing user to the group fails, log and continue with script
            logging.error('LDAP Update Attribute: ' + str(user) + ' from ' + str(attribute) + '\nError: ' + str(err))
            return None
    # End update_attribute

    # set LDAP user cn.  This actually changes the distringuished name which the CN is derived from.
    def update_cn(self, user, new_cn):
        try:
            return self.connect.modify_dn(user, "cn=" + new_cn)

            #return user.update_attribute(attribute, value)
        except Exception as err:
            # If removing user to the group fails, log and continue with script
            logging.error('LDAP Update CN: ' + str(user) + ' to ' + str(new_cn) + '\nError: ' + str(err))
            return None
    # End update_attribute

    # Converts a LDAP timestamp to a datetime or a human-readable string
    def convert_ad_timestamp(timestamp):

        timestamp = int(timestamp)
        if timestamp == 0:
            return datetime.now()
        epoch_start = datetime(year=1601, month=1, day=1)
        seconds_since_epoch = timestamp / 10 ** 7
        converted_timestamp = epoch_start + timedelta(seconds=seconds_since_epoch)

        return converted_timestamp