# Module:           Edsembli
# Purpose:          Library to query Edsembli's SOAP API
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy
# Last Modified:    Nov 2021

import logging
import requests
from identity_automation.common import constants
from identity_automation.lib import mssql
from posixpath import pathsep

# Query Edsembli to Get List (in XML)
# Data queried is based on the soap body
# Returns xml with student data
def soap(body):
    
    # structured XML for data request
    payload = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
                    <soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">
                        <soap:Body>
                        """ + body + """
                        </soap:Body>
                    </soap:Envelope>"""

    # headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8'
    }

    # POST request and return result
    response = requests.request("POST", constants.edsembli_soap_url, headers=headers, data=payload)

    if (not hasattr(response, 'status_code') or response.status_code != 200):
        logging.critical('Couldn\'t connect to Edsembli')
        exit()
    return response.text
# End soap

# Returns the number of records found in the xml
# It uses the Num_Elements element and returns that instead of actually counting records
def record_count (tree, namespace):
    # Try to find Num_Elements element.  If not's not found catch error and skip job gracefully
    try:
        if (tree[0][0][0][1][0][0][0].tag != namespace + 'Num_Elements'):
            logging.error('Num_Elements element not found.  Skipping...')
            return 0
    except:
        logging.error('Num_Elements element not found.  Skipping...')
        return 0

    count = tree[0][0][0][1][0][0][0].text #expected location of the RecordNum element

    if (not count.isnumeric() or count == 0):
        logging.error('No records found.  Skipping...')
        return 0

    logging.info('Found ' + count + ' Records')

    return count
# End record_count

# Pull field from student element (subset of the xml)
def get (data, field, namespace, type):
    value = data.find(namespace + field).text
    if type == 'date':
        if (value.split('T')[0] != '0001-01-01'):
            return value.split('T')[0]
        else:
            return value.split('T')[0]
    elif type == 'number':
            return data.find(namespace + field).text or 0
    else: #string
            return data.find(namespace + field).text or ''
# End get

# Writes xml to file
# Add the following to the top of the job's run function:
#   edsembli.write_to_file(edsembli.soap(edsembli_soap_request), 'file.xml')
#   return
def write_to_file(data, path):
    file = open(path, "w")
    file.write(data)
# End write_to_file