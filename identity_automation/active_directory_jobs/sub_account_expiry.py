# Module:           Sub Expriny Password Notification Active Directory Job
# Purpose:          Compares the data in SQL to Active Directory and makes changes to the Active Directory to reflect the SQL data
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy

import logging
import io
import pyodbc
import datetime
from ftplib import FTP
from pypika import MSSQLQuery, functions as fn
from identity_automation.common import constants
from identity_automation.lib import email
from identity_automation.lib import mssql
from identity_automation.lib import active_directory
from identity_automation.models import student_model
from identity_automation.models import school_model

# Open DB connection to be reused within module
db                  = mssql.db()
ldap                = active_directory.LDAP()

# Job Entry Point
def run():

    # Get Sub from Active Directory
    sub_accounts = get_sub_accounts()

    # compare expiry dates to see when account is going to expire, if it's less than 14 days return user
    if sub_accounts != None:
        expiring_accounts = get_expiring_accounts(sub_accounts)

        if len(expiring_accounts) > 0:
            send_notifications(expiring_accounts)

#End run

# Returns all the sub accounts
def get_sub_accounts():

    # Get sub accounts from each school OU
    subs = ldap.get_users_expiry('OU=SUBS,OU=FFCA-CAMPUS,' + constants.ldap_search_base)

    return subs
# End get_sub_accounts

def get_expiring_accounts (subs):
    expiring_accounts = []

    for account in subs:
        expiry_date = account['pwdLastSet'].value.replace(tzinfo=None)
        today = datetime.datetime.now()
        DaysOfPasswordChange = (today - expiry_date).days
        expiry_date = expiry_date.strftime('%d, %b %Y')

        ExpireIn = constants.ldap_expired_subs_days - DaysOfPasswordChange

        # if password not changed before 14 days 
        if ExpireIn <= constants.ldap_sub_pre_notification:
            expiring_accounts.append(account)

    return expiring_accounts

# Iterate through expiring sub accounts
def send_notifications(accounts):

    body = ''

    body = body + '<h2>Sub accounts that will expire soon</h2>'

    body = body + '<table>'
    body = body + '<tr><th>Username</th><th>Expiry Date</th></tr>'
        
    for account in accounts:
        body = body + '<tr><td>' + str(account.sAMAccountName) + '</td><td>' + account.pwdLastSet.value.strftime('%Y-%m-%d') + '</td></tr>'

    body = body + '</table>'
    body = body + '<br><br>'
    body = body + '<small>This is an automated message.  If you have any questions or concerns about the changes made please create a ticket by emailing: <a href="mailto:ffcatech@ffca-calgary.com">ffcatech@ffca-calgary.com</a>'

    if email.send(constants.ldap_expired_subs_email, 'FFCA Expiring Sub Account Notification', body):
        logging.info('Sub Expiring Account Notification Email successfully sent to ' + constants.ldap_expired_subs_email)
# end send_notifications