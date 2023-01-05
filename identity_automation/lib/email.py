import logging
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from identity_automation.common import constants

def send(to, subject, body):
    try: 
        # Create SMTP session 
        smtp = smtplib.SMTP(constants.email_server, constants.email_port) 

        # Use TLS to add security 
        smtp.starttls() 

        # User Authentication 
        smtp.login(constants.email_username, constants.email_password)

        # Encode message
        message = MIMEText(body, "html")
        message['From'] = constants.email_sender_name + ' <' + constants.email_username + '>'
        message['To'] = to
        message['Subject'] = subject

        # Sending the Email
        smtp.sendmail(constants.email_username, to, message.as_string()) 

        smtp.close()
        return True

    except smtplib.SMTPException as e:
        logging.warning('Error: unable to send email to ' + to, e)
        smtp.close()