# Module:           Constants
# Purpose:          Contains the settings for the application.  These can be adjusted as needed
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy

import os
import email
import logging

from datetime import date

job_collections               = ['edsembli_jobs', 'active_directory_jobs'] # list of the folders that will have their jobs ran (in order listed)

edsembli_soap_url             = 'https://webservices.edsembli.com/AB/Private/<site name>/WebService/Integration/mwWebSrvStAc.asmx'

edsembli_ftp_server           = 'ftp.edsembli.com'
edsembli_ftp_username         = '<username>'
edsembli_ftp_password         = '<password>'

destiny_ftp_server            = 'sftp.follettdestiny.ca'
destiny_ftp_username          = '<username>'
destiny_ftp_password          = '<password>'
destiny_ftp_student_filename  = 'upload/Student_Patrons.csv'
destiny_ftp_employee_filename = 'upload/Employee_Patrons.csv'
destiny_keep_active_for_days  = 90

edsembli_sql_connection       = (
                                  'Driver={ODBC Driver 18 for SQL Server};'
                                  'Server=<server name>;'
                                  'Database=<Database Name>;'
                                  'UID=<username>;'
                                  'PWD=<password>;'
                                  'Encrypt=yes;'
                                  'TrustServerCertificate=yes;'
                                )

atrieve_sql_connection        = (
                                  'Driver={ODBC Driver 18 for SQL Server};'
                                  'Server=<server name>;'
                                  'Database=<Database Name>;'
                                  'UID=<username>;'
                                  'PWD=<password>;'
                                  'Encrypt=yes;'
                                  'TrustServerCertificate=yes;'
                                )

ldap_server                   = '<Server Name>'
ldap_username                 = '<Full Distiguished Name>'
ldap_password                 = '<password>'
ldap_search_base              = 'DC=Server,DC=local'
ldap_managed_groups           = ['Student-All', 'Password Policy K-4', 'Password Policy 5-12', '365 A1 Student License', '365 A3 Student License'] # This list doesn't need to contain groups 'Students-<School Name>' or 'Students-<Grade> as they will be added automatically
ldap_student_domain           = 'student.local'
ldap_student_ou_base          = 'OU=STUDENT,DC=Server,DC=local'
ldap_student_disabled_ou_base = 'OU=Students,OU=Users,OU=Stale,DC=domain,DC=local'
ldap_student_pwd_change_new   = False
ldap_expired_subs_email       = '<notification email>'
ldap_expired_subs_days        = 180    # how many days before account expires
ldap_sub_pre_notification     = 14     # Notify # number of days before the password expires

atrieve_base_url              = 'https://ab05.atrieveerp.com'
atrieve_logon_url             = atrieve_base_url + '/<site_name>/servlet/Broker'
atrieve_invoice_report_url    = atrieve_base_url + '/<site_name>/servlet/Broker?env=bas&template=prm.BASReportWriter2.xml&SESSION_IS_ALIVE=YES&REPORT_NAME=Invoice+List+by+Date&portal=none&HTML_FILE_NAME=REPORTWRITERMENU&RUN_TIME=YES&NO_HTML_WAIT=YES'
atrieve_username              = '<username>'
atrieve_password              = os.getenv('identity_atrieve_web_password')
atrieve_employee_reports      = [
                                {'sql_table': 'Employee_Demographics', 'url': atrieve_logon_url + '?env=prm&template=prm.PRMReportWriter2.xml&JSTIMESTAMP=8_53_23_953&SESSION_IS_ALIVE=YES&REPORT_NAME=Employee_Demographics&portal=none&HTML_FILE_NAME=REPORTWRITERMENU&RUN_TIME=YES&NO_HTML_WAIT=YES' },
                                {'sql_table': 'Assignments', 'url': atrieve_logon_url + '?env=prm&template=prm.PRMReportWriter2.xml&JSTIMESTAMP=8_44_26_216&SESSION_IS_ALIVE=YES&REPORT_NAME=Assignments&portal=none&HTML_FILE_NAME=REPORTWRITERMENU&RUN_TIME=YES&NO_HTML_WAIT=YES' },
                                {'sql_table': 'Positions', 'url': atrieve_logon_url + '?env=prm&template=prm.PRMReportWriter2.xml&JSTIMESTAMP=8_30_58_592&SESSION_IS_ALIVE=YES&REPORT_NAME=Positions&portal=none&HTML_FILE_NAME=REPORTWRITERMENU&RUN_TIME=YES&NO_HTML_WAIT=YES' },
                                {'sql_table': 'Locations', 'url': atrieve_logon_url + '?env=prm&template=prm.PRMReportWriter2.xml&JSTIMESTAMP=8_30_48_3&SESSION_IS_ALIVE=YES&REPORT_NAME=Locations&portal=none&HTML_FILE_NAME=REPORTWRITERMENU&RUN_TIME=YES&NO_HTML_WAIT=YES' },
                                ]

selenium_headless             = True
selenium_download_dir         = 'C:\\Scripts\\Downloads'

logging_log_to_screen         = True
logging_log_level             = logging.INFO # Normal = logging.INFO       Detailed Logging = logging.DEBUG
logging_console_format        = '%(levelname)-8s %(message)s'
logging_file_format           = '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
logging_file_time_format      = '%H:%M:%S'
logging_path                  = 'C:\\Scripts\\User Identity Automation Logs\\'  # can be absolute or relative to application path and must be escaped and have a trailling slash
logging_file                  = 'application_' + date.today().strftime("%Y-%m-%d") +'.log'

sanity_student_threshold      = 2000         # The minimum number of records in the Student Demographics table otherwise the script will stop executing
ldap_student_pwd_reset_reactivate = 300

execute_changes               = True         # Simulate = False, Execute = True   <-- only only affects Active Directory changes.
execute_moving_past_users     = True         # Disabled withdrawn/terminated users.  Requires execute_changes to be true to take effect.
execute_disabling_past_users  = True         # Moves withdrawn/terminated users to the disabled ou base OUs listed in the config above.  Requires execute_changes to be true to take effect

email_server                  = 'smtp.office365.com'
email_port                    = 587
email_username                = 'noreply@domain.local'
email_sender_name             = 'Account Automation'
email_password                = '<password>'