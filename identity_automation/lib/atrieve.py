# Module:           LDAP
# Purpose:          Library to login into Atrieve and pull a report
# Author:           Trevor Smith
# Organization:     Foundations for the Future Charter Academy

import logging
import requests
import time
import glob
import os
import csv
from identity_automation.common import constants
from identity_automation.lib import mssql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

def login (login_url = constants.atrieve_logon_url, username = constants.atrieve_username, password = constants.atrieve_password):
    # Creating an instance webdriver
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
    "download.default_directory": constants.selenium_download_dir,
    "download.prompt_for_download": False,
    })

    if constants.selenium_headless:
        chrome_options.add_argument("--headless")

    browser = webdriver.Chrome(chrome_options=chrome_options, executable_path='C:\Scripts\chromedriver.exe')

    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': constants.selenium_download_dir}}
    command_result = browser.execute("send_command", params)
     
    browser.get(login_url)
    
    # Let's the user see and also load the element 
    time.sleep(2)
    
    browser.find_element(By.NAME, 'Username').send_keys(username)
    browser.find_element(By.NAME, 'Password').send_keys(password)
    browser.find_element(By.ID, 'SsoLogin_Btn').click()

    time.sleep(2)

    if not 'Welcome to Atrieve!' in browser.page_source:
        return browser
    
    return None

def get(browser, url = constants.atrieve_invoice_report_url):

    browser.get(url)

    time.sleep(2)

    list_of_files = glob.glob(os.path.join(constants.selenium_download_dir, '*.csv')) # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)

    data = csv.DictReader(open(latest_file, newline=''))
    print(data)
    return data
